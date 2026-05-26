# 📦 Catalog API

API REST para catálogos de negocios locales. Los dueños actualizan su catálogo vía WhatsApp bot; los clientes ven un catálogo público limpio y compartible.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · JWT Auth · Docker

---

## Flujo del producto

```
Dueño → WhatsApp Bot → POST /products/  →  DB
Cliente → /catalog/{slug}               ←  DB
```

---

## Arranque rápido

```bash
# 1. Clonar y entrar
git clone https://github.com/tuusuario/catalog-api
cd catalog-api

# 2. Variables de entorno
cp .env.example .env
# Edita .env con tus credenciales

# 3. Docker (recomendado)
docker compose up --build

# 4. Sin Docker
pip install -r requirements.txt
uvicorn app.main:app --reload

# API disponible en: http://localhost:8000
# Docs interactivos: http://localhost:8000/docs
```

---

## Tests

```bash
pip install pytest httpx
pytest tests/ -v

# Output esperado:
# tests/test_catalog.py::TestAuth::test_register_creates_business PASSED
# tests/test_catalog.py::TestAuth::test_login_returns_token PASSED
# tests/test_catalog.py::TestProducts::test_toggle_availability PASSED
# ... 14 tests total
```

---

## Endpoints

### 🔓 Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/catalog/{slug}` | Catálogo público del negocio |
| GET | `/catalog/{slug}/products` | Productos con filtros |
| GET | `/health` | Health check |

**Filtros disponibles:**
```
/catalog/tacos-mary/products?available_only=true
/catalog/tacos-mary/products?category=bebidas
```

### 🔐 Autenticados (Bearer Token)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/register` | Registrar negocio |
| POST | `/auth/login` | Login → JWT token |
| GET | `/products/mine` | Mis productos |
| POST | `/products/` | Crear producto |
| PUT | `/products/{id}` | Actualizar producto |
| PATCH | `/products/{id}/toggle` | Cambiar disponibilidad |
| DELETE | `/products/{id}` | Eliminar producto |

---

## Ejemplo de uso

```bash
# 1. Registrar negocio
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Tacos Mary","email":"mary@tacos.com","password":"secret123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=mary@tacos.com&password=secret123"
# → {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Crear producto
curl -X POST http://localhost:8000/products/ \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"name":"Taco de Canasta","price":"15.00","category":"tacos"}'

# 4. Ver catálogo público
curl http://localhost:8000/catalog/tacos-mary
```

---

## Deploy gratuito / barato

### Opción A — Railway (⭐ recomendado para portfolio)
```
1. railway.app → New Project → Deploy from GitHub
2. Add Plugin → PostgreSQL (automático)
3. Variables: DATABASE_URL (se llena sola), SECRET_KEY
4. Dominio gratis: tuapp.railway.app
Precio: Free tier 5$/mes créditos incluidos
```

### Opción B — Render
```
1. render.com → New Web Service → GitHub repo
2. New PostgreSQL (free 90 días, luego $7/mes)
3. Variables de entorno en dashboard
Precio: Free tier disponible
```

### Opción C — Fly.io
```
fly launch
fly postgres create
fly secrets set DATABASE_URL=... SECRET_KEY=...
fly deploy
Precio: Free tier generoso (3 VMs pequeñas)
```

### Opción D — AWS (para el CV de AWS)
```
- ECS Fargate (contenedor) + RDS PostgreSQL
- O Lambda + Aurora Serverless (más barato en reposo)
- Costo estimado: ~$15-25/mes mínimo
- Valor en CV: alto si mencionas arquitectura
```

### Base de datos gratuita standalone
```
- Supabase: PostgreSQL gratis con 500MB
- Neon: PostgreSQL serverless, free tier generoso
- Ambas dan DATABASE_URL lista para usar
```

---

## Roadmap

- [ ] WhatsApp bot (Twilio / Meta Cloud API)
- [ ] Subida de imágenes (S3 / Cloudinary)
- [ ] Panel admin web (React o HTMX)
- [ ] Alembic migrations
- [ ] Rate limiting por negocio
- [ ] Dominio personalizado por slug

---

## Arquitectura

```
┌─────────────────────────────────────┐
│           FastAPI App               │
│  /auth  /products  /catalog         │
└──────────────┬──────────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼──────────────────────┐
│         PostgreSQL                  │
│   businesses  │  products           │
└─────────────────────────────────────┘

Futuro:
WhatsApp → Webhook → /bot/message → parser → /products/
```
