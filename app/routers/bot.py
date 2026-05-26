"""
Bot de WhatsApp via Twilio
--------------------------
Comandos disponibles:
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

HELP_MSG = """🤖 *Shelfy Bot* — Comandos disponibles:

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
    Acciones: agregar, agotado, disponible, listar, ayuda, desconocido
    """
    text = text.strip().lower()

    # agregar <nombre> <precio>
    # El precio es el último token, el nombre es todo lo del medio
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
    if text in ("ayuda", "ayuda", "help", "hola", "inicio", "menu", "menú", "start"):
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


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@router.post("/message", response_class=PlainTextResponse)
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Twilio llama este endpoint cuando el dueño manda un mensaje.
    'From' viene como 'whatsapp:+523121234567'
    """
    # Extraer número limpio
    phone = From.replace("whatsapp:", "").strip()

    # Buscar el negocio por número de WhatsApp
    business = (
        db.query(Business)
        .filter(Business.whatsapp_number == phone, Business.is_active == True)
        .first()
    )

    if not business:
        return twiml_response(
            "❌ Tu número no está registrado en Shelfy.\n"
            "Regístrate en shelfy.com para usar el bot."
        )

    # Parsear y ejecutar comando
    cmd = parse_command(Body)
    response_text = handle_command(cmd, business, db)

    return twiml_response(response_text)
