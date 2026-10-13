"""
history.py - Endpoints for session listing, reloading, comparison, and deletion.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.core.database import list_sessions, get_session, delete_session

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/")
async def get_all_sessions(limit: int = 50):
    """Lists saved analysis sessions."""
    return list_sessions(limit=limit)

@router.get("/{session_id}")
async def get_single_session(session_id: str):
    """Retrieves full details of a saved analysis session."""
    data = get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found.")
    return data

@router.delete("/{session_id}")
async def remove_session(session_id: str):
    """Deletes an analysis session from the database."""
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or already deleted.")
    return {"status": "deleted", "session_id": session_id}
