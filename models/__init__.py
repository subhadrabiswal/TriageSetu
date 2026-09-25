"""
models/__init__.py
---------------------
Importing every model here means that when app.database.Base is
used to create tables (Base.metadata.create_all), SQLAlchemy already
knows about all of them - just import this package once at startup.
"""

from app.models.facility import Facility, FacilityType, DigitalMaturityLevel
from app.models.user import User, UserRole
from app.models.patient import Patient, AgeRange
from app.models.patient_pii import PatientPII
from app.models.symptom_report import SymptomReport, InputMode
from app.models.document import UploadedDocument, DocumentType
from app.models.triage_note import TriageNote, RiskCategory, TriageStatus
from app.models.reviewer_action import ReviewerAction, ReviewerActionType
from app.models.referral import Referral, ReferralStatus
from app.models.facility_queue import FacilityQueue, QueueStatus
from app.models.consent_record import ConsentRecord, ConsentType
from app.models.audit_log import AuditLog
from app.models.followup_answer import FollowUpAnswer

