# Deploy the backend to Railway

1. Create a Railway project from this GitHub repository and add a PostgreSQL
   service.
2. Create a service for the repository and set its **Root Directory** to
   `/backend`. Railway will read `railway.toml` from that directory.
3. In the backend service variables, set:
   - `DATABASE_URL` to the PostgreSQL service's `DATABASE_URL` reference.
   - `JWT_SECRET` to a new, randomly generated secret. Do not use the development
     default.
   - `FRONTEND_URL` to the deployed frontend's origin, such as
     `https://your-app.example.com` (no path or trailing slash).
4. Deploy. The start command applies pending Alembic migrations before starting
   Uvicorn. Railway supplies `PORT`, and the service checks `/health`.
5. In the frontend hosting service, set `NEXT_PUBLIC_API_URL` to the public
   Railway backend origin, such as `https://your-api.example.com`, then rebuild
   the frontend. Keep `FRONTEND_URL` on the backend set to that same frontend
   origin so browser requests pass CORS.

Keep the PostgreSQL service attached to the Railway project so its database URL
is available to the backend service. Seed initial content separately when
needed; table changes are managed by Alembic migrations.

Add optional variables only for features you use, such as `DIDIT_API_KEY`,
`DIDIT_WORKFLOW_ID`, `DIDIT_CALLBACK_URL`, or the `SMTP_*` settings. Store
credentials only in Railway's service variables, never in source control.

**Credential rotation:** a Didit API key was present in the repository README.
Replace/revoke that key in Didit before deploying and configure its replacement
only as a Railway variable.
