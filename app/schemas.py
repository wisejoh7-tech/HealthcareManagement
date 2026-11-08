from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import AppointmentStatus, InvoiceStatus


# ---------------- Patient Schemas ----------------
class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    date_of_birth: str = Field(..., description="YYYY-MM-DD")
    gender: str = Field(..., description="Male, Female, Other")
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------------- Doctor Schemas ----------------
class DoctorBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    specialty: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=100)
    consultation_fee: float = Field(..., ge=0.0)
    available_days: Optional[str] = "Monday,Tuesday,Wednesday,Thursday,Friday"
    available_time: Optional[str] = "09:00-17:00"


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[str] = None
    consultation_fee: Optional[float] = None
    available_days: Optional[str] = None
    available_time: Optional[str] = None


class DoctorResponse(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------------- Appointment Schemas ----------------
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: str = Field(..., description="YYYY-MM-DD")
    appointment_time: str = Field(..., description="HH:MM")
    reason: str = Field(..., min_length=3, max_length=255)


class AppointmentCreate(AppointmentBase):
    status: Optional[AppointmentStatus] = AppointmentStatus.SCHEDULED


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None


class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AppointmentStatus
    created_at: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None


# ---------------- Medical Record Schemas ----------------
class MedicalRecordBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    symptoms: str
    diagnosis: str
    prescription: str
    vital_blood_pressure: Optional[str] = None
    vital_heart_rate: Optional[int] = None
    vital_temperature: Optional[float] = None
    vital_weight: Optional[float] = None
    doctor_notes: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    vital_blood_pressure: Optional[str] = None
    vital_heart_rate: Optional[int] = None
    vital_temperature: Optional[float] = None
    vital_weight: Optional[float] = None
    doctor_notes: Optional[str] = None


class MedicalRecordResponse(MedicalRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_date: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None


# ---------------- Invoice Schemas ----------------
class InvoiceBase(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    amount: float = Field(..., ge=0.0)
    description: str
    status: Optional[InvoiceStatus] = InvoiceStatus.PENDING
    payment_method: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    payment_method: Optional[str] = None
    paid_date: Optional[datetime] = None


class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_date: datetime
    paid_date: Optional[datetime] = None
    patient_name: Optional[str] = None


# ---------------- Dashboard Stats Schema ----------------
class DashboardStats(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    scheduled_appointments: int
    completed_appointments: int
    total_revenue: float
    pending_revenue: float
    recent_appointments: List[AppointmentResponse]
