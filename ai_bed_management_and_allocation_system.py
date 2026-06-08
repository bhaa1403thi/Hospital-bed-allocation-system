import streamlit as st
from queue import PriorityQueue
from collections import defaultdict

# =========================================================================
# 1. CORE ALGORITHM LOGIC (Preserving your exact Patient & Bed Classes)
# =========================================================================

class Patient:
    def __init__(self, patient_id, name, severity, required_bed, duration_of_stay=1):
        self.patient_id = patient_id 
        self.name = name             
        self.severity = severity     
        self.required_bed = required_bed 
        self.duration_of_stay = duration_of_stay 
        self.admission_day = -1      

    def __str__(self):
        return f"Patient ID: {self.patient_id}, Name: {self.name}, Severity: {self.severity}, Required Bed: {self.required_bed}, Duration: {self.duration_of_stay} days"

    def __lt__(self, other):
        return self.severity > other.severity

class Bed:
    def __init__(self, bed_id, bed_type):
        self.bed_id = bed_id         
        self.bed_type = bed_type     
        self.is_occupied = False     

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Available"
        return f"Bed ID: {self.bed_id}, Type: {self.bed_type}, Status: {status}"

class HospitalBedAllocation:
    def __init__(self, initial_beds=None):
        self.beds = []               
        if initial_beds:
            for bed in initial_beds:
                self.add_bed(bed)
        self.patient_queue = PriorityQueue() 
        self.allocations = {}        
        self.current_day = 0         

    def add_bed(self, bed):
        self.beds.append(bed)

    def add_patient(self, patient):
        self.patient_queue.put((-patient.severity, patient))

    def allocate_bed(self):
        if self.patient_queue.empty():
            return "⚠️ No patients waiting in the triage queue."

        priority, patient = self.patient_queue.get() 

        # Low-severity patient logic (<5 goes to Observation first)
        if patient.severity < 5:
            for bed in self.beds:
                if not bed.is_occupied and bed.bed_type == "Observation":
                    bed.is_occupied = True
                    patient.admission_day = self.current_day 
                    self.allocations[bed.bed_id] = patient 
                    return f"🟢 Bed Allocated Successfully: Observation Bed {bed.bed_id} assigned to {patient.name}."
            
        # Standard unit matching logic
        for bed in self.beds:
            if not bed.is_occupied and bed.bed_type == patient.required_bed:
                bed.is_occupied = True
                patient.admission_day = self.current_day 
                self.allocations[bed.bed_id] = patient 
                return f"🟢 Bed Allocated Successfully: {patient.required_bed} Bed {bed.bed_id} assigned to {patient.name}."

        # Put the patient back in the queue if no matching beds are free
        self.patient_queue.put((priority, patient))
        return f"❌ Allocation Failed: No available {patient.required_bed} bed for {patient.name}."

    def advance_day(self):
        self.current_day += 1 
        return self.discharge_patients()

    def discharge_patients(self):
        discharged_today = [] 
        beds_to_free = []     

        for bed_id, patient in list(self.allocations.items()):
            if patient.admission_day != -1 and (self.current_day - patient.admission_day) >= patient.duration_of_stay:
                discharged_today.append(patient)
                beds_to_free.append(bed_id)

        logs = []
        if beds_to_free:
            for bed_id in beds_to_free:
                patient = self.allocations.pop(bed_id) 
                for bed in self.beds:
                    if bed.bed_id == bed_id:
                        bed.is_occupied = False 
                        logs.append(f"🔵 Patient {patient.name} (ID: {patient.patient_id}) completed treatment and was discharged from Bed {bed.bed_id}.")
                        break
        return logs

# =========================================================================
# 2. APP PRESENTATION LAYER (Replaces terminal input loops)
# =========================================================================

st.set_page_config(page_title="Hospital Bed Management", layout="wide")
st.title("🏥 Smart Patient Triage & Bed Allocation App")

