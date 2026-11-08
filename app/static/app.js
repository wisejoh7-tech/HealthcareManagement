// State & Selectors
const API_BASE = '/api';

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'short', day: 'numeric'
  });
  loadDashboard();
});

// View Routing
function setupNavigation() {
  const links = document.querySelectorAll('.nav-link');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = link.getAttribute('data-view');
      switchView(targetView);
    });
  });
}

function switchView(viewName) {
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));

  const activeLink = document.querySelector(`.nav-link[data-view="${viewName}"]`);
  if (activeLink) activeLink.classList.add('active');

  const activeSection = document.getElementById(`view-${viewName}`);
  if (activeSection) activeSection.classList.add('active');

  const titles = {
    dashboard: 'Dashboard Overview',
    patients: 'Patient Directory',
    doctors: 'Medical Staff & Doctors',
    appointments: 'Appointment Scheduling',
    records: 'Electronic Medical Records (EHR)',
    billing: 'Billing & Invoicing'
  };
  document.getElementById('page-title').textContent = titles[viewName] || 'Healthcare System';

  if (viewName === 'dashboard') loadDashboard();
  if (viewName === 'patients') loadPatients();
  if (viewName === 'doctors') loadDoctors();
  if (viewName === 'appointments') { loadAppointments(); populateDropdowns(); }
  if (viewName === 'records') { loadRecords(); populateDropdowns(); }
  if (viewName === 'billing') { loadBilling(); populateDropdowns(); }
}

// Modal handling
function openModal(id) {
  populateDropdowns();
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
}

// Async Data Fetchers
async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/stats/`);
    if (!res.ok) throw new Error('Failed to load stats');
    const data = await res.json();
    document.getElementById('stat-patients').textContent = data.total_patients;
    document.getElementById('stat-doctors').textContent = data.total_doctors;
    document.getElementById('stat-appointments').textContent = data.scheduled_appointments;
    document.getElementById('stat-revenue').textContent = `$${data.total_revenue.toFixed(2)}`;

    const tbody = document.getElementById('dashboard-recent-appointments');
    if (data.recent_appointments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">No recent appointments found.</td></tr>`;
    } else {
      tbody.innerHTML = data.recent_appointments.map(a => `
        <tr>
          <td>#${escapeHtml(a.id)}</td>
          <td><strong>${escapeHtml(a.patient_name || 'Patient #' + a.patient_id)}</strong></td>
          <td>${escapeHtml(a.doctor_name || 'Doctor #' + a.doctor_id)}</td>
          <td>${escapeHtml(a.doctor_specialty || '-')}</td>
          <td>${escapeHtml(a.appointment_date)} ${escapeHtml(a.appointment_time)}</td>
          <td><span class="badge badge-${escapeHtml(a.status.toLowerCase())}">${escapeHtml(a.status)}</span></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

async function populateDropdowns() {
  try {
    const [pRes, dRes] = await Promise.all([
      fetch(`${API_BASE}/patients/`),
      fetch(`${API_BASE}/doctors/`)
    ]);
    const patients = await pRes.json();
    const doctors = await dRes.json();

    const patientOptions = patients.map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.full_name)} (${escapeHtml(p.phone)})</option>`).join('');
    const doctorOptions = doctors.map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.full_name)} - ${escapeHtml(d.specialty)} ($${escapeHtml(d.consultation_fee)})</option>`).join('');

    const pDropdowns = ['appt-patient-select', 'record-patient-select', 'invoice-patient-select'];
    pDropdowns.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = patientOptions || '<option value="">No patients available</option>';
    });

    const dDropdowns = ['appt-doctor-select', 'record-doctor-select'];
    dDropdowns.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = doctorOptions || '<option value="">No doctors available</option>';
    });
  } catch (err) {
    console.error('Error populating dropdowns:', err);
  }
}

// Patients
async function loadPatients() {
  const search = document.getElementById('patient-search').value.trim();
  const url = search ? `${API_BASE}/patients/?search=${encodeURIComponent(search)}` : `${API_BASE}/patients/`;
  const res = await fetch(url);
  const data = await res.json();
  const tbody = document.getElementById('patients-table-body');
  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No patients found.</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(p => `
    <tr>
      <td>#${escapeHtml(p.id)}</td>
      <td><strong>${escapeHtml(p.full_name)}</strong></td>
      <td>${escapeHtml(p.email)}</td>
      <td>${escapeHtml(p.phone)}</td>
      <td>${escapeHtml(p.date_of_birth)} (${escapeHtml(p.gender)})</td>
      <td>${escapeHtml(p.blood_group || 'N/A')}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deletePatient(${Number(p.id)})">Delete</button>
      </td>
    </tr>
  `).join('');
}

async function handlePatientSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = Object.fromEntries(formData.entries());
  try {
    const res = await fetch(`${API_BASE}/patients/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not register patient'}`);
      return;
    }
    closeModal('patient-modal');
    e.target.reset();
    loadPatients();
  } catch (err) {
    alert(err.message);
  }
}

