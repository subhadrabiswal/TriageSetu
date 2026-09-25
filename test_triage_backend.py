"""
tests/test_triage_backend.py
------------------------------
Comprehensive automated tests for Multimodal Healthcare Triage Assistant (PS03):
1. Users & Roles (5 distinct roles: patient, health_worker, nurse, doctor, admin)
2. Patient PII Isolation (patient_contact_pii vault table linked via anonymized_token, RBAC access control)
3. Timestamped Consent Capture & Immutable Audit Logging
4. Reviewer Workflows (prioritized queue retrieval Red > Yellow > Green, review actions approve, edit, escalate)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import database
from app.database import Base, get_db
from app.models.facility import Facility, FacilityType


client = TestClient(app)


def setup_clean_db():
    Base.metadata.drop_all(bind=database.engine)
    Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    facility = Facility(
        name="Test Community Hospital",
        facility_type=FacilityType.GOVT_HOSPITAL,
        state="Odisha",
        district="Khurda",
    )
    db.add(facility)
    db.commit()
    facility_id = facility.facility_id
    db.close()
    return facility_id


def test_users_and_roles_registration_auth():
    """Requirement 1: Test registration & login for all 5 roles."""
    facility_id = setup_clean_db()
    roles = ["patient", "health_worker", "nurse", "doctor", "admin"]
    tokens = {}

    for role in roles:
        # Register staff / patient user
        reg_resp = client.post(
            "/auth/register",
            json={
                "name": f"Test {role.capitalize()}",
                "username": f"user_{role}",
                "password": "Password@123",
                "role": role,
                "facility_id": facility_id,
                "preferred_language": "hi",
            },
        )
        assert reg_resp.status_code == 200, f"Registration failed for role {role}: {reg_resp.text}"
        data = reg_resp.json()
        assert data["role"] == role
        assert data["facility_id"] == facility_id
        assert "access_token" in data
        tokens[role] = data["access_token"]

    # Verify invalid role returns 400
    bad_reg = client.post(
        "/auth/register",
        json={
            "name": "Invalid User",
            "username": "invalid_user",
            "password": "Password@123",
            "role": "superhero",
        },
    )
    assert bad_reg.status_code == 400


def test_patient_pii_isolation_and_rbac():
    """Requirement 2: Test patient PII isolation vault table and RBAC enforcement."""
    facility_id = setup_clean_db()

    # Register Doctor (authorized to access PII) and Health Worker (unauthorized)
    doc_resp = client.post(
        "/auth/register",
        json={"name": "Dr. Smith", "username": "dr_smith", "password": "Pass@123", "role": "doctor", "facility_id": facility_id},
    )
    doc_token = doc_resp.json()["access_token"]

    hw_resp = client.post(
        "/auth/register",
        json={"name": "Worker Priya", "username": "worker_priya", "password": "Pass@123", "role": "health_worker", "facility_id": facility_id},
    )
    hw_token = hw_resp.json()["access_token"]

    # Register patient with PII name & phone
    patient_resp = client.post(
        "/patients",
        json={
            "facility_id": facility_id,
            "age_range": "19-40",
            "gender": "Female",
            "preferred_language": "or",
            "consent_given": True,
            "name": "Sita Devi",
            "contact_number": "+919876543210",
        },
        headers={"Authorization": f"Bearer {hw_token}"},
    )
    assert patient_resp.status_code == 201
    patient_data = patient_resp.json()

    # Clinical endpoint PatientOut should NOT contain name or contact_number
    assert "name" not in patient_data
    assert "contact_number" not in patient_data
    token = patient_data["anonymized_token"]
    assert token.startswith("PT-")

    # Health Worker attempts to retrieve PII -> Expected 403 Forbidden
    pii_hw_resp = client.get(
        f"/patients/{token}/pii",
        headers={"Authorization": f"Bearer {hw_token}"},
    )
    assert pii_hw_resp.status_code == 403

    # Doctor retrieves PII -> Expected 200 OK with decrypted values
    pii_doc_resp = client.get(
        f"/patients/{token}/pii",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert pii_doc_resp.status_code == 200
    pii_data = pii_doc_resp.json()
    assert pii_data["name"] == "Sita Devi"
    assert pii_data["contact_number"] == "+919876543210"
    assert pii_data["anonymized_token"] == token


def test_consent_capture_and_audit_logging():
    """Requirement 3: Test timestamped consent capture & immutable audit log entries."""
    facility_id = setup_clean_db()

    # Admin user to inspect audit logs
    admin_resp = client.post(
        "/auth/register",
        json={"name": "Admin Boss", "username": "admin_boss", "password": "Pass@123", "role": "admin", "facility_id": facility_id},
    )
    admin_token = admin_resp.json()["access_token"]

    # Register patient with explicit consent
    pat_resp = client.post(
        "/patients",
        json={
            "facility_id": facility_id,
            "age_range": "41-60",
            "gender": "Male",
            "consent_given": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pat_resp.status_code == 201
    pat = pat_resp.json()
    assert pat["consent_given"] is True
    assert pat["consent_timestamp"] is not None

    # Record additional timestamped consent
    consent_resp = client.post(
        f"/patients/{pat['patient_id']}/consent",
        json={
            "patient_id": pat["patient_id"],
            "consent_type": "data_sharing_referral",
            "granted": True,
            "retention_period_days": 180,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert consent_resp.status_code == 201
    assert consent_resp.json()["granted_at"] is not None

    # Submit symptom report
    sym_resp = client.post(
        "/symptoms",
        json={
            "patient_id": pat["patient_id"],
            "input_mode": "text",
            "raw_input_text": "High fever and persistent cough for 4 days.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert sym_resp.status_code == 201

    # Generate AI triage note
    triage_resp = client.post(
        "/triage-notes/generate",
        json={"patient_id": pat["patient_id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert triage_resp.status_code == 201

    # Verify audit logs list
    audit_resp = client.get(
        "/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    action_types = [l["action_type"] for l in logs]

    assert "USER_REGISTERED" in action_types
    assert "PATIENT_REGISTERED" in action_types
    assert "CONSENT_RECORDED" in action_types
    assert "SYMPTOM_REPORT_SUBMITTED" in action_types
    assert "AI_SUMMARY_GENERATED" in action_types


def test_reviewer_workflows_and_queue_prioritization():
    """Requirement 4: Test prioritized queue retrieval (Red > Yellow > Green) and reviewer actions."""
    facility_id = setup_clean_db()

    nurse_resp = client.post(
        "/auth/register",
        json={"name": "Nurse Rita", "username": "nurse_rita", "password": "Pass@123", "role": "nurse", "facility_id": facility_id},
    )
    nurse_token = nurse_resp.json()["access_token"]

    # Create 3 patients: Red (severe chest pain), Yellow (fever), Green (mild cough)
    cases = [
        ("Routine cough", "0-12"),
        ("Severe crushing chest pain and shortness of breath", "60+"),
        ("Moderate fever and dehydration", "19-40"),
    ]

    for text, age in cases:
        p_res = client.post(
            "/patients",
            json={"facility_id": facility_id, "age_range": age, "consent_given": True},
            headers={"Authorization": f"Bearer {nurse_token}"},
        )
        pid = p_res.json()["patient_id"]

        client.post(
            "/symptoms",
            json={"patient_id": pid, "input_mode": "text", "raw_input_text": text},
            headers={"Authorization": f"Bearer {nurse_token}"},
        )

        client.post(
            "/triage-notes/generate",
            json={"patient_id": pid},
            headers={"Authorization": f"Bearer {nurse_token}"},
        )

    # Fetch prioritized queue
    q_resp = client.get("/queue", headers={"Authorization": f"Bearer {nurse_token}"})
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) >= 3

    # Verify queue sorting: Red (rank 1) comes before Yellow (rank 2) comes before Green (rank 3)
    ranks = [item["priority_rank"] for item in queue]
    assert ranks == sorted(ranks), "Queue is not prioritized by risk rank!"

    red_item = [item for item in queue if item["risk_category"] == "red"][0]
    note_id = red_item["triage_note_id"]

    # Review action 1: Edit triage note
    edit_resp = client.patch(
        f"/triage-notes/{note_id}/review",
        json={
            "action_type": "edited",
            "comments": "Reviewed by Nurse Rita, added ECG recommendation.",
            "edited_summary_text": "CRITICAL: Severe chest pain, suspected cardiac issue. Needs immediate doctor evaluation.",
        },
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["action_type"] == "edited"

    # Review action 2: Escalate case
    escalate_resp = client.patch(
        f"/triage-notes/{note_id}/review",
        json={
            "action_type": "escalated",
            "comments": "Escalating to Cardiology ICU.",
        },
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert escalate_resp.status_code == 200
    assert escalate_resp.json()["action_type"] == "escalated"
