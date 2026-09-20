# Configuración de Auth0 para PrecioInbox

El código está integrado, pero necesita un tenant y credenciales reales de Auth0 antes de ejecutarse.

## 1. Crear la API

En **Applications > APIs > Create API**:

- Name: `PrecioInbox API`
- Identifier: `https://api.precioinbox.com`
- Signing Algorithm: `RS256`

En **Permissions**, agregar:

- `create:categories`

En la configuración de la API:

- Enable RBAC: activado.
- Add Permissions in the Access Token: activado.

El permiso `create:categories` debe asignarse únicamente al rol de superadministrador.

## 2. Crear la aplicación React

En **Applications > Applications > Create Application**:

- Name: `PrecioInbox Web`
- Type: `Single Page Web Application`

Configurar:

### Allowed Callback URLs

```text
http://localhost:5173,https://precioinbox.com
```

### Allowed Logout URLs

```text
http://localhost:5173,https://precioinbox.com
```

### Allowed Web Origins

```text
http://localhost:5173,https://precioinbox.com
```

Si todavía se usa la URL de Cloudflare `workers.dev`, agregarla también en las tres listas.

## 3. Exigir correo verificado

Crear una **Post Login Action** y conectarla al flujo de Login:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  if (!event.user.email_verified) {
    api.access.deny('Verifica tu correo antes de entrar a PrecioInbox.');
  }
};
```

Esto evita que Auth0 emita una sesión utilizable antes de verificar el correo.

## 4. Variables del backend

```dotenv
AUTH0_DOMAIN=tu-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.precioinbox.com
AUTH0_ALGORITHMS=RS256
```

No incluir `https://` dentro de `AUTH0_DOMAIN`.

## 5. Variables del frontend

```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=tu-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=tu-client-id
VITE_AUTH0_AUDIENCE=https://api.precioinbox.com
```

Estas mismas variables deben configurarse en Cloudflare Pages con la URL de producción para la API.

## 6. Base de datos limpia

Esta versión no utiliza Alembic ni conserva compatibilidad con las cuentas locales anteriores. El backend crea automáticamente el esquema nuevo cuando inicia sobre una base vacía.

Antes del despliegue se eliminará exclusivamente el volumen PostgreSQL actual de PrecioInbox. No se debe usar `docker compose down -v`, porque también eliminaría el volumen de imágenes.

Primero se identificará el nombre exacto:

```bash
docker volume ls
```

Después se detendrán los servicios, se eliminará únicamente el volumen de PostgreSQL confirmado y se reconstruirá el backend. Estos pasos se ejecutarán posteriormente en el VPS.

El modelo nuevo de usuario contiene solamente:

```text
id
auth0_subject
```

Auth0 conserva correo, contraseña, verificación y recuperación de cuenta.

## 7. Verificación final

1. Registrar una cuenta desde `/registro`.
2. Confirmar que Auth0 exija verificar el correo.
3. Iniciar sesión y crear un catálogo.
4. Crear, editar y eliminar un producto.
5. Confirmar que otro usuario recibe `404` al intentar administrar ese producto.
6. Confirmar que un producto oculto no aparece ni abre mediante una URL pública.
7. Cerrar sesión y comprobar que las rutas privadas redirigen a Auth0.
