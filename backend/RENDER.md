# Deploy the backend to Render

## Render web service

Configure the existing Render web service with:

- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`

Set these service environment variables in Render:

- `DATABASE_URL`: the production PostgreSQL connection string.
- `JWT_SECRET`: a newly generated, private random secret. Never use a checked-in
  example or development value.
- `FRONTEND_URL`: `https://www.apexiveai.com`. Separate additional allowed
  frontend origins with commas.

Configure optional `SMTP_*`, `DIDIT_*`, and `EMBEDDING_*` variables only when
those features are enabled. Keep all credentials in Render's environment
settings.

## Vercel frontend

Set the Vercel project's **Root Directory** to `frontend`, then configure:

- `NEXT_PUBLIC_API_URL`: `https://international-unstoppable.onrender.com`
- `NEXT_PUBLIC_SITE_URL`: `https://www.apexiveai.com`

Set any other `NEXT_PUBLIC_*` values required by the feature using them, then
redeploy so Next.js includes the values in the frontend build.

## Domain routing

Add `www.apexiveai.com` to the Vercel project and use the DNS records Vercel
shows for that domain. The current DNS screenshot points both `@` and `www` to
`apexiveai-detector.onrender.com`, which sends website traffic to Render rather
than the Vercel frontend. Do not replace those records until confirming whether
the detector service depends on them.

If the API needs a custom domain, add a separate hostname such as
`api.apexiveai.com` to the Render web service and use the exact DNS target Render
provides. Keep the detector's existing `onrender.com` hostname independent.

After deployment, verify that the Render `/health` endpoint returns HTTP 200 and
that `https://www.apexiveai.com` serves the Vercel frontend.
