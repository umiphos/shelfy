"""
Bot de Facebook Messenger
--------------------------
Reutiliza la misma lógica de comandos del bot de WhatsApp.
Comandos disponibles:
  vincular <email>             → vincula tu Messenger a tu cuenta
  agregar <nombre> <precio>    → crea producto
  agotado <id>                 → marca como no disponible
  disponible <id>              → marca como disponible
  mis productos                → lista productos
  ayuda                        → menú de comandos
"""
import httpx
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.catalog import Business
from app.routers.bot import parse_command, handle_command, handle_vincular
from app.config import settings

router = APIRouter(prefix="/bot", tags=["messenger bot"])

MESSENGER_API = "https://graph.facebook.com/v19.0/me/messages"


# ── Verificación del webhook (GET) ────────────────────────────────────────────

@router.get("/messenger")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta llama este endpoint para verificar que el servidor es tuyo.
    Compara hub.verify_token con tu MESSENGER_VERIFY_TOKEN.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.MESSENGER_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Verify token mismatch")


# ── Recibir mensajes (POST) ───────────────────────────────────────────────────

@router.post("/messenger")
async def messenger_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await request.json()

    # Meta manda un array de entries con mensajes
    for entry in body.get("object") == "page" and body.get("entry", []) or []:
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {})
            text = message.get("text", "").strip()

            if not sender_id or not text:
                continue

            # Comando vincular — no requiere estar registrado
            cmd = parse_command(text)
            if cmd["action"] == "vincular":
                response_text = handle_vincular(cmd["email"], sender_id, "messenger", db)
                await send_message(sender_id, response_text)
                continue

            # Para el resto, buscar negocio por messenger_id
            business = (
                db.query(Business)
                .filter(
                    Business.messenger_id == sender_id,
                    Business.is_active == True,
                )
                .first()
            )

            if not business:
                await send_message(sender_id, (
                    "❌ Tu cuenta no está registrada en Shelfy.\n"
                    "Regístrate en shelfy.com para usar el bot."
                ))
                continue

            cmd = parse_command(text)
            response_text = handle_command(cmd, business, db)
            await send_message(sender_id, response_text)

    # Meta espera siempre 200 OK inmediato
    return {"status": "ok"}


# ── Enviar mensaje de vuelta ──────────────────────────────────────────────────

async def send_message(recipient_id: str, text: str):
    """Llama a la Graph API para responder al usuario."""
    async with httpx.AsyncClient() as client:
        await client.post(
            MESSENGER_API,
            params={"access_token": settings.MESSENGER_PAGE_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text},
            },
        )
