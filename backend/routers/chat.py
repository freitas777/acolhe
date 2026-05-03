from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging

from backend.database import get_db
from backend.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ConversationCreate,
    ConversationResponse,
    ChatRequest,
    ChatResponse
)
from backend.services.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

conversations_db = {}

def generate_id() -> str:
    return f"conv_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db)
):
    conversation_id = generate_id()
    
    conversation = {
        "id": conversation_id,
        "title": data.title,
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "user_id": 1
    }
    
    conversations_db[conversation_id] = conversation

    ai_service.start_chat(
        system_instruction="""
        Você é o Acolhe+, um assistente educacional especializado em educação inclusiva.
        Seu objetivo é ajudar professores e psicopedagogos a criar estratégias e conteúdos
        adaptados para alunos com necessidades educacionais específicas.
        
        Seja prestativo, claro e sempre focado na inclusão e acessibilidade.
        """
    )
    
    return conversation


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(db: Session = Depends(get_db)):
    return list(conversations_db.values())


@router.post("/send", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        conversation_id = data.conversation_id or generate_id()
        
        if conversation_id not in conversations_db:
            conversations_db[conversation_id] = {
                "id": conversation_id,
                "title": "Nova conversa",
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "user_id": 1
            }
        
        conversation = conversations_db[conversation_id]

        user_message = ChatMessageResponse(
            id=generate_id(),
            role="user",
            content=data.message,
            created_at=datetime.now()
        )
        

        conversation["messages"].append(user_message.model_dump())

        if len(conversation["messages"]) == 1:
            conversation["title"] = data.message[:50] + ("..." if len(data.message) > 50 else "")
        
        logger.info(f"Gerando resposta para: {data.message[:50]}...")
        
        try:
            assistant_content = await ai_service.generate_response(data.message)
            
            assistant_message = ChatMessageResponse(
                id=generate_id(),
                role="assistant",
                content=assistant_content,
                created_at=datetime.now()
            )
            
            conversation["messages"].append(assistant_message.model_dump())
            
        except Exception as ai_error:
            logger.error(f"Erro na IA: {ai_error}")
            assistant_message = ChatMessageResponse(
                id=generate_id(),
                role="assistant",
                content="Desculpe, estou com dificuldades para responder no momento. Tente novamente.",
                created_at=datetime.now()
            )
        
        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/educational-content")
async def generate_educational_content(
    tema: str,
    perfil_aluno: dict,
    db: Session = Depends(get_db)
):
    try:
        content = await ai_service.generate_educational_content(tema, perfil_aluno)
        
        return {
            "success": True,
            "tema": tema,
            "conteudo": content,
            "gerado_em": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar conteúdo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    if conversation_id in conversations_db:
        del conversations_db[conversation_id]
    
    ai_service.clear_history()
    
    return
