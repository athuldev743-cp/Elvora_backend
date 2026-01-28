from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.admin import router as admin_router
from app.products import router as product_router
from app.orders import router as order_router

app = FastAPI()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
# -------------------- CORS --------------------
origins = [
    "https://ekabhumi.vercel.app/",
    # you can add more URLs if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # allow frontend URL
    allow_credentials=True,
    allow_methods=["*"],         # allow all methods
    allow_headers=["*"],         # allow all headers
)

# -------------------- Routers --------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
