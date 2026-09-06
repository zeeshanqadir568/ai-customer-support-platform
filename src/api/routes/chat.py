"""POST /chat - run the support agent on one customer message."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from agent.llm import LLMClient
from agent.orchestrator import SupportAgent
from api.deps import ConversationStore, get_db, get_llm, get_store, settings_dep
from core.config import Settings
from models.schemas import ChatRequest, ChatResponse, ToolCallView

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    llm: LLMClient = Depends(get_llm),
    conn=Depends(get_db),
    settings: Settings = Depends(settings_dep),
    store: ConversationStore = Depends(get_store),
) -> ChatResponse:
    conversation_id = req.conversation_id or uuid4().hex
    history = store.get(conversation_id)

    agent = SupportAgent(llm=llm, conn=conn, settings=settings)
    try:
        result = agent.run(
            req.message, history=history, customer_email=req.customer_email
        )
    except Exception as exc:  # noqa: BLE001 - turn any agent failure into a clean 502
        # The LLM provider timed out, refused the connection, returned an
        # error, or the agent hit an unexpected snag. The customer should see
        # a helpful message, never a stack trace.
        logger.exception("Support agent failed for conversation %s", conversation_id)
        store.drop(conversation_id)
        raise HTTPException(
            status_code=502,
            detail=(
                "The support agent could not complete this request right now "
                f"({type(exc).__name__}). Please try again in a moment. If it "
                "keeps happening, check that the model is reachable and the "
                "API key is valid."
            ),
        ) from exc

    if result.resolved:
        store.put(conversation_id, agent.transcript)
    else:
        # Conversation now belongs to a human; don't let the bot resume it.
        store.drop(conversation_id)

    return ChatResponse(
        conversation_id=conversation_id,
        reply=result.reply,
        resolved=result.resolved,
        escalated=result.escalated,
        ticket_id=result.ticket_id,
        steps=result.steps,
        tool_calls=[
            ToolCallView(
                step=c.step, name=c.name, input=c.input, outcome=c.outcome
            )
            for c in result.tool_calls
        ],
    )
