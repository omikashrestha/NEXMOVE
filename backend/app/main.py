from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.session import engine, Base
from backend.app.api.projects import router as projects_router
from backend.app.api.documents import router as documents_router
from backend.app.api.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables automatically
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="NEXMOVE Multi-Agent Relocation API",
    description="Backend API Gateway coordinating autonomous LangGraph agents and n8n orchestration for relocation planning.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Next.js dashboard (port 3000) and n8n (port 5678)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for university prototype testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(webhooks_router)


@app.get("/", tags=["Health"])
def root_endpoint():
    return {
        "service": "NEXMOVE Multi-Agent Relocation Assistant",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "database": "sqlite_connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
