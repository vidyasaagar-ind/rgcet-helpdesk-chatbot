from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, chat
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Backend AI API for the RGCET Help Desk Chatbot.",
    version="0.1.0"
)

# Setup CORS to allow standard frontend fetching
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health Operations"])
app.include_router(chat.router, tags=["Chat Operations"])

@app.get("/")
def root():
    return {"message": "Welcome to RGCET Chatbot API. Access /docs for endpoints."}
