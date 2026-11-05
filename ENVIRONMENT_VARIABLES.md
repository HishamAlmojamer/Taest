# Environment Variables

Never commit real values. Production secrets belong in the Render dashboard or
another secret manager. `.env.example` files contain placeholders only.

## Backend (FastAPI)

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `ENVIRONMENT` | Production: yes | `development` | Use `production` to enable strict validation. |
| `DATABASE_URL` | Yes | local PostgreSQL | Neon pooled URL with `sslmode=require`. `postgresql://` and `postgresql+asyncpg://` are accepted. |
| `JWT_SECRET` | Yes | none | At least 32 characters; use 64 random hex characters. Must match the gateway. |
| `JWT_ALGORITHM` | No | `HS256` | One of `HS256`, `HS384`, `HS512`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Short-lived access token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime. Tokens are rotated. |
| `CORS_ORIGINS` | Production: yes | local origins | Comma-separated exact origins, no `*` in production. |
| `DB_POOL_SIZE` | No | `20` | Lower to `5` on a 512 MB Render instance. |
| `DB_MAX_OVERFLOW` | No | `10` | Lower to `2` on a small instance. |
| `DB_POOL_TIMEOUT` | No | `30` | Seconds to wait for a connection. |
| `DB_POOL_RECYCLE` | No | `1800` | Recycle connections before pooler/network idle timeouts. |
| `CACHE_ENABLED` | No | `true` | Set `false` when no Redis is available. |
| `REDIS_URL` | No | local Redis | Only used when caching is enabled. |
| `DEBUG` | No | `false` | Must be `false` in production. |
| `APP_NAME` | No | `ERP System` | Display name. |
| `GATEWAY_URL` | No | `http://localhost:3001` | Backend-to-gateway event URL. `start-render.sh` sets it automatically. |
| `BOOTSTRAP_ADMIN_USERNAME` | First run: yes | none | Created only if the user does not exist. |
| `BOOTSTRAP_ADMIN_PASSWORD` | First run: yes | none | Strong password; remove after first login. |
| `BOOTSTRAP_ADMIN_FULL_NAME` | No | `System Administrator` | Display name for the first admin. |
| `BOOTSTRAP_COMPANY_NAME` | No | `HM Next ERP` | Seeded company name. |
| `BOOTSTRAP_BRANCH_NAME` | No | `Main Branch` | Seeded branch name. |

## Gateway (Express)

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `PORT` | Provider sets it | `3001` | Render injects this; do not hardcode. |
| `ENVIRONMENT` / `NODE_ENV` | Production: yes | `development` | Enables strict validation. |
| `DATABASE_URL` | Yes | none in production | Same Neon URL as the backend. |
| `JWT_SECRET` | Yes | none | Must match the backend. |
| `JWT_ALGORITHM` | No | `HS256` | Must match the backend. |
| `PYTHON_BACKEND_URL` | Yes | `http://localhost:8001` | Internal FastAPI URL; keep it on loopback. |
| `CORS_ORIGINS` | Production: yes | local origins | Exact Pages origin(s), comma-separated. |
| `ALLOW_PAGES_DEV` | No | `false` | `true` temporarily allows the configured Pages project and its previews. |
| `CF_PAGES_PROJECT` | No | `erp-frontend` | Pages project name used by `ALLOW_PAGES_DEV`. |
| `PG_POOL_MAX` | No | `10` | Lower to `5` on a small Render instance. |
| `FRONTEND_URL` | No | `http://localhost:5173` | Used by single-service CORS/redirect flows. |
| `SERVE_FRONTEND_DIR` | No | empty | Only for the all-in-one image; leave empty for split deployment. |

## Frontend (Vite / Cloudflare Pages)

| Variable | Required | Notes |
| --- | --- | --- |
| `VITE_API_URL` | Production: yes | Full API base including `/api`, for example `https://erp-api.onrender.com/api`. This is embedded at build time; rebuild after changing it. |
| `NODE_VERSION` | Recommended | `20` for the Cloudflare Pages build image. |

## Local development

`web/backend/.env` and `web/gateway/.env` are local-only and ignored by Git.
Use the development values from `.env.example`. Never reuse the repository's
insecure default JWT secret outside local development.

## Validation rules

Production startup fails when:

- `JWT_SECRET` is missing, shorter than 32 characters, the published default, or
  a placeholder;
- `DEBUG=true`;
- `DATABASE_URL` is empty or points at localhost/127.0.0.1/::1;
- `CORS_ORIGINS` is empty or contains `*`;
- the backend is given a bootstrap username without a password.
