from __future__ import annotations

from typing import Any

from threading import Lock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.exact_cell_intelligence import (
    build_exact_cell_intelligence,
)
from backend.app.ai.autonomous_master import (
    run_awareon_agent,
)
from backend.app.ai.conversation_memory import (
    ConversationMemory,
    create_conversation_memory,
)


router = APIRouter(
    prefix="/api/v1/intelligence",
    tags=["intelligence"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class IntelligenceAskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=4000,
    )
    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=80,
    )


_CONVERSATIONS: dict[str, ConversationMemory] = {}
_CONVERSATIONS_LOCK = Lock()
_MAX_CONVERSATIONS = 64
_MAX_TURNS = 12


def _conversation_for(session_id: str) -> ConversationMemory:
    key = session_id.strip() or "default"

    with _CONVERSATIONS_LOCK:
        conversation = _CONVERSATIONS.get(key)

        if conversation is None:
            if len(_CONVERSATIONS) >= _MAX_CONVERSATIONS:
                oldest_key = next(iter(_CONVERSATIONS))
                _CONVERSATIONS.pop(oldest_key, None)

            conversation = create_conversation_memory(key)
            _CONVERSATIONS[key] = conversation

        if len(conversation.turns) > _MAX_TURNS:
            conversation.turns = conversation.turns[-_MAX_TURNS:]

        return conversation


# ============================================================
# AUTONOMOUS AWAREON AGENT
# ============================================================

@router.post(
    "/ask"
)
def ask_awareon(
    request: IntelligenceAskRequest,
) -> dict[str, Any]:

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="query is required.",
        )

    try:
        conversation = _conversation_for(
            request.session_id
        )

        result = run_awareon_agent(
            query,
            conversation=conversation,
        )

        payload = result.to_dict()
        payload["conversation"] = {
            "session_id": conversation.session_id,
            "turn_count": len(conversation.turns),
        }

        return {
            "success": True,
            **payload,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "AwareOn autonomous intelligence failed. "
                "Check the backend logs for diagnostic details."
            ),
        )


# ============================================================
# EXACT CELL INTELLIGENCE
# ============================================================

@router.get(
    "/cell/{cell_id}"
)
def exact_cell_intelligence(
    cell_id: str,
    rainfall_change_percent: float = 100.0,
    radius_m: float = 5000.0,
):
    """
    Return the complete AwareOn intelligence state
    for one exact cell.
    """

    if not cell_id:
        raise HTTPException(
            status_code=400,
            detail="cell_id is required.",
        )

    if radius_m <= 0:
        raise HTTPException(
            status_code=400,
            detail="radius_m must be greater than 0.",
        )

    try:
        result = build_exact_cell_intelligence(
            cell_id=cell_id,
            rainfall_change_percent=(
                rainfall_change_percent
            ),
            radius_m=radius_m,
        )

        return {
            "success": True,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Exact cell intelligence failed: "
                f"{exc}"
            ),
        )
