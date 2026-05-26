"""
Tests para el bot de WhatsApp
Run: pytest tests/test_bot.py -v
"""
from fastapi.testclient import TestClient
from app.main import app
from app.routers.bot import parse_command

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_with_whatsapp(phone="+523121234567"):
    client.post("/auth/register", json={
        "name": "Tacos Mary",
        "email": "mary@test.com",
        "password": "secret123",
        "whatsapp_number": phone,
    })


def send_message(body: str, phone: str = "+523121234567"):
    return client.post("/bot/message", data={
        "From": f"whatsapp:{phone}",
        "Body": body,
    })


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestParser:
    def test_agregar_simple(self):
        cmd = parse_command("agregar Taco 15")
        assert cmd["action"] == "agregar"
        assert cmd["name"] == "Taco"
        assert cmd["price"] == 15.0

    def test_agregar_nombre_compuesto(self):
        cmd = parse_command("agregar Taco de canasta 15.50")
        assert cmd["action"] == "agregar"
        assert cmd["name"] == "Taco De Canasta"
        assert cmd["price"] == 15.50

    def test_agregar_mayusculas(self):
        cmd = parse_command("AGREGAR Agua 10")
        assert cmd["action"] == "agregar"

    def test_agotado(self):
        cmd = parse_command("agotado 2")
        assert cmd["action"] == "agotado"
        assert cmd["product_num"] == 2

    def test_disponible(self):
        cmd = parse_command("disponible 1")
        assert cmd["action"] == "disponible"
        assert cmd["product_num"] == 1

    def test_listar_variantes(self):
        for texto in ["mis productos", "productos", "lista", "listar"]:
            assert parse_command(texto)["action"] == "listar"

    def test_ayuda_variantes(self):
        for texto in ["ayuda", "help", "hola", "start"]:
            assert parse_command(texto)["action"] == "ayuda"

    def test_desconocido(self):
        cmd = parse_command("quiero una pizza")
        assert cmd["action"] == "desconocido"


# ── Webhook Tests ─────────────────────────────────────────────────────────────

class TestWebhook:
    def test_numero_no_registrado(self):
        r = send_message("ayuda", phone="+521111111111")
        assert r.status_code == 200
        assert "no está registrado" in r.text

    def test_ayuda(self):
        register_with_whatsapp()
        r = send_message("ayuda")
        assert r.status_code == 200
        assert "agregar" in r.text.lower()

    def test_agregar_producto(self):
        register_with_whatsapp()
        r = send_message("agregar Taco de canasta 15")
        assert r.status_code == 200
        assert "Taco De Canasta" in r.text
        assert "15.00" in r.text

    def test_listar_productos(self):
        register_with_whatsapp()
        send_message("agregar Taco 15")
        send_message("agregar Agua 10")
        r = send_message("mis productos")
        assert "Taco" in r.text
        assert "Agua" in r.text

    def test_marcar_agotado(self):
        register_with_whatsapp()
        send_message("agregar Taco 15")
        r = send_message("agotado 1")
        assert r.status_code == 200
        assert "agotado" in r.text.lower()

    def test_marcar_disponible(self):
        register_with_whatsapp()
        send_message("agregar Taco 15")
        send_message("agotado 1")
        r = send_message("disponible 1")
        assert "disponible" in r.text.lower()

    def test_numero_invalido(self):
        register_with_whatsapp()
        send_message("agregar Taco 15")
        r = send_message("agotado 99")
        assert "inválido" in r.text or "invalido" in r.text.lower()

    def test_comando_desconocido(self):
        register_with_whatsapp()
        r = send_message("hola quiero una pizza")
        assert "ayuda" in r.text.lower()

    def test_respuesta_es_xml(self):
        register_with_whatsapp()
        r = send_message("ayuda")
        assert "<Response>" in r.text
        assert "<Message>" in r.text
