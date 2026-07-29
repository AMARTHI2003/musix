from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes.auth_routes import router as auth_router
from routes.song_routes import router as song_router
from routes.playlist_routes import router as playlist_router

app = FastAPI(
    title="Harmony Music API",
    description="Backend API for the Harmony Music streaming application",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_router)
app.include_router(song_router)
app.include_router(playlist_router)


@app.on_event("startup")
async def startup_event():
    await init_db()
    print("[OK] Harmony Music API started successfully!")
    print("[DOCS] API Docs: http://localhost:8000/docs")


@app.get("/")
async def root():
    return {
        "app": "Harmony Music",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
