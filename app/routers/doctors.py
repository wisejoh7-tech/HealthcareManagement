from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


@router.post("/", response_model=schemas.DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Doctor).filter(models.Doctor.email == doctor.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Doctor with this email already exists.")

    db_doctor = models.Doctor(**doctor.model_dump())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


@router.get("/", response_model=List[schemas.DoctorResponse])
def get_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Doctor)
    if specialty:
        query = query.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))
    if department:
        query = query.filter(models.Doctor.department.ilike(f"%{department}%"))
    if search:
        query = query.filter(models.Doctor.full_name.ilike(f"%{search}%"))
    return query.order_by(models.Doctor.id.desc()).offset(skip).limit(limit).all()


@router.get("/{doctor_id}", response_model=schemas.DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return doctor


@router.put("/{doctor_id}", response_model=schemas.DoctorResponse)
def update_doctor(doctor_id: int, updates: schemas.DoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    update_data = updates.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != doctor.email:
        existing = db.query(models.Doctor).filter(models.Doctor.email == update_data["email"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already in use by another doctor.")

    for field, value in update_data.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    db.delete(doctor)
    db.commit()
    return None