async function deletePatient(id) {
  if (!confirm('Are you sure you want to delete this patient?')) return;
  await fetch(`${API_BASE}/patients/${id}`, { method: 'DELETE' });
  loadPatients();
}

// Doctors
async function loadDoctors() {
  const search = document.getElementById('doctor-search').value.trim();
  const url = search ? `${API_BASE}/doctors/?search=${encodeURIComponent(search)}` : `${API_BASE}/doctors/`;
  const res = await fetch(url);
  const data = await res.json();
  const tbody = document.getElementById('doctors-table-body');
  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No doctors found.</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(d => `
    <tr>
      <td>#${escapeHtml(d.id)}</td>
      <td><strong>${escapeHtml(d.full_name)}</strong></td>
      <td>${escapeHtml(d.specialty)}</td>
      <td>${escapeHtml(d.department)}</td>
      <td>$${Number(d.consultation_fee).toFixed(2)}</td>
      <td>${escapeHtml(d.phone)} | ${escapeHtml(d.email)}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteDoctor(${Number(d.id)})">Delete</button>
      </td>
    </tr>
  `).join('');
}

async function handleDoctorSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = Object.fromEntries(formData.entries());
  payload.consultation_fee = parseFloat(payload.consultation_fee);
  try {
    const res = await fetch(`${API_BASE}/doctors/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not save doctor'}`);
      return;
    }
    closeModal('doctor-modal');
    e.target.reset();
    loadDoctors();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteDoctor(id) {
  if (!confirm('Are you sure you want to delete this doctor?')) return;
  await fetch(`${API_BASE}/doctors/${id}`, { method: 'DELETE' });
  loadDoctors();
}

// Appointments
async function loadAppointments() {
  const date = document.getElementById('appointment-filter-date').value;
  const status = document.getElementById('appointment-filter-status').value;
  let url = `${API_BASE}/appointments/?`;
  if (date) url += `date=${encodeURIComponent(date)}&`;
  if (status) url += `status=${encodeURIComponent(status)}&`;

  const res = await fetch(url);
  const data = await res.json();
  const tbody = document.getElementById('appointments-table-body');
  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No appointments found.</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(a => `
    <tr>
      <td>#${escapeHtml(a.id)}</td>
      <td><strong>${escapeHtml(a.patient_name || 'Patient #' + a.patient_id)}</strong></td>
      <td>${escapeHtml(a.doctor_name || 'Doctor #' + a.doctor_id)} (${escapeHtml(a.doctor_specialty || '-')})</td>
      <td>${escapeHtml(a.appointment_date)} ${escapeHtml(a.appointment_time)}</td>
      <td>${escapeHtml(a.reason)}</td>
      <td><span class="badge badge-${escapeHtml(a.status.toLowerCase())}">${escapeHtml(a.status)}</span></td>
      <td>
        ${a.status === 'Scheduled' ? `
          <button class="btn btn-secondary btn-sm" onclick="updateAppointmentStatus(${Number(a.id)}, 'Completed')">Complete</button>
          <button class="btn btn-danger btn-sm" onclick="updateAppointmentStatus(${Number(a.id)}, 'Cancelled')">Cancel</button>
        ` : `<button class="btn btn-danger btn-sm" onclick="deleteAppointment(${Number(a.id)})">Delete</button>`}
      </td>
    </tr>
  `).join('');
}

async function handleAppointmentSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = Object.fromEntries(formData.entries());
  payload.patient_id = parseInt(payload.patient_id);
  payload.doctor_id = parseInt(payload.doctor_id);

  try {
    const res = await fetch(`${API_BASE}/appointments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not schedule appointment'}`);
      return;
    }
    closeModal('appointment-modal');
    e.target.reset();
    loadAppointments();
  } catch (err) {
    alert(err.message);
  }
}

