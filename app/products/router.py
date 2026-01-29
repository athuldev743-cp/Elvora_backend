# app/products/router.py - Return real database products
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product

router = APIRouter()

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    try:
        # Get ALL products from database
        products = db.query(Product).order_by(Product.priority.asc()).all()
        
        if not products:
            # If no products in database, return empty array
            return []
        
        # Convert to list of dicts
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price) if product.price else 0.0,
                "description": product.description or "",
                "image_url": product.image_url or "",
                "priority": product.priority or 100
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []  # Return empty array on error