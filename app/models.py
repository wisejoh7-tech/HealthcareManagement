from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No-Show"


class InvoiceStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # YYYY-MM-DD
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(10), nullable=True)
    address = Column(String(255), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    specialty = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    consultation_fee = Column(Float, nullable=False, default=50.0)
    available_days = Column(String(100), default="Monday,Tuesday,Wednesday,Thursday,Friday")
    available_time = Column(String(50), default="09:00-17:00")
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="doctor", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    appointment_time = Column(String(10), nullable=False)  # HH:MM
    reason = Column(String(255), nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    invoice = relationship("Invoice", back_populates="appointment", uselist=False)
    medical_record = relationship("MedicalRecord", back_populates="appointment", uselist=False)


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    symptoms = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=False)
    prescription = Column(Text, nullable=False)
    vital_blood_pressure = Column(String(20), nullable=True)  # e.g., 120/80
    vital_heart_rate = Column(Integer, nullable=True)  # bpm
    vital_temperature = Column(Float, nullable=True)  # Celsius
    vital_weight = Column(Float, nullable=True)  # kg
    doctor_notes = Column(Text, nullable=True)
    record_date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")
    appointment = relationship("Appointment", back_populates="medical_record")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)
    payment_method = Column(String(50), nullable=True)  # Cash, Credit Card, Insurance
    description = Column(String(255), nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    paid_date = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")
