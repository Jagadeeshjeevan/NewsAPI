from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import news

app = FastAPI(title="DigiNews API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "DigiNews API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}