from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.admin import router as admin_router
from app.products import router as product_router
from app.orders import router as order_router

app = FastAPI()

# -------------------- CORS --------------------
# This MUST come BEFORE including routers
origins = [
    "https://ekabhumi.vercel.app",
    "http://localhost:3000",  # For React dev server
    "http://localhost:5173",  # For Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Add this line to expose all headers
)

# -------------------- Routers --------------------
# Routers come AFTER CORS middleware
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)