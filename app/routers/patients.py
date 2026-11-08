from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.post("/", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Patient).filter(models.Patient.email == patient.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient with this email already exists.")

    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/", response_model=List[schemas.PatientResponse])
def get_patients(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (models.Patient.full_name.ilike(pattern)) |
            (models.Patient.email.ilike(pattern)) |
            (models.Patient.phone.ilike(pattern))
        )
    return query.order_by(models.Patient.id.desc()).offset(skip).limit(limit).all()


@router.get("/{patient_id}", response_model=schemas.PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@router.put("/{patient_id}", response_model=schemas.PatientResponse)
def update_patient(patient_id: int, updates: schemas.PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    update_data = updates.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != patient.email:
        existing = db.query(models.Patient).filter(models.Patient.email == update_data["email"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already in use by another patient.")

    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    db.delete(patient)
    db.commit()
    return None
