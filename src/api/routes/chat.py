"""POST /chat - run the support agent on one customer message."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends

from agent.llm import LLMClient
from agent.orchestrator import SupportAgent
from api.deps import ConversationStore, get_db, get_llm, get_store, settings_dep
from core.config import Settings
from models.schemas import ChatRequest, ChatResponse, ToolCallView

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
    result = agent.run(
        req.message, history=history, customer_email=req.customer_email
    )

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
