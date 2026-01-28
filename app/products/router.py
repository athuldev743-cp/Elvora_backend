from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product
from app.dependencies.admin import admin_only

router = APIRouter()

# ADMIN ENDPOINTS
@router.post("/admin")
def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    priority: int = Form(100),
    db: Session = Depends(get_db),
    admin = Depends(admin_only)
):
    product = Product(
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        priority=priority
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/admin")
def get_admin_products(db: Session = Depends(get_db), admin=Depends(admin_only)):
    products = db.query(Product).order_by(Product.priority.asc()).all()
    return products

# ... keep the rest of your endpoints as they were