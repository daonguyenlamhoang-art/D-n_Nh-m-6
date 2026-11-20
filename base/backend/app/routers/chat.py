"""Router Chat giữa Khách hàng và Cửa hàng (T3D2DC1)."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin
from app.db.session import get_db
from app.models.chat import ChatMessage
from app.models.user import User
from app.schemas.chat import AdminChatReply, ChatMessageCreate, ChatMessageOut

router = APIRouter(tags=["Chat"])


@router.post("/chat/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def customer_send_message(
    msg_in: ChatMessageCreate,
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Khách gửi tin nhắn hỗ trợ cho cửa hàng (T3D2DC1)."""
    tok = (msg_in.guest_token or x_guest_token or "").strip()
    if not tok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GUEST_TOKEN_REQUIRED", "message": "Thiếu mã phiên chat của khách", "details": {}},
        )
    text_clean = msg_in.message.strip()
    if not text_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_MESSAGE", "message": "Nội dung tin nhắn không được để trống", "details": {}},
        )

    chat_msg = ChatMessage(
        sender_type="customer",
        guest_token=tok,
        customer_name=(msg_in.customer_name or "Khách hàng").strip() or "Khách hàng",
        order_id=msg_in.order_id,
        message=text_clean,
        is_read=False,
    )
    db.add(chat_msg)
    db.commit()
    db.refresh(chat_msg)
    return ChatMessageOut.model_validate(chat_msg)


@router.get("/chat/messages", response_model=list[ChatMessageOut])
def customer_poll_messages(
    guest_token: Optional[str] = Query(None),
    since: int = Query(0, ge=0, description="Lấy các tin nhắn mới có id > since"),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Khách lấy danh sách tin nhắn định kỳ (since = id tin cuối) (T3D2DC1)."""
    tok = (guest_token or x_guest_token or "").strip()
    if not tok:
        return []

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.guest_token == tok, ChatMessage.id > since)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    # Đánh dấu các tin nhắn do cửa hàng gửi đã được khách đọc
    unread_admin_msgs = [m for m in messages if m.sender_type == "admin" and not m.is_read]
    if unread_admin_msgs:
        for m in unread_admin_msgs:
            m.is_read = True
        db.commit()

    return [ChatMessageOut.model_validate(m) for m in messages]


# ----------------- NHÂN VIÊN / ADMIN XỬ LÝ CHAT (T3D2DC1) -----------------
@router.get("/admin/chat/conversations")
def admin_list_chat_conversations(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Danh sách các cuộc hội thoại với khách kèm số tin chưa đọc (T3D2DC1)."""
    all_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.guest_token.isnot(None))
        .order_by(ChatMessage.id.asc())
        .all()
    )

    conv_map: dict[str, dict] = {}
    for m in all_msgs:
        tok = m.guest_token or "unknown"
        if tok not in conv_map:
            conv_map[tok] = {
                "guest_token": tok,
                "customer_name": m.customer_name or f"Khách #{tok[:6]}",
                "last_message": m.message,
                "last_sender": m.sender_type,
                "last_time": m.created_at,
                "last_id": m.id,
                "unread_count": 0,
            }
        conv = conv_map[tok]
        if m.customer_name and m.sender_type == "customer":
            conv["customer_name"] = m.customer_name
        conv["last_message"] = m.message
        conv["last_sender"] = m.sender_type
        conv["last_time"] = m.created_at
        conv["last_id"] = m.id
        if m.sender_type == "customer" and not m.is_read:
            conv["unread_count"] += 1

    conversations = sorted(conv_map.values(), key=lambda x: x["last_id"], reverse=True)
    total_unread = sum(c["unread_count"] for c in conversations)

    return {
        "total_unread": total_unread,
        "conversations": conversations,
    }


@router.get("/admin/chat/messages", response_model=list[ChatMessageOut])
def admin_get_conversation_messages(
    guest_token: str = Query(..., min_length=1),
    since: int = Query(0, ge=0),
    mark_read: bool = Query(True),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Nhân viên lấy tin nhắn của 1 khách hàng (since = id tin cuối) và đánh dấu đã đọc (T3D2DC1)."""
    tok = guest_token.strip()
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.guest_token == tok, ChatMessage.id > since)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    if mark_read:
        unread = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.guest_token == tok,
                ChatMessage.sender_type == "customer",
                ChatMessage.is_read == False,
            )
            .all()
        )
        if unread:
            for m in unread:
                m.is_read = True
            db.commit()

    return [ChatMessageOut.model_validate(m) for m in messages]


@router.post("/admin/chat/reply", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def admin_reply_chat_message(
    rep_in: AdminChatReply,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Nhân viên trả lời tin nhắn của khách hàng (T3D2DC1)."""
    tok = rep_in.guest_token.strip()
    text_clean = rep_in.message.strip()
    if not text_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_MESSAGE", "message": "Nội dung trả lời không được để trống", "details": {}},
        )

    # Đánh dấu các tin nhắn trước đó của khách là đã đọc
    db.query(ChatMessage).filter(
        ChatMessage.guest_token == tok,
        ChatMessage.sender_type == "customer",
        ChatMessage.is_read == False,
    ).update({"is_read": True})

    reply_msg = ChatMessage(
        user_id=current_admin.id,
        sender_type="admin",
        guest_token=tok,
        customer_name=rep_in.customer_name or "NightFood CSKH",
        message=text_clean,
        is_read=False,
    )
    db.add(reply_msg)
    db.commit()
    db.refresh(reply_msg)
    return ChatMessageOut.model_validate(reply_msg)
