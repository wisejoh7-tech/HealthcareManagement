from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/billing", tags=["Billing & Invoices"])


def enrich_invoice(invoice: models.Invoice) -> schemas.InvoiceResponse:
    resp = schemas.InvoiceResponse.model_validate(invoice)
    if invoice.patient:
        resp.patient_name = invoice.patient.full_name
    return resp


@router.post("/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == invoice.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    if invoice.appointment_id:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == invoice.appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found.")

    db_invoice = models.Invoice(**invoice.model_dump())
    if db_invoice.status == models.InvoiceStatus.PAID and not db_invoice.paid_date:
        db_invoice.paid_date = datetime.utcnow()

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return enrich_invoice(db_invoice)


@router.get("/", response_model=List[schemas.InvoiceResponse])
def get_invoices(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    status: Optional[models.InvoiceStatus] = Query(None, description="Filter by payment status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Invoice)
    if patient_id:
        query = query.filter(models.Invoice.patient_id == patient_id)
    if status:
        query = query.filter(models.Invoice.status == status)

    invoices = query.order_by(models.Invoice.issue_date.desc()).offset(skip).limit(limit).all()
    return [enrich_invoice(inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=schemas.InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return enrich_invoice(invoice)


@router.put("/{invoice_id}", response_model=schemas.InvoiceResponse)
def update_invoice(invoice_id: int, updates: schemas.InvoiceUpdate, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    update_data = updates.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == models.InvoiceStatus.PAID:
        if not invoice.paid_date:
            invoice.paid_date = datetime.utcnow()

    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return enrich_invoice(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    db.delete(invoice)
    db.commit()
    return None