async function updateAppointmentStatus(id, newStatus) {
  await fetch(`${API_BASE}/appointments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus })
  });
  loadAppointments();
}

async function deleteAppointment(id) {
  if (!confirm('Are you sure you want to delete this appointment?')) return;
  await fetch(`${API_BASE}/appointments/${id}`, { method: 'DELETE' });
  loadAppointments();
}

// Medical Records
async function loadRecords() {
  const search = document.getElementById('record-search').value.trim();
  const url = search ? `${API_BASE}/records/?search=${encodeURIComponent(search)}` : `${API_BASE}/records/`;
  const res = await fetch(url);
  const data = await res.json();
  const tbody = document.getElementById('records-table-body');
  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No medical records found.</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(r => `
    <tr>
      <td>#${escapeHtml(r.id)}</td>
      <td><strong>${escapeHtml(r.patient_name || 'Patient #' + r.patient_id)}</strong></td>
      <td>${escapeHtml(r.doctor_name || 'Doctor #' + r.doctor_id)}</td>
      <td><strong>${escapeHtml(r.diagnosis)}</strong></td>
      <td>${escapeHtml(r.symptoms)}</td>
      <td>BP: ${escapeHtml(r.vital_blood_pressure || '-')} | HR: ${escapeHtml(r.vital_heart_rate || '-')} bpm</td>
      <td>${new Date(r.record_date).toLocaleDateString()}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteRecord(${Number(r.id)})">Delete</button>
      </td>
    </tr>
  `).join('');
}

async function handleRecordSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = Object.fromEntries(formData.entries());
  payload.patient_id = parseInt(payload.patient_id);
  payload.doctor_id = parseInt(payload.doctor_id);
  if (payload.vital_heart_rate) payload.vital_heart_rate = parseInt(payload.vital_heart_rate);
  if (payload.vital_temperature) payload.vital_temperature = parseFloat(payload.vital_temperature);
  if (payload.vital_weight) payload.vital_weight = parseFloat(payload.vital_weight);

  try {
    const res = await fetch(`${API_BASE}/records/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not save record'}`);
      return;
    }
    closeModal('record-modal');
    e.target.reset();
    loadRecords();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteRecord(id) {
  if (!confirm('Are you sure you want to delete this medical record?')) return;
  await fetch(`${API_BASE}/records/${id}`, { method: 'DELETE' });
  loadRecords();
}

// Billing
async function loadBilling() {
  const status = document.getElementById('billing-filter-status').value;
  const url = status ? `${API_BASE}/billing/?status=${encodeURIComponent(status)}` : `${API_BASE}/billing/`;
  const res = await fetch(url);
  const data = await res.json();
  const tbody = document.getElementById('invoices-table-body');
  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No invoices found.</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(inv => `
    <tr>
      <td>#${escapeHtml(inv.id)}</td>
      <td><strong>${escapeHtml(inv.patient_name || 'Patient #' + inv.patient_id)}</strong></td>
      <td>${escapeHtml(inv.description)}</td>
      <td>$${Number(inv.amount).toFixed(2)}</td>
      <td><span class="badge badge-${escapeHtml(inv.status.toLowerCase())}">${escapeHtml(inv.status)}</span></td>
      <td>${escapeHtml(inv.payment_method || '-')}</td>
      <td>
        ${inv.status === 'Pending' ? `
          <button class="btn btn-primary btn-sm" onclick="markPaid(${Number(inv.id)})">Mark Paid</button>
        ` : ''}
        <button class="btn btn-danger btn-sm" onclick="deleteInvoice(${Number(inv.id)})">Delete</button>
      </td>
    </tr>
  `).join('');
}

async function handleInvoiceSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = Object.fromEntries(formData.entries());
  payload.patient_id = parseInt(payload.patient_id);
  payload.amount = parseFloat(payload.amount);

  try {
    const res = await fetch(`${API_BASE}/billing/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not create invoice'}`);
      return;
    }
    closeModal('invoice-modal');
    e.target.reset();
    loadBilling();
  } catch (err) {
    alert(err.message);
  }
}

async function markPaid(id) {
  await fetch(`${API_BASE}/billing/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Paid', payment_method: 'Credit Card' })
  });
  loadBilling();
}

async function deleteInvoice(id) {
  if (!confirm('Are you sure you want to delete this invoice?')) return;
  await fetch(`${API_BASE}/billing/${id}`, { method: 'DELETE' });
  loadBilling();
}
