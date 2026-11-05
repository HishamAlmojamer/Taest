# Deployment Guide

Status: **code prepared and locally verified; cloud deployment PENDING account authorization.**

This project is deployed as a split three-tier stack:

| Tier | Provider | Free plan | Status |
| --- | --- | --- | --- |
| Frontend (React/Vite) | Cloudflare Pages | Free, no credit card | PENDING |
| Gateway + FastAPI | Render (single Docker web service) | Free, no credit card | PENDING |
| PostgreSQL | Neon | Free, no credit card | PENDING |

The existing `web/Dockerfile.render` (frontend + API in one image) and
`web/Dockerfile` (gateway + SPA) remain available for a single-service
deployment. The split deployment intentionally uses `web/Dockerfile.api`, which
does **not** build or serve the SPA.

## 1. Create the Neon database

1. Sign in at <https://console.neon.tech> and create a project.
2. Recommended region: `eu-central-1` (Frankfurt), close to the Render service.
3. Keep the default database (`neondb`) and role, or create a dedicated role.
4. Copy a connection string from **Connect**:
   - Prefer the **Pooled connection** endpoint (host contains `-pooler`).
   - The URL must include `sslmode=require`.
5. Do not paste the URL into source files, chat, or Git. Put it only in the
   hosting provider's secret environment settings.

The backend automatically:

- accepts `postgresql://` and `postgresql+asyncpg://`;
- converts `sslmode` to an asyncpg SSL argument;
- removes libpq-only parameters such as `channel_binding`;
- disables asyncpg's prepared-statement cache for `-pooler` hosts.

## 2. Deploy the API on Render

1. Open the Blueprint link:
   <https://render.com/deploy?repo=https://github.com/HishamAlmojamer/Taest>
2. Authorize GitHub access for the repository.
3. Fill the prompted values:
   - `DATABASE_URL`: the Neon pooled connection string.
   - `BOOTSTRAP_ADMIN_PASSWORD`: a strong first-admin password.
4. Keep `ALLOW_PAGES_DEV=true` until the Cloudflare Pages URL is final.
5. Deploy. The service is named `erp-api` and exposes:
   - health: `https://<api-service>.onrender.com/health`
   - API: `https://<api-service>.onrender.com/api`
6. Wait for the health check to pass. On a free instance the first request after
   idle can take about a minute (cold start).
7. Copy the real service URL. If `erp-api` is already taken, Render appends a
   suffix; use the URL shown in the dashboard.

Render free-tier limits (official docs, verified November 2026): 512 MB RAM,
0.1 CPU, 750 instance hours per workspace per month, spin-down after 15 minutes
idle, ephemeral filesystem, no persistent disk. No credit card is required.
Render's docs also state that free instances are not intended for production
workloads; this deployment accepts that limitation.

## 3. Deploy the frontend on Cloudflare Pages

1. Open **Cloudflare Dashboard > Workers & Pages > Create > Pages >
   Connect to Git**.
2. Select the `HishamAlmojamer/Taest` repository and the `main` branch.
3. Build settings:
   - Framework preset: `Vite`
   - Root directory: `web/frontend`
   - Build command: `npm ci && npm run build`
   - Build output directory: `dist`
   - Node version: `20` (environment variable `NODE_VERSION=20`)
4. Add the production environment variable:
   - `VITE_API_URL=https://<api-service>.onrender.com/api`
5. Deploy. Copy the generated URL (`https://<project>.pages.dev`).
6. `web/frontend/public/_redirects` provides SPA fallback for client-side
   routes, and `_headers` adds basic security and asset-cache headers.

`VITE_API_URL` is a **build-time** variable. Changing it requires a new Pages
deployment.

## 4. Lock down CORS

After the Pages URL is known:

1. In Render, set `CORS_ORIGINS` to the exact Pages origin, for example
   `https://erp-frontend.pages.dev`.
2. Set `ALLOW_PAGES_DEV=false` once the final URL is stable.
3. Optional: keep `CF_PAGES_PROJECT=erp-frontend`; while
   `ALLOW_PAGES_DEV=true`, only that project's production and preview origins
   are accepted.

The gateway refuses wildcard CORS in production.

## 5. Verify the deployment

```bash
curl -fsS https://<api-service>.onrender.com/health
curl -fsS -I https://<project>.pages.dev
```

Then open the Pages URL, log in with the bootstrapped administrator, and check:

- dashboard loads;
- chart of accounts loads;
- trial balance is balanced;
- create a test journal entry, then void it;
- log out, refresh the page, and confirm the session is gone.

Do not treat the deployment as complete until these checks pass against the
public HTTPS URLs.

## 6. Updates

- Push to `main`: Render (`autoDeploy: true`) and Cloudflare Pages rebuild
  automatically.
- Database migrations run at API container startup via `alembic upgrade head`.
- A failed Render deploy leaves the previous live version running; roll back to
  the previous deploy in the dashboard if needed.
- Cloudflare Pages keeps previous deployments and supports instant rollback.
- Never run destructive migrations or reset the Neon database.

## 7. Alternative API hosts

Render was selected because it offers a real free Docker web service without a
credit card. Verified alternatives if Render is unavailable:

- **SnapDeploy** — free 512 MB containers, 100 running hours/month, no card;
  sleeps after 15 minutes.
- **Deployxa** — free 512 MB / 3 projects, no card (vendor claim).
- **Bonto** — Node-only free tier, not suitable for the Python backend.

Koyeb and Fly.io require a card. Railway's free allowance is a trial credit,
not a durable free tier. Hugging Face Docker Spaces require a paid PRO plan.
