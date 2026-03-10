from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import questions, sessions
from app.core.database import connect_db, disconnect_db

app = FastAPI(
    title="Adaptive Diagnostic Engine",
    description="1D Adaptive Testing API with IRT-based ability estimation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()


app.include_router(questions.router, prefix="/api", tags=["Questions"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])


@app.get("/")
async def root():
    return {"message": "Adaptive Diagnostic Engine is running 🚀"}
