"""Authenticated endpoints consumed by the Next.js application."""

from typing import List, Optional, Union

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agents.communication_agent import CommunicationOutput, draft_communication
from backend.schemas.communication import CommunicationRequest
from backend.agents.explanation_agent import ExplanationOutput, explain_recommendation
from backend.agents.extraction_agent import ExtractionOutput, extract_meeting_info
from backend.agents.recommendation_agent import RecommendationOutput, generate_recommendations
from backend.app.db import Email, Investor, Meeting, Notification, User
from backend.database.session import get_db
from backend.services.auth_service import get_current_user
from backend.services.email_service import EmailService
from backend.services.notification_service import NotificationService
from backend.services.dashboard_service import get_dashboard_summary

router = APIRouter(tags=["Frontend"])


class ExtractRequest(BaseModel):
    transcript_text: str


class RecommendRequest(BaseModel):
    investor_profile: Optional[str] = ""
    meeting_summary: str
    memory: Optional[str] = ""
    past_meetings: Optional[Union[str, List[str]]] = ""


class ExplainRequest(BaseModel):
    recommendation: str
    investor_memory: Optional[str] = ""
    meeting_history: Optional[str] = ""



class EmailRequest(BaseModel):
    investor_id: str
    subject: str
    body: str
    tone: str = "Professional"
    type: str = "Follow-up Email"


def owned_investor(db: Session, investor_id: str, user_id: int) -> Investor:
    investor = db.query(Investor).filter(
        Investor.id == investor_id,
        Investor.owner_id == user_id,
    ).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    return {"status": "healthy", "database": "ready"}


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = get_dashboard_summary(db, current_user.id)
    return {
        "founder_name": current_user.full_name,
        **summary,
    }


@router.get("/search")
def search(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    value = f"%{query.strip()}%"
    if value == "%%":
        return []
    investors = db.query(Investor).filter(
        Investor.owner_id == current_user.id,
        (Investor.name.ilike(value)) |
        (Investor.firm.ilike(value)) |
        (Investor.location.ilike(value)),
    ).limit(10).all()
    return [{
        "id": investor.id,
        "name": investor.name,
        "firm": investor.firm,
        "role": investor.role,
        "location": investor.location,
        "typical_check": investor.typical_check,
        "status": investor.status,
        "match_score": 100,
    } for investor in investors]


@router.get("/notifications")
def notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = NotificationService.get_all(db, owner_id=current_user.id)
    return [{
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "link": row.link,
        "isRead": row.is_read,
        "createdAt": row.created_at.isoformat(),
    } for row in rows]


@router.post("/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = NotificationService.get_by_id(db, notification_id, owner_id=current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read = True
    db.commit()
    return {"status": "success"}


@router.post("/send-email")
def save_email(
    payload: EmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investor = owned_investor(db, payload.investor_id, current_user.id)
    email = EmailService.create(
        db,
        investor_id=investor.id,
        subject=payload.subject,
        body=payload.body,
        tone=payload.tone,
        type_=payload.type,
        owner_id=current_user.id
    )
    return {
        "status": "success",
        "message": "Draft saved. External email delivery is not configured.",
        "email_id": email.id,
    }


@router.post("/upload")
async def inspect_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    return {
        "status": "accepted",
        "file_name": file.filename,
        "content_type": file.content_type,
    }


@router.post("/extract", response_model=ExtractionOutput)
def extract(
    payload: ExtractRequest,
    current_user: User = Depends(get_current_user),
):
    if not payload.transcript_text.strip():
        raise HTTPException(status_code=422, detail="Transcript cannot be empty")
    return extract_meeting_info(payload.transcript_text)


@router.post("/extract-file", response_model=ExtractionOutput)
async def extract_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if file.content_type not in {"text/plain", "text/markdown", "application/pdf"}:
        raise HTTPException(
            status_code=415,
            detail="Only text, Markdown, and text-based PDF transcripts are supported",
        )
    if file.content_type == "application/pdf":
        from io import BytesIO
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    else:
        text = content.decode("utf-8")
    if not text.strip():
        raise HTTPException(status_code=422, detail="No transcript text was found")
    return extract_meeting_info(text)


@router.post("/recommend", response_model=RecommendationOutput)
def recommend(
    payload: RecommendRequest,
    current_user: User = Depends(get_current_user),
):
    history = (
        "\n".join(payload.past_meetings)
        if isinstance(payload.past_meetings, list)
        else payload.past_meetings
    )
    return generate_recommendations(
        investor_profile=payload.investor_profile or "",
        meeting_summary=payload.meeting_summary,
        memory=payload.memory or "",
        past_meetings=history or "",
    )


@router.post("/explain", response_model=ExplanationOutput)
def explain(
    payload: ExplainRequest,
    current_user: User = Depends(get_current_user),
):
    return explain_recommendation(
        recommendation=payload.recommendation,
        investor_memory=payload.investor_memory or "",
        meeting_history=payload.meeting_history or "",
    )


@router.post("/communication", response_model=CommunicationOutput)
def communicate(
    payload: CommunicationRequest,
    current_user: User = Depends(get_current_user),
):
    return draft_communication(
        investor_name=payload.investor_name,
        communication_type=payload.communication_type,
        tone=payload.tone,
        meeting_context=payload.meeting_context or "",
        founder_message=payload.founder_message or "",
        attachments=payload.attachments or [],
        additional_instructions=payload.additional_instructions or ""
    )


@router.get("/followups/context")
def get_followup_context(
    investor_name: Optional[str] = None,
    investor_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches context (recent meeting summary, commitments, key memories) to prefill the composer.
    """
    from backend.services.investor_service import InvestorService
    from backend.services.meeting_service import MeetingService
    from backend.services.memory_service import MemoryService
    
    investor = None
    if investor_id:
        investor = InvestorService.get_by_id(db, investor_id, current_user.id)
    elif investor_name:
        investor = InvestorService.get_by_name(db, investor_name, current_user.id)
        
    if not investor:
        return {
            "meeting_context": "No active CRM context found. Standard outbound detail prefilled.",
            "founder_message": "",
            "attachments": []
        }
        
    # Get last meeting
    meetings = MeetingService.get_all(db, current_user.id, investor.id)
    last_meeting_summary = meetings[0].summary if meetings else ""
    
    # Get memories
    memories = MemoryService.get_all(db, current_user.id, investor.id)
    memories_str = "; ".join([m.memory for m in memories])
    
    context_str = f"Investor: {investor.name} from {investor.firm}. "
    if last_meeting_summary:
        context_str += f"Last meeting summary: {last_meeting_summary}. "
    if memories_str:
        context_str += f"Key relationship memories: {memories_str}."
        
    return {
        "meeting_context": context_str,
        "founder_message": f"Great speaking with you about our developer workflow and data pipelines.",
        "attachments": []
    }

