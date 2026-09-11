"""Notification delivery: template lookup, rendering and (mock) channel send."""

from __future__ import annotations

import logging

from common.clock import utc_now
from common.ids import next_id
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationRecord, NotificationTemplateVersion
from app.services.renderer import render

logger = logging.getLogger("notification-service.delivery")

_EVENT_TEMPLATE = {
    "user.registered": ("USER_WELCOME_EMAIL", "EMAIL"),
    "order.created": ("ORDER_CREATED_EMAIL", "EMAIL"),
    "order.paid": ("ORDER_PAID_EMAIL", "EMAIL"),
    "order.cancelled": ("ORDER_CANCELLED_EMAIL", "EMAIL"),
    "order.shipped": ("ORDER_SHIPPED_EMAIL", "EMAIL"),
    "payment.failed": ("PAYMENT_FAILED_EMAIL", "EMAIL"),
    "payment.refunded": ("REFUND_SUCCEEDED_EMAIL", "EMAIL"),
    "stock.low": ("OPS_STOCK_LOW_EMAIL", "EMAIL"),
}


def _record_no() -> str:
    return f"NT{utc_now().strftime('%Y%m%d')}{next_id() % 100000000:08d}"


_DEFAULT_BODIES = {
    "USER_WELCOME_EMAIL": "欢迎注册 {{nickname|default:顾客}}，感谢加入我们！",
    "ORDER_CREATED_EMAIL": "订单 {{order_no}} 已创建，金额 {{total_amount_cents}} 分，请在 {{expires_at}} 前完成支付。",
    "ORDER_PAID_EMAIL": "订单 {{order_no}} 支付成功，感谢购买。",
    "ORDER_CANCELLED_EMAIL": "订单 {{order_no}} 已取消。",
    "ORDER_SHIPPED_EMAIL": "订单 {{order_no}} 已发货，物流公司 {{carrier}}，单号 {{tracking_no}}。",
    "PAYMENT_FAILED_EMAIL": "订单 {{order_no}} 支付失败，请重新支付。",
    "REFUND_SUCCEEDED_EMAIL": "订单 {{order_no}} 退款 {{amount_cents}} 分成功。",
    "OPS_STOCK_LOW_EMAIL": "商品 {{spu_title}}（{{spec_name}}）库存告急，当前可售 {{available}}，阈值 {{threshold}}。",
}


def _mask_recipient(recipient: str) -> str:
    if "@" in recipient:
        local, domain = recipient.split("@", 1)
        return f"{local[:1]}***@{domain}"
    return f"{recipient[:3]}****{recipient[-4:]}" if len(recipient) > 7 else "***"


def _resolve_recipient(payload: dict, event_type: str, settings) -> str | None:
    if event_type == "stock.low":
        return settings.ops_alert_emails
    return payload.get("email") or None


async def dispatch_event(session_factory, envelope: dict, settings) -> dict:
    event_type = envelope.get("event_type", "")
    event_id = envelope.get("event_id")
    payload = envelope.get("payload") or {}

    if event_type not in _EVENT_TEMPLATE:
        return {"status": "IGNORED"}
    template_code, channel = _EVENT_TEMPLATE[event_type]

    recipient = _resolve_recipient(payload, event_type, settings)
    if not recipient:
        return {"status": "SKIPPED", "reason": "no-recipient"}

    variables = dict(payload)

    async with session_factory() as session:
        # Idempotency: one record per event.
        existing = (await session.execute(
            select(NotificationRecord).where(NotificationRecord.event_id == event_id,
                                             NotificationRecord.template_code == template_code)
        )).scalar_one_or_none()
        if existing is not None:
            return {"status": "DUPLICATE", "record_no": existing.record_no}

        version = (await session.execute(
            select(NotificationTemplateVersion)
            .where(NotificationTemplateVersion.template_code == template_code)
            .order_by(NotificationTemplateVersion.version.desc()).limit(1)
        )).scalar_one_or_none()

        body = version.body_template if version else _DEFAULT_BODIES.get(template_code, "")
        subject = version.title_template if version and version.title_template else template_code
        rendered = render(body, variables)
        rendered_subject = render(subject or "", variables)

        rec_no = _record_no()
        record = NotificationRecord(
            id=next_id(), record_no=rec_no, event_id=event_id, event_type=event_type,
            trigger_source="EVENT", user_id=int(payload.get("user_id", 0)) if payload.get("user_id") else None,
            template_code=template_code, template_version=version.version if version else 1,
            channel=channel, provider="SENDGRID" if channel == "EMAIL" else "TWILIO",
            recipient_masked=_mask_recipient(recipient), subject=rendered_subject,
            status="SENT", provider_message_id=f"mock_{rec_no}", sent_at=utc_now())
        session.add(record)
        await session.commit()
        logger.info("notification sent", extra={"record_no": record.record_no,
                                                "template_code": template_code, "event_type": event_type})
        return {"status": "SENT", "record_no": record.record_no, "rendered": rendered}


async def list_records(session: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    from sqlalchemy import func as sqlfunc

    total = int((await session.execute(
        select(sqlfunc.count()).select_from(NotificationRecord))).scalar_one())
    rows = list((await session.execute(
        select(NotificationRecord).order_by(NotificationRecord.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size))).scalars().all())
    items = [{
        "record_no": r.record_no, "event_type": r.event_type, "template_code": r.template_code,
        "channel": r.channel, "provider": r.provider, "recipient_masked": r.recipient_masked,
        "subject": r.subject, "status": r.status, "retry_count": r.retry_count,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        "created_at": r.created_at.isoformat(),
    } for r in rows]
    return {"items": items, "pagination": {"page": page, "page_size": page_size, "total": total,
                                          "total_pages": max(1, (total + page_size - 1) // page_size)}}