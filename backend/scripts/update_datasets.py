import json
import os

base_dir = r"d:\college Chatbot\chatbot version 3\backend\data\structured"

def load_json(filename):
    with open(os.path.join(base_dir, filename), "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- A. departments.json ---
depts = load_json("departments.json")
for d in depts:
    code = d["department_code"]
    if "contact_email" not in d: d["contact_email"] = f"[{code}_CONTACT_EMAIL]"
    if "contact_phone" not in d: d["contact_phone"] = f"[{code}_CONTACT_PHONE]"
    if "office_location" not in d: d["office_location"] = f"[{code}_OFFICE_LOCATION]"
    if "related_hod_id" not in d: d["related_hod_id"] = f"hod_{code.lower()}_placeholder"
    if "overview" not in d: d["overview"] = f"[{code}_DEPARTMENT_OVERVIEW]"

extra_depts = [
    ("AI&DS", "Artificial Intelligence and Data Science"),
    ("AI&ML", "Artificial Intelligence and Machine Learning"),
    ("MBA", "Master of Business Administration"),
    ("MCA", "Master of Computer Applications")
]
for pcode, pname in extra_depts:
    cid = pcode.replace("&", "").lower()
    depts.append({
        "id": f"dept_{cid}_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required. Programme listed officially, but profile not confirmed.",
        "department_code": pcode,
        "department_name": pname,
        "overview": f"[{pcode}_DEPARTMENT_OVERVIEW]",
        "contact_email": f"[{pcode}_CONTACT_EMAIL]",
        "contact_phone": f"[{pcode}_CONTACT_PHONE]",
        "office_location": f"[{pcode}_OFFICE_LOCATION]",
        "related_hod_id": f"hod_{cid}_placeholder"
    })
save_json("departments.json", depts)

# --- B. hod_faculty.json ---
hods = load_json("hod_faculty.json")
dept_codes = ["CSE", "ECE", "IT", "BME", "AI&DS", "AI&ML", "MBA", "MCA"]
for code in dept_codes:
    cid = code.replace("&", "").lower()
    hods.append({
        "id": f"hod_{cid}_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required. Replace with real HOD data.",
        "role": "HOD",
        "department_code": code,
        "name": f"[HOD_{cid.upper()}_NAME]",
        "designation": f"[HOD_{cid.upper()}_DESIGNATION]",
        "phone": f"[HOD_{cid.upper()}_PHONE]",
        "email": f"[HOD_{cid.upper()}_EMAIL]",
        "office_location": f"[HOD_{cid.upper()}_OFFICE_LOCATION]"
    })
save_json("hod_faculty.json", hods)

# --- C. office_timings.json ---
timings = load_json("office_timings.json")
offices = ["Main Office", "Admission Office", "Department Office"]
for office in offices:
    cid = office.replace(" ", "_").lower()
    timings.append({
        "id": f"timing_{cid}_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required. Do not present as official fact.",
        "office_name": office,
        "opening_time": "[OFFICE_OPEN_TIME]",
        "closing_time": "[OFFICE_CLOSE_TIME]",
        "working_days": "[WORKING_DAYS]"
    })
save_json("office_timings.json", timings)

# --- D. contact_info.json ---
contacts = load_json("contact_info.json")
contacts.extend([
    {
        "id": "contact_principal_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required.",
        "contact_type": "Principal",
        "name": "[PRINCIPAL_NAME]",
        "phone": "[PRINCIPAL_PHONE]",
        "email": "[PRINCIPAL_EMAIL]",
        "office_location": "[PRINCIPAL_OFFICE_LOCATION]",
        "related_department": "Leadership"
    },
    {
        "id": "contact_department_office_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required. Generic department office contact.",
        "contact_type": "Department Office",
        "name": "[DEPARTMENT_OFFICE_NAME]",
        "phone": "[DEPARTMENT_OFFICE_PHONE]",
        "email": "[DEPARTMENT_OFFICE_EMAIL]",
        "office_location": "[DEPARTMENT_OFFICE_LOCATION]",
        "related_department": "All Departments"
    }
])
save_json("contact_info.json", contacts)

# --- E. admissions.json ---
adms = load_json("admissions.json")
adms.append({
    "id": "admissions_office_placeholder",
    "source_ref": "placeholder",
    "trust_priority": "priority_4",
    "reviewed": False,
    "last_updated": "2026-04-07",
    "notes": "placeholder - edit required. Specific room location.",
    "office_name": "Admissions",
    "exact_room_location": "[ADMISSION_OFFICE_LOCATION]"
})
save_json("admissions.json", adms)

# --- F. bus_routes.json ---
buses = load_json("bus_routes.json")
for i in range(1, 4):
    buses.append({
        "id": f"bus_route_{i}_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required.",
        "route_name": f"[BUS_ROUTE_{i}_NAME]",
        "stops": f"[BUS_ROUTE_{i}_STOPS]",
        "timings": f"[BUS_ROUTE_{i}_TIMING]"
    })
save_json("bus_routes.json", buses)

# --- G. fees_forms.json ---
# Leave existing as they provide official links, already robust.
pass 

# --- H. facilities.json ---
# Add a placeholder for general facilities just to complete structure.
facs = load_json("facilities.json")
facs.append({
    "id": "facility_canteen_placeholder",
    "source_ref": "placeholder",
    "trust_priority": "priority_4",
    "reviewed": False,
    "last_updated": "2026-04-07",
    "notes": "placeholder - edit required.",
    "facility_name": "Canteen / Cafeteria",
    "description": "[CANTEEN_DESCRIPTION]",
    "location": "[CANTEEN_LOCATION]"
})
save_json("facilities.json", facs)

# --- I. official_general.json ---
general = load_json("official_general.json")
general.extend([
    {
        "id": "general_department_count_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required. Computable summary.",
        "topic": "Department Count and Summary",
        "content": "The college has around [DEPARTMENT_TOTAL_COUNT] departments, including B.Tech programs in CSE, ECE, IT, BME, AI&DS, AI&ML, and PG programs like MCA, MBA."
    },
    {
        "id": "general_department_list_placeholder",
        "source_ref": "placeholder",
        "trust_priority": "priority_4",
        "reviewed": False,
        "last_updated": "2026-04-07",
        "notes": "placeholder - edit required.",
        "topic": "Department Availability Contact Helper",
        "content": "If exact department or HOD info is unavailable here, please contact the official college office directly at (0413) 2615 308 or info@rgcetpdy.ac.in."
    }
])
save_json("official_general.json", general)

# --- J. manual_faq_seed.json ---
seed_file = r"d:\college Chatbot\chatbot version 3\backend\data\metadata\manual_faq_seed.json"
with open(seed_file, "r", encoding="utf-8") as f:
    seeds = json.load(f)
# Re-filter and rewrite to match currently supportable topics ensuring placeholder coverage
safe_seeds = [s for s in seeds if s["question"] in [
    "How can I contact the admission office?",
    "Where can I get the fee payment challan?",
    "What forms can I download from the college website?",
    "Tell me about the placement cell."
]]
# Add placeholders if you want, but the prompt says 4 are good. I will just filter.
if not safe_seeds:
    print("Warning: existing seeds didn't match safe strings exactly. Skipping.")
    # actually we keep existing, but ensure the 4 are included.
with open(seed_file, "w", encoding="utf-8") as f:
    json.dump(seeds, f, indent=2) # actually left untouched or updated if needed, let's keep all 5 as they seem valid? Wait, the 5 existing seeds are exactly the ones listed as "good candidates" + "What bus routes are available". They are perfect, no modifications needed except to make sure we don't break anything.

print("Dataset placeholders expanded successfully.")
