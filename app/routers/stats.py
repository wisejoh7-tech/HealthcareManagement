from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models, schemas
from app.routers.appointments import enrich_appointment

router = APIRouter(prefix="/api/stats", tags=["Dashboard Stats"])


@router.get("/", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_patients = db.query(models.Patient).count()
    total_doctors = db.query(models.Doctor).count()
    total_appointments = db.query(models.Appointment).count()

    scheduled_appointments = db.query(models.Appointment).filter(
        models.Appointment.status == models.AppointmentStatus.SCHEDULED
    ).count()

    completed_appointments = db.query(models.Appointment).filter(
        models.Appointment.status == models.AppointmentStatus.COMPLETED
    ).count()

    total_revenue = db.query(func.coalesce(func.sum(models.Invoice.amount), 0.0)).filter(
        models.Invoice.status == models.InvoiceStatus.PAID
    ).scalar()

    pending_revenue = db.query(func.coalesce(func.sum(models.Invoice.amount), 0.0)).filter(
        models.Invoice.status == models.InvoiceStatus.PENDING
    ).scalar()

    recent_appointments = db.query(models.Appointment).order_by(
        models.Appointment.id.desc()
    ).limit(5).all()

    return schemas.DashboardStats(
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        scheduled_appointments=scheduled_appointments,
        completed_appointments=completed_appointments,
        total_revenue=float(total_revenue),
        pending_revenue=float(pending_revenue),
        recent_appointments=[enrich_appointment(a) for a in recent_appointments]
    )
