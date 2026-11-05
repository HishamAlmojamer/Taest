# Production Setup

## Topology

```
Browser
  -> Cloudflare Pages (static React SPA)
  -> Render web service "erp-api" (public HTTPS, port $PORT)
       -> Express gateway (auth, rate limits, security headers, /api proxy)
       -> FastAPI on 127.0.0.1:8001 (business logic, migrations, scheduler)
       -> Neon PostgreSQL (TLS, pooled)
```

One Render container runs both processes. The gateway is the only public
listener; FastAPI is bound to loopback inside the container.

## Startup sequence

`web/start-render.sh` is the container entrypoint and performs:

1. Resolve `GATEWAY_URL` to `http://127.0.0.1:${PORT:-3001}` so backend ledger
   events reach the gateway even when Render assigns a port.
2. Run `alembic upgrade head` from `web/backend`.
3. Start FastAPI with Uvicorn on `127.0.0.1:8001`.
4. Start the SPA-less gateway on `0.0.0.0:${PORT}`.
5. Wait for the gateway process; exit non-zero if it dies.

The backend lifespan additionally waits for the database, ensures the schema,
seeds first-run data idempotently, and starts the scheduler with a PostgreSQL
advisory lock so only one instance runs scheduled jobs. A second instance waits
for the lock instead of duplicating work.

## Required production configuration

Set these in Render (or the provider's secret store), never in Git:

- `ENVIRONMENT=production`
- `DATABASE_URL` — Neon pooled URL with `sslmode=require`
- `JWT_SECRET` — 64 random hex characters, shared by gateway and backend
- `CORS_ORIGINS` — exact Pages origin, comma-separated if more than one
- `BOOTSTRAP_ADMIN_PASSWORD` — strong first-admin password

Recommended:

- `CACHE_ENABLED=false` while there is no Redis instance
- `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=2`, `PG_POOL_MAX=5`
- `ALLOW_PAGES_DEV=true` only until the final Pages URL is known
- `CF_PAGES_PROJECT=erp-frontend`

Both services validate configuration at startup. In production they refuse to
start when:

- `DATABASE_URL` is empty or points at localhost/127.0.0.1/::1;
- `CORS_ORIGINS` is empty or contains `*`;
- the gateway is started with the known insecure default JWT secret.

## First-run bootstrap

Bootstrap is idempotent and only creates missing records:

- company and main branch;
- current fiscal year and 12 monthly periods;
- 114 standard accounts;
- administrator user, only if the `BOOTSTRAP_ADMIN_*` values are present and the
  username does not already exist.

The password is hashed; it is never logged. After the first successful login,
remove `BOOTSTRAP_ADMIN_PASSWORD` from the service environment and redeploy.

## Authentication and authorization

- Access tokens are short-lived JWTs signed with the shared `JWT_SECRET`.
- Refresh tokens are opaque, hashed at rest, rotated on every refresh, and
  revoked on logout. Reuse of a rotated token is rejected.
- The gateway validates token type and forwards identity headers to FastAPI.
- Role checks are enforced server-side; hiding UI controls is not a security
  boundary.
- Failed logins are rate-limited and locked out by the existing auth policy.

## Security checklist

- [ ] TLS only (Render and Pages provide HTTPS automatically).
- [ ] `JWT_SECRET` generated per environment, never the repository default.
- [ ] Neon database password unique and stored only in the provider secret.
- [ ] `CORS_ORIGINS` exact; `ALLOW_PAGES_DEV` disabled after launch.
- [ ] API docs disabled in production (`/docs`, `/redoc`, `/openapi.json`).
- [ ] Security headers enabled by Helmet and Pages `_headers`.
- [ ] No `.env`, tokens, dumps, or local scripts committed.
- [ ] Bootstrap password removed after first login.
- [ ] Database backups verified before real accounting data is entered.

## Health and observability

- `GET /health` on the gateway returns process and dependency status.
- `GET /api/health` is the proxied backend health endpoint.
- Render restarts the container when the health check fails.
- Logs go to the provider's log stream; do not log tokens, passwords, or full
  connection strings.

## Capacity expectations

The free stack is suitable for evaluation, development, and light use only:

- Render free instances sleep after 15 minutes idle and have 512 MB RAM;
- Neon free has a storage/compute allowance and may wake with latency;
- there is no high-availability SLA, no horizontal autoscaling, and no
  persistent local disk.

For real production accounting, move the API to a paid always-on instance and
Neon to a paid plan with a longer restore window.
