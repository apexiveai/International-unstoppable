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
- `RPA_LICENSE_SERVICE_TOKEN`: a high-entropy private secret shared only with
  the RPA backend. Configure the identical value as `LICENSE_SERVICE_TOKEN`
  there; do not expose it to the browser.
- `FRONTEND_URL`:
  `https://www.apexiveai.com,https://trademark.apexiveai.com,https://apexiveai-detector-v1-1.vercel.app`.
  Separate allowed frontend origins with commas so the Next.js site and both
  Vite Detector hostnames can call the API.

Configure optional `SMTP_*`, `DIDIT_*`, and `EMBEDDING_*` variables only when
those features are enabled. Keep all credentials in Render's environment
settings.

## Vercel frontend

Set the Vercel project's **Root Directory** to `frontend`, then configure:

- `NEXT_PUBLIC_API_URL`: `https://international-unstoppable.onrender.com`
- `NEXT_PUBLIC_SITE_URL`: `https://www.apexiveai.com`
- `NEXT_PUBLIC_TRADEMARK_DETECTOR_URL`:
  `https://apexiveai-detector-v1-1.vercel.app` (the Vite deployment).

Set any other `NEXT_PUBLIC_*` values required by the feature using them, then
redeploy so Next.js includes the values in the frontend build.

Configure the Vite Detector deployment's `APEXIVE_API_URL` to
`https://international-unstoppable.onrender.com`. The custom domain is
currently returning a Railway 404; use the Vercel deployment URL until DNS and
domain routing for `trademark.apexiveai.com` are corrected.

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