# Store app data across framework cycles using session state
if 'hospital' not in st.session_state:
    # Build your exact hospital infrastructure
    initial_beds = [
        Bed(101, "ICU"), Bed(102, "General"), Bed(103, "Emergency"),
        Bed(104, "ICU"), Bed(105, "General"), Bed(106, "Emergency"),
        Bed(107, "General"), Bed(201, "Observation"), Bed(202, "Observation"),
        Bed(203, "Observation")
    ]
    st.session_state.hospital = HospitalBedAllocation(initial_beds)
    st.session_state.action_logs = ["System initialized with default beds inventory configuration."]

hosp = st.session_state.hospital

# Real-time Key Metrics
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Simulation Timeline Clock", value=f"Day {hosp.current_day}")
with m2:
    st.metric(label="Patients in Triage Queue", value=hosp.patient_queue.qsize())
with m3:
    occupied = sum(1 for b in hosp.beds if b.is_occupied)
    st.metric(label="Total Capacity Load", value=f"{occupied} / {len(hosp.beds)} Beds Occupied")

st.markdown("---")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("⚙️ Control Dashboard Operations")
    
    # User Input Form (replaces console input loops)
    with st.form("triage_form", clear_on_submit=True):
        st.write("**Patient Triage & Intake Form**")
        p_id = st.number_input("Patient Tracking ID", min_value=1, step=1, value=101)
        p_name = st.text_input("Full Patient Name", value="Jane Doe")
        p_severity = st.slider("Clinical Urgency Severity (1-10)", min_value=1, max_value=10, value=5)
        
        # Rule sets for severity inference
        if p_severity < 5:
            inf_bed, inf_stay = "Observation", 2
        elif 5 <= p_severity <= 7:
            inf_bed, inf_stay = "General", 4
        else:
            inf_bed, inf_stay = "ICU", 7
            
        st.caption(f"ℹ️ *System Automation Rules applied: Inferred **{inf_bed}** unit for **{inf_stay} days**.*")
        
        if st.form_submit_button("📥 Register Patient into Priority Queue"):
            new_patient = Patient(p_id, p_name, p_severity, inf_bed, inf_stay)
            hosp.add_patient(new_patient)
            st.session_state.action_logs.append(f"📋 Enqueued Patient {p_name} into system database.")
            st.rerun()

    st.write("**Run Allocation & Scheduling Engines**")
    if st.button("⚡ Execute Allocation (Greedy Placement Search)", use_container_width=True, type="primary"):
        result_message = hosp.allocate_bed()
        st.session_state.action_logs.append(result_message)
        st.rerun()
        
    if st.button("⏩ Advance Operations Clock (+1 Day)", use_container_width=True):
        discharge_notices = hosp.advance_day()
        st.session_state.action_logs.append(f"⏳ Timeline shifted forward to operational Day {hosp.current_day}.")
        if discharge_notices:
            st.session_state.action_logs.extend(discharge_notices)
        st.rerun()

with col_right:
    st.subheader("📊 Dynamic Facility Map Overview")
    
    # Process structured data from your core script arrays into readable dataframes
    bed_grid = []
    for b in hosp.beds:
        pat = hosp.allocations.get(b.bed_id)
        bed_grid.append({
            "Bed ID": b.bed_id,
            "Care Unit Type": b.bed_type,
            "Current State": "🔴 Occupied" if b.is_occupied else "🟢 Free & Available",
            "Patient Name": pat.name if pat else "—",
            "Urgency Score": pat.severity if pat else "—",
            "Treatment Days Left": (pat.duration_of_stay - (hosp.current_day - pat.admission_day)) if pat else "—"
        })
    st.dataframe(bed_grid, use_container_width=True, hide_index=True)

    st.subheader("📜 Event Activity Logs")
    with st.container(height=220):
        for log in reversed(st.session_state.action_logs):
            st.write(log)
