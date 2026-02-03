# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# IMPORTANT: import models BEFORE create_all so tables are registered
from app import models  # noqa: F401

app = FastAPI()

# Create tables when the app starts (not at import time)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# CORS Configuration
origins = [
    "https://elvora-eta.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.products import router as product_router
from app.orders import router as order_router
from app.admin import router as admin_router
from app.auth import router as auth_router
from app.payment import router as payments_router

# Include routers
app.include_router(product_router)
app.include_router(order_router)
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router, prefix="/auth")
app.include_router(payments_router) 

@app.get("/")
async def root():
    return {"message": "EKB Backend API", "status": "running"}
