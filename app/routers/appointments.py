from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


def enrich_appointment(appointment: models.Appointment) -> schemas.AppointmentResponse:
    resp = schemas.AppointmentResponse.model_validate(appointment)
    if appointment.patient:
        resp.patient_name = appointment.patient.full_name
    if appointment.doctor:
        resp.doctor_name = appointment.doctor.full_name
        resp.doctor_specialty = appointment.doctor.specialty
    return resp


@router.post("/", response_model=schemas.AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    # Check for doctor conflict on the same date and time (excluding cancelled)
    conflict = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.appointment_date == appointment.appointment_date,
        models.Appointment.appointment_time == appointment.appointment_time,
        models.Appointment.status != models.AppointmentStatus.CANCELLED
    ).first()

    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor {doctor.full_name} is already booked at {appointment.appointment_time} on {appointment.appointment_date}."
        )

    db_appointment = models.Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.flush()

    # Automatically generate an invoice for the consultation fee
    invoice = models.Invoice(
        patient_id=patient.id,
        appointment_id=db_appointment.id,
        amount=doctor.consultation_fee,
        description=f"Consultation with Dr. {doctor.full_name} ({doctor.specialty})",
        status=models.InvoiceStatus.PENDING
    )
    db.add(invoice)
    db.commit()
    db.refresh(db_appointment)

    return enrich_appointment(db_appointment)


@router.get("/", response_model=List[schemas.AppointmentResponse])
def get_appointments(
    date: Optional[str] = Query(None, description="Filter by YYYY-MM-DD"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    status: Optional[models.AppointmentStatus] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Appointment)
    if date:
        query = query.filter(models.Appointment.appointment_date == date)
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if status:
        query = query.filter(models.Appointment.status == status)

    appointments = query.order_by(
        models.Appointment.appointment_date.desc(),
        models.Appointment.appointment_time.desc()
    ).offset(skip).limit(limit).all()

    return [enrich_appointment(a) for a in appointments]


@router.get("/{appointment_id}", response_model=schemas.AppointmentResponse)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return enrich_appointment(appointment)


@router.put("/{appointment_id}", response_model=schemas.AppointmentResponse)
def update_appointment(appointment_id: int, updates: schemas.AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    update_data = updates.model_dump(exclude_unset=True)

    new_date = update_data.get("appointment_date", appointment.appointment_date)
    new_time = update_data.get("appointment_time", appointment.appointment_time)
    new_status = update_data.get("status", appointment.status)

    if (new_date != appointment.appointment_date or new_time != appointment.appointment_time) and new_status != models.AppointmentStatus.CANCELLED:
        conflict = db.query(models.Appointment).filter(
            models.Appointment.id != appointment.id,
            models.Appointment.doctor_id == appointment.doctor_id,
            models.Appointment.appointment_date == new_date,
            models.Appointment.appointment_time == new_time,
            models.Appointment.status != models.AppointmentStatus.CANCELLED
        ).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Slot conflict: another appointment exists at {new_time} on {new_date}."
            )

    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return enrich_appointment(appointment)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    db.delete(appointment)
    db.commit()
    return None
