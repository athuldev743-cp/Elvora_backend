from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Configuration
origins = [
    "https://ekabhumi.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Import routers
from app.products import router as product_router
from app.orders import router as order_router
from app.admin import router as admin_router
from app.auth import router as auth_router

# Include routers WITHOUT prefix since they already have full paths
app.include_router(product_router)
app.include_router(order_router)
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router, prefix="/auth")

@app.get("/")
async def root():
    return {"message": "EKB Backend API", "status": "running"}