import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import patients, doctors, appointments, records, billing, stats

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Healthcare Management System API",
    description="Comprehensive API for managing Patients, Doctors, Appointments, Medical Records, and Billing.",
    version="1.0.0"
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(records.router)
app.include_router(billing.router)
app.include_router(stats.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Healthcare Management System API is running. Access /docs for API documentation."}


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Healthcare Management System"}
