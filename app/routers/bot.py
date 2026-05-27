"""
Bot de WhatsApp via Twilio
--------------------------
Comandos disponibles:
  vincular <email>             → vincula tu número de WhatsApp a tu cuenta
  agregar <nombre> <precio>    → crea producto
  agotado <id>                 → marca como no disponible
  disponible <id>              → marca como disponible
  mis productos                → lista productos
  ayuda                        → menú de comandos
"""
import re
from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.catalog import Business, Product

router = APIRouter(prefix="/bot", tags=["whatsapp bot"])

# ── Respuestas del bot ────────────────────────────────────────────────────────

HELP_MSG = """🤖 *PrecioInbox Bot* — Comandos disponibles:

🔗 *vincular <tu-email>*
  Ej: vincular mary@tacos.com

📦 *agregar <nombre> <precio>*
  Ej: agregar Taco de canasta 15

🔴 *agotado <número>*
  Ej: agotado 3

🟢 *disponible <número>*
  Ej: disponible 3

📋 *mis productos*
  Ver tu lista con números

❓ *ayuda*
  Ver este menú"""


def twiml_response(message: str) -> PlainTextResponse:
    """Twilio espera TwiML XML como respuesta."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
    return PlainTextResponse(content=xml, media_type="application/xml")


# ── Parser de comandos ────────────────────────────────────────────────────────

def parse_command(text: str) -> dict:
    """
    Devuelve: {"action": str, ...params}
    Acciones: vincular, agregar, agotado, disponible, listar, ayuda, desconocido
    """
    text = text.strip().lower()

    # vincular <email>
    match = re.match(r"vincular\s+(\S+@\S+\.\S+)$", text)
    if match:
        return {"action": "vincular", "email": match.group(1).strip()}

    # agregar <nombre> <precio>
    match = re.match(r"agregar\s+(.+?)\s+(\d+(?:\.\d{1,2})?)$", text)
    if match:
        return {
            "action": "agregar",
            "name": match.group(1).strip().title(),
            "price": float(match.group(2)),
        }

    # agotado <id>
    match = re.match(r"agotado\s+(\d+)$", text)
    if match:
        return {"action": "agotado", "product_num": int(match.group(1))}

    # disponible <id>
    match = re.match(r"disponible\s+(\d+)$", text)
    if match:
        return {"action": "disponible", "product_num": int(match.group(1))}

    # mis productos
    if text in ("mis productos", "productos", "lista", "listar"):
        return {"action": "listar"}

    # ayuda
    if text in ("ayuda", "help", "hola", "inicio", "menu", "menú", "start"):
        return {"action": "ayuda"}

    return {"action": "desconocido", "text": text}


# ── Lógica del bot ────────────────────────────────────────────────────────────

def handle_command(cmd: dict, business: Business, db: Session) -> str:
    action = cmd["action"]

    if action == "ayuda":
        return HELP_MSG

    if action == "agregar":
        product = Product(
            business_id=business.id,
            name=cmd["name"],
            price=cmd["price"],
            available=True,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return (
            f"✅ Producto agregado:\n"
            f"*{product.name}* — ${float(product.price):.2f}\n"
            f"ID: {product.id}"
        )

    if action in ("agotado", "disponible"):
        available = action == "disponible"
        products = (
            db.query(Product)
            .filter(Product.business_id == business.id)
            .order_by(Product.id)
            .all()
        )
        num = cmd["product_num"]
        if num < 1 or num > len(products):
            return (
                f"❌ Número inválido. Tienes {len(products)} producto(s).\n"
                f"Escribe *mis productos* para ver la lista."
            )
        product = products[num - 1]
        product.available = available
        db.commit()
        estado = "🟢 disponible" if available else "🔴 agotado"
        return f"{estado}: *{product.name}*"

    if action == "listar":
        products = (
            db.query(Product)
            .filter(Product.business_id == business.id)
            .order_by(Product.id)
            .all()
        )
        if not products:
            return "📋 No tienes productos aún.\n\nEscribe:\n*agregar <nombre> <precio>*"
        lines = ["📋 *Tus productos:*\n"]
        for i, p in enumerate(products, 1):
            estado = "🟢" if p.available else "🔴"
            lines.append(f"{i}. {estado} {p.name} — ${float(p.price):.2f}")
        lines.append("\n_Usa el número para cambiar disponibilidad._")
        return "\n".join(lines)

    # Desconocido
    return (
        f"🤔 No entendí: _{cmd.get('text', '')}_\n\n"
        f"Escribe *ayuda* para ver los comandos disponibles."
    )


# ── Lógica de vinculación (compartida con Messenger y WhatsApp) ───────────────

def handle_vincular(email: str, contact_id: str, contact_type: str, db: Session) -> str:
    """
    contact_type: "whatsapp" | "messenger"
    contact_id:   el número de teléfono o el messenger_id
    """
    business = (
        db.query(Business)
        .filter(Business.email == email, Business.is_active == True)
        .first()
    )

    if not business:
        return (
            "❌ No encontré una cuenta con ese email.\n"
            "Regístrate en www.precioinbox.com primero."
        )

    if contact_type == "whatsapp":
        # Verificar que no esté vinculado a otra cuenta
        existing = (
            db.query(Business)
            .filter(Business.whatsapp_number == contact_id, Business.id != business.id)
            .first()
        )
        if existing:
            return "❌ Este número ya está vinculado a otra cuenta."
        business.whatsapp_number = contact_id

    elif contact_type == "messenger":
        existing = (
            db.query(Business)
            .filter(Business.messenger_id == contact_id, Business.id != business.id)
            .first()
        )
        if existing:
            return "❌ Este Messenger ya está vinculado a otra cuenta."
        business.messenger_id = contact_id

    db.commit()
    return (
        f"✅ ¡Cuenta vinculada!\n"
        f"*{business.name}* conectado correctamente.\n\n"
        f"Escribe *ayuda* para ver los comandos disponibles."
    )


# ── Webhook endpoint (WhatsApp/Twilio) ───────────────────────────────────────

@router.post("/message", response_class=PlainTextResponse)
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db),
):
    phone = From.replace("whatsapp:", "").strip()
    text = Body.strip()

    # Comando vincular — no requiere estar registrado
    cmd = parse_command(text)
    if cmd["action"] == "vincular":
        response_text = handle_vincular(cmd["email"], phone, "whatsapp", db)
        return twiml_response(response_text)

    # Para el resto de comandos, buscar negocio por número
    business = (
        db.query(Business)
        .filter(Business.whatsapp_number == phone, Business.is_active == True)
        .first()
    )

    if not business:
        return twiml_response(
            "👋 Bienvenido a PrecioInbox.\n\n"
            "Para vincular tu cuenta escribe:\n"
            "*vincular tu@email.com*\n\n"
            "Si no tienes cuenta, regístrate en:\n"
            "www.precioinbox.com"
        )

    response_text = handle_command(cmd, business, db)
    return twiml_response(response_text)
