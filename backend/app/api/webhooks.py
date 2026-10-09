from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models import RelocationProject
from backend.app.api.projects import user_decision, UserDecisionRequest

router = APIRouter(prefix="/api/webhooks/n8n", tags=["n8n Webhooks"])


class N8nResumeRequest(BaseModel):
    project_id: str
    callback_token: Optional[str] = None
    user_choice: str = Field(..., description="APPROVE, REJECT, SELECT_OPTION_A, SELECT_OPTION_B")
    notes: Optional[str] = None


class N8nWebhookResponse(BaseModel):
    success: bool
    project_id: str
    status: str
    message: str


@router.get("/health")
def webhook_health_check():
    """Health check endpoint for n8n HTTP Request nodes."""
    return {"status": "ok", "service": "NEXMOVE-FastAPI-Bridge", "n8n_compatible": True}


@router.post("/resume", response_model=N8nWebhookResponse)
def resume_from_n8n_approval(req: N8nResumeRequest, db: Session = Depends(get_db)):
    """Receives resume callback from n8n Human-in-the-Loop Wait node and updates the plan."""
    project = db.query(RelocationProject).filter_by(id=req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{req.project_id}' not found.")

    decision_req = UserDecisionRequest(
        decision_action=req.user_choice,
        notes=req.notes or f"Resumed via n8n workflow callback (token: {req.callback_token})"
    )

    updated_project = user_decision(req.project_id, decision_req, db)

    return N8nWebhookResponse(
        success=True,
        project_id=req.project_id,
        status=updated_project.status,
        message=f"Successfully resumed project via n8n callback. Current status: {updated_project.status}"
    )
