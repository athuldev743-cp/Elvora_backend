# app/products/router.py - Return real database products
from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from fastapi import HTTPException

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
                "quantity": int(product.quantity or 0),  # ✅ NEW

                "image_url": product.image_url or "",
                "priority": product.priority or 100
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []  # Return empty array on error
 
@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0.0,
            "description": product.description or "",
            "quantity": int(product.quantity or 0),
            "image_url": product.image_url or "",
            "priority": product.priority or 100
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")