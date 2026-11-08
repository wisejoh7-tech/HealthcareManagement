import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_get_patient(client):
    patient_payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0100",
        "date_of_birth": "1990-05-15",
        "gender": "Female",
        "blood_group": "O+",
        "address": "123 Health Ave",
        "emergency_contact": "Bob Smith (+1-555-0101)",
        "allergies": "Penicillin",
        "medical_history": "Asthma"
    }
    response = client.post("/api/patients/", json=patient_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["full_name"] == "Alice Smith"
    patient_id = data["id"]

    # Duplicate email check
    dup_response = client.post("/api/patients/", json=patient_payload)
    assert dup_response.status_code == 400

    # Get patient by ID
    get_res = client.get(f"/api/patients/{patient_id}")
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "alice@example.com"

    # Search patients
    search_res = client.get("/api/patients/?search=Alice")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # Update patient
    update_res = client.put(f"/api/patients/{patient_id}", json={"phone": "+1-555-9999"})
    assert update_res.status_code == 200
    assert update_res.json()["phone"] == "+1-555-9999"


def test_create_and_get_doctor(client):
    doc_payload = {
        "full_name": "Dr. Gregory House",
        "email": "house@princetonplainsboro.com",
        "phone": "+1-555-0199",
        "specialty": "Diagnostic Medicine",
        "department": "Infectious Diseases",
        "consultation_fee": 150.0,
        "available_days": "Monday,Tuesday,Wednesday",
        "available_time": "10:00-16:00"
    }
    res = client.post("/api/doctors/", json=doc_payload)
    assert res.status_code == 201
    doc_data = res.json()
    assert doc_data["id"] is not None
    assert doc_data["consultation_fee"] == 150.0

    # Duplicate email
    dup_res = client.post("/api/doctors/", json=doc_payload)
    assert dup_res.status_code == 400

    # Filter doctors by specialty
    filt_res = client.get("/api/doctors/?specialty=Diagnostic")
    assert filt_res.status_code == 200
    assert len(filt_res.json()) == 1


def test_appointment_booking_and_conflict_prevention(client):
    # Setup patient & doctor
    p = client.post("/api/patients/", json={
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-555-0111",
        "date_of_birth": "1985-02-20",
        "gender": "Male"
    }).json()

    d = client.post("/api/doctors/", json={
        "full_name": "Dr. Sarah Connor",
        "email": "sarah@example.com",
        "phone": "+1-555-0122",
        "specialty": "Cardiology",
        "department": "Cardiology",
        "consultation_fee": 120.0
    }).json()

    # Book appointment
    appt_payload = {
        "patient_id": p["id"],
        "doctor_id": d["id"],
        "appointment_date": "2026-11-15",
        "appointment_time": "10:00",
        "reason": "Chest tightness and palpitations"
    }
    appt_res = client.post("/api/appointments/", json=appt_payload)
    assert appt_res.status_code == 201
    appt_data = appt_res.json()
    assert appt_data["status"] == "Scheduled"
    assert appt_data["patient_name"] == "John Doe"
    assert appt_data["doctor_name"] == "Dr. Sarah Connor"

    # Verify invoice was automatically generated
    invoices_res = client.get(f"/api/billing/?patient_id={p['id']}")
    assert invoices_res.status_code == 200
    invoices = invoices_res.json()
    assert len(invoices) == 1
    assert invoices[0]["amount"] == 120.0
    assert invoices[0]["status"] == "Pending"

    # Attempt to book another appointment at the exact same slot for same doctor -> Conflict
    p2 = client.post("/api/patients/", json={
        "full_name": "Jane Roe",
        "email": "jane@example.com",
        "phone": "+1-555-0133",
        "date_of_birth": "1992-08-10",
        "gender": "Female"
    }).json()

    conflict_res = client.post("/api/appointments/", json={
        "patient_id": p2["id"],
        "doctor_id": d["id"],
        "appointment_date": "2026-11-15",
        "appointment_time": "10:00",
        "reason": "Routine heart screening"
    })
    assert conflict_res.status_code == 400
    assert "already booked" in conflict_res.json()["detail"]

    # Reschedule to another time
    update_res = client.put(f"/api/appointments/{appt_data['id']}", json={
        "appointment_time": "11:00"
    })
    assert update_res.status_code == 200
    assert update_res.json()["appointment_time"] == "11:00"


def test_medical_record_creation_and_stats(client):
    p = client.post("/api/patients/", json={
        "full_name": "Charlie Brown",
        "email": "charlie@example.com",
        "phone": "+1-555-0144",
        "date_of_birth": "1978-11-03",
        "gender": "Male"
    }).json()

    d = client.post("/api/doctors/", json={
        "full_name": "Dr. Meredith Grey",
        "email": "meredith@example.com",
        "phone": "+1-555-0155",
        "specialty": "General Surgery",
        "department": "Surgery",
        "consultation_fee": 200.0
    }).json()

    appt = client.post("/api/appointments/", json={
        "patient_id": p["id"],
        "doctor_id": d["id"],
        "appointment_date": "2026-11-16",
        "appointment_time": "14:00",
        "reason": "Abdominal pain evaluation"
    }).json()

    record_payload = {
        "patient_id": p["id"],
        "doctor_id": d["id"],
        "appointment_id": appt["id"],
        "symptoms": "Lower right quadrant abdominal pain, mild fever",
        "diagnosis": "Acute Appendicitis (Early stage)",
        "prescription": "Antibiotics IV, surgical consult scheduled",
        "vital_blood_pressure": "130/85",
        "vital_heart_rate": 88,
        "vital_temperature": 38.2,
        "vital_weight": 76.5,
        "doctor_notes": "Admit for ultrasound and observation."
    }
    rec_res = client.post("/api/records/", json=record_payload)
    assert rec_res.status_code == 201
    rec_data = rec_res.json()
    assert rec_data["diagnosis"] == "Acute Appendicitis (Early stage)"
    assert rec_data["patient_name"] == "Charlie Brown"

    # Appointment should now be marked Completed
    appt_status_res = client.get(f"/api/appointments/{appt['id']}")
    assert appt_status_res.json()["status"] == "Completed"

    # Mark invoice as paid
    inv_res = client.get(f"/api/billing/?patient_id={p['id']}")
    inv_id = inv_res.json()[0]["id"]
    pay_res = client.put(f"/api/billing/{inv_id}", json={
        "status": "Paid",
        "payment_method": "Insurance"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "Paid"
    assert pay_res.json()["paid_date"] is not None

    # Check dashboard stats
    stats_res = client.get("/api/stats/")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_patients"] == 1
    assert stats["total_doctors"] == 1
    assert stats["total_appointments"] == 1
    assert stats["completed_appointments"] == 1
    assert stats["total_revenue"] == 200.0
