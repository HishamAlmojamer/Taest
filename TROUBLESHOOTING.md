# Troubleshooting

## First checks

```bash
curl -i https://<api-service>.onrender.com/health
curl -i https://<api-service>.onrender.com/api/health
curl -I https://<project>.pages.dev
```

Read the Render logs from the top of the latest deploy. Most startup failures
are configuration validation errors, not code errors.

## API returns 502 or times out

- Render free instances sleep; the first request can take 30-90 seconds.
- Open `/health` directly and wait for the cold start.
- Check that the gateway process is still running; `start-render.sh` exits if it
  dies.
- Check that the service port is `$PORT`, not a hardcoded `3001`.
- If memory is exhausted, lower `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` and
  `PG_POOL_MAX`.

## Health check fails with 503

The `/health` response reports dependency state. Common causes:

- `DATABASE_URL` is wrong, expired, or missing `sslmode=require`;
- Neon is waking or the compute quota is exhausted;
- migrations failed at startup;
- the gateway cannot reach FastAPI on `127.0.0.1:8001`.

Run `alembic current` and inspect the first traceback in the Render log.

## Startup exception: DATABASE_URL must point to a managed host

Production validation rejects localhost/127.0.0.1/::1. Paste the Neon pooled
URL into Render's secret environment; do not use the local development URL.

## Startup exception: CORS_ORIGINS must be set / cannot contain '*'

Set the exact Cloudflare Pages origin, for example:

```text
CORS_ORIGINS=https://erp-frontend.pages.dev
```

Multiple origins are comma-separated. Do not use `*` in production.

## Startup exception: JWT_SECRET is the insecure default

The repository contains a published development secret that both services
reject in production. Generate a unique value, for example:

```bash
openssl rand -hex 32
```

Set the same value for the gateway and backend, then redeploy.

## Login works locally but fails on the public site

- Confirm `VITE_API_URL` was set **before** the Pages build and includes `/api`.
- Rebuild the Pages deployment after changing it.
- Check the browser network tab for CORS errors.
- Confirm the Pages origin is in `CORS_ORIGINS`.
- While the final URL is unknown, `ALLOW_PAGES_DEV=true` permits only the
  configured `CF_PAGES_PROJECT` production and preview origins.
- Check the response status: `401` is credentials, `403` is permission, `429` is
  rate limiting/lockout, and a CORS failure usually appears as a network error.

## Refresh on a client route returns 404

Cloudflare Pages needs SPA fallback. Confirm `web/frontend/public/_redirects`
was built into `dist`:

```text
/*    /index.html   200
```

If it is missing, check the Pages build output directory is `dist` and redeploy.

## Neon error: prepared statement already exists / cached plan

The app disables asyncpg's statement cache when the host contains `-pooler`.
Use the pooled URL, not a manually edited host. If the error persists, verify
`DATABASE_URL` actually contains `-pooler` and restart the service.

## Neon error: SSL is required

Append `sslmode=require` to `DATABASE_URL`. The backend converts it to an
asyncpg SSL context.

## Migrations fail on startup

- Read the first Alembic error, not only the final "Application startup failed".
- Confirm the database role can create tables, indexes, and constraints.
- Confirm `alembic_version` matches the repository baseline.
- Do not edit an applied migration; add a new revision.
- If a deploy is stuck, roll back to the previous Render deploy, fix forward,
  and redeploy. Do not drop the database.

## Administrator cannot log in

- Confirm the bootstrap variables were present on the **first** successful
  startup. Bootstrap only creates a missing user; it does not reset passwords.
- Wait out the login lockout if there were repeated failures.
- Use the password exactly as stored in Render; avoid trailing spaces.
- Remove `BOOTSTRAP_ADMIN_PASSWORD` only after confirming the login works.

## Cloudflare Pages build fails

- Node version must be 20 or newer; set `NODE_VERSION=20`.
- Root directory must be `web/frontend`.
- Use `npm ci && npm run build`; the lockfile must be committed.
- Confirm the build output is `dist`.
- A missing `VITE_API_URL` does not fail the build, but the deployed app cannot
  reach the API.

## CORS preflight succeeds but the request fails

The browser sends the real request after `OPTIONS`. Check:

- `Authorization` is in the allowed headers;
- the token is not expired and has the expected type;
- the API URL uses the same host and scheme as configured;
- cookies are not required (the app uses bearer tokens).

## Free-tier limits

- Render free: 512 MB RAM, sleeps after 15 minutes idle, no persistent disk.
- Neon free: limited storage and compute; check the console for the current
  allowance and restore window.
- Cloudflare Pages: static hosting and builds within the free limits.

If the service is suspended for bandwidth or hours, wait for the reset or move
to a paid instance. A paid plan is required for always-on production use.

## Local Docker

If `docker` cannot connect to the daemon on Windows:

- start Docker Desktop and wait for "Engine running";
- verify with `docker version`;
- `com.docker.service` can require administrator privileges to start.

The API image was not built locally when the daemon was unavailable; Render
builds `web/Dockerfile.api` on deploy.

## Tests

Backend tests require live PostgreSQL, FastAPI on `127.0.0.1:8001`, and the
gateway on `127.0.0.1:3001`. The full suite is slow because several accounting
scenarios perform real database work; it can exceed 10 minutes. Run it in
batches if a single command times out:

```bash
cd web/backend
.venv/Scripts/python.exe -m pytest -q tests/test_accounting_integrity.py
.venv/Scripts/python.exe -m pytest -q tests/test_vouchers.py tests/test_journal_entries.py
.venv/Scripts/python.exe -m pytest -q tests/test_phase1_fixes.py tests/test_cheques.py
.venv/Scripts/python.exe -m pytest -q tests/test_ledger_integrity.py
.venv/Scripts/python.exe -m pytest -q tests/test_accounting_scenarios.py tests/test_accounting_units.py tests/test_chart_of_accounts.py tests/test_integration_flows.py
```
