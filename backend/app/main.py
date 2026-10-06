from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.api.auth import router as auth_router
from app.api.didit import router as didit_router
from app.api.categories import router as categories_router
from app.api.threads import router as threads_router
from app.api.replies import router as replies_router
from app.api.article import router as article_router
from app.api.projects import router as projects_router
from app.api.resources import router as resources_router
from app.api.clone_detector import router as clone_detector_router
from app.api import chatbot
from app.api.tenant import router as tenant_router
from app.api.project_engagement import router as project_engagement_router
from app.api.search import router as search_router
from app.api.phase1 import router as phase_one_router
from app.api.executions import router as executions_router
from app.api.admin import router as admin_router
from app.api.client_management import router as client_management_router
from app.api import payments
from app.api.subscriptions import router as subscriptions_router
from app.api.client_products import router as client_products_router


api = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


api.include_router(chatbot.router)
api.include_router(auth_router)
api.include_router(didit_router)
api.include_router(categories_router)
api.include_router(threads_router)
api.include_router(replies_router)
api.include_router(article_router)
api.include_router(projects_router)
api.include_router(resources_router)
api.include_router(clone_detector_router)
api.include_router(phase_one_router)

# Register only once
api.include_router(
    executions_router,
    prefix="/api",
)

api.include_router(admin_router)
api.include_router(client_management_router)
api.include_router(tenant_router)
api.include_router(project_engagement_router)
api.include_router(search_router)
api.include_router(payments.router)
api.include_router(subscriptions_router)
api.include_router(client_products_router)

@api.get("/health")
def health():
    return {
        "status": "ok",
        "service": "apexive-community-api",
    }


app = CORSMiddleware(
    app=api,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    + [
        origin.strip().rstrip("/")
        for origin in settings.frontend_url.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)