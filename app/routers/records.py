from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/records", tags=["Medical Records"])


def enrich_record(record: models.MedicalRecord) -> schemas.MedicalRecordResponse:
    resp = schemas.MedicalRecordResponse.model_validate(record)
    if record.patient:
        resp.patient_name = record.patient.full_name
    if record.doctor:
        resp.doctor_name = record.doctor.full_name
    return resp


@router.post("/", response_model=schemas.MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(record: schemas.MedicalRecordCreate, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == record.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == record.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    if record.appointment_id:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == record.appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found.")
        # Mark appointment as completed
        appointment.status = models.AppointmentStatus.COMPLETED

    db_record = models.MedicalRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return enrich_record(db_record)


@router.get("/", response_model=List[schemas.MedicalRecordResponse])
def get_medical_records(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    search: Optional[str] = Query(None, description="Search in diagnosis or symptoms"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.MedicalRecord)
    if patient_id:
        query = query.filter(models.MedicalRecord.patient_id == patient_id)
    if doctor_id:
        query = query.filter(models.MedicalRecord.doctor_id == doctor_id)
    if search:
        query = query.filter(
            (models.MedicalRecord.diagnosis.ilike(f"%{search}%")) |
            (models.MedicalRecord.symptoms.ilike(f"%{search}%"))
        )

    records = query.order_by(models.MedicalRecord.record_date.desc()).offset(skip).limit(limit).all()
    return [enrich_record(r) for r in records]


@router.get("/{record_id}", response_model=schemas.MedicalRecordResponse)
def get_medical_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found.")
    return enrich_record(record)


@router.put("/{record_id}", response_model=schemas.MedicalRecordResponse)
def update_medical_record(record_id: int, updates: schemas.MedicalRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found.")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return enrich_record(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medical_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found.")
    db.delete(record)
    db.commit()
    return None
