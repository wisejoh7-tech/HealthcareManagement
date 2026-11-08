# Healthcare Management System (CareSync)

A full-stack, modular Healthcare and Clinic Management System built with **FastAPI**, **SQLAlchemy**, **SQLite**, and an intuitive responsive web dashboard.

---

## 🌟 Features

1. **Patient Management (EMR/EHR):**
   - Register, view, search, update, and manage patients.
   - Comprehensive profile data: contact information, date of birth, gender, blood group, allergies, emergency contacts, and past medical history.

2. **Doctor & Staff Registry:**
   - Manage doctor profiles, specialties, departments, consultation rates, and available schedules.
   - Quick lookup and filtering by department and clinical specialty.

3. **Appointment Scheduling:**
   - Schedule, view, reschedule, and cancel appointments with doctor time-slot conflict validation.
   - Automatically generates a pending billing invoice based on doctor's consultation rate.

4. **Electronic Health Records & Consultations:**
   - Record diagnosis, reported symptoms, prescriptions, and vital signs (blood pressure, heart rate, temperature, weight).
   - Automatically transitions appointment status to completed when medical consultation notes are filed.

5. **Billing & Invoicing:**
   - Tracks billing status (Pending, Paid, Cancelled) and payment methods (Cash, Credit Card, Insurance).
   - Generates itemized consultation and medical charges.

6. **Interactive Web Dashboard:**
   - Responsive, modern frontend UI accessible directly in the browser at `/`.
   - Real-time statistics: active patients, doctors, scheduled appointments, and revenue metrics.
   - Interactive modal forms for streamlined record entry.

7. **Interactive API Documentation:**
   - Auto-generated OpenAPI / Swagger UI documentation available at `/docs` and ReDoc at `/redoc`.

---

## 🚀 Quickstart

### 1. Requirements & Installation
- Python 3.10+
- Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Launch the server using `uvicorn`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Web Application: [http://localhost:8000/](http://localhost:8000/)
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

Execute the automated test suite with pytest:
```bash
pytest -v
```

---

## 📁 Project Structure

```
HealthcareManagement/
├── app/
│   ├── database.py         # SQLAlchemy engine, session maker, and DB dependency
│   ├── main.py             # FastAPI entrypoint and static file mounting
│   ├── models.py           # Database models (Patient, Doctor, Appointment, MedicalRecord, Invoice)
│   ├── schemas.py          # Pydantic schemas for data validation and serialization
│   ├── routers/
│   │   ├── appointments.py # Appointment endpoints & conflict prevention logic
│   │   ├── billing.py      # Invoice generation & payment endpoints
│   │   ├── doctors.py      # Doctor registry endpoints
│   │   ├── patients.py     # Patient records & search endpoints
│   │   ├── records.py      # EHR consultation and prescription endpoints
│   │   └── stats.py        # Dashboard analytics and overview metrics
│   └── static/
│       ├── app.js          # Frontend interactivity & REST API integrations
│       ├── index.html      # Responsive web portal & management dashboard
│       └── styles.css      # Custom dashboard styling
├── tests/
│   └── test_api.py         # Unit and integration test suite
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Project dependencies
└── README.md               # System documentation
```

---

## 🛠️ API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Management Dashboard |
| `GET` | `/api/health` | Health Check |
| `GET`, `POST` | `/api/patients/` | List, search, or register patients |
| `GET`, `PUT`, `DELETE` | `/api/patients/{id}` | Manage single patient record |
| `GET`, `POST` | `/api/doctors/` | List or register healthcare professionals |
| `GET`, `PUT`, `DELETE` | `/api/doctors/{id}` | Manage single doctor profile |
| `GET`, `POST` | `/api/appointments/` | List, filter, or book appointments |
| `GET`, `PUT`, `DELETE` | `/api/appointments/{id}` | Reschedule or cancel appointments |
| `GET`, `POST` | `/api/records/` | List or create EHR consultation notes |
| `GET`, `PUT`, `DELETE` | `/api/records/{id}` | Manage medical records & vitals |
| `GET`, `POST` | `/api/billing/` | List or generate invoices |
| `GET`, `PUT`, `DELETE` | `/api/billing/{id}` | Process invoice payments or updates |
| `GET` | `/api/stats/` | Dashboard metrics & summary statistics |
