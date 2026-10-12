from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.session import engine, Base
from backend.app.api.projects import router as projects_router
from backend.app.api.documents import router as documents_router
from backend.app.api.webhooks import router as webhooks_router
from backend.app.api.places import router as places_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables automatically
    Base.metadata.create_all(bind=engine)
    # Check and add columns if table was created previously without them
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(relocation_projects);")).fetchall()]
            if "target_workplace" not in cols:
                conn.execute(text("ALTER TABLE relocation_projects ADD COLUMN target_workplace VARCHAR(200) DEFAULT 'City Center';"))
            if "max_commute_mins" not in cols:
                conn.execute(text("ALTER TABLE relocation_projects ADD COLUMN max_commute_mins INTEGER DEFAULT 45;"))
            if "selected_property_id" not in cols:
                conn.execute(text("ALTER TABLE relocation_projects ADD COLUMN selected_property_id VARCHAR(50);"))
            conn.commit()
    except Exception:
        pass
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
app.include_router(places_router)


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
