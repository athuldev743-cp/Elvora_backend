# app/products/router.py - Return real database products
from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from fastapi import HTTPException

router = APIRouter()

# app/products/router.py
# ... imports ...

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).order_by(Product.priority.asc()).all()
        if not products: return []
        
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price) if product.price else 0.0,
                "description": product.description or "",
                "quantity": int(product.quantity or 0),
                "image_url": product.image_url or "",
                
                # ✅ NEW: Include image2_url
                "image2_url": product.image2_url or "",
                
                "priority": product.priority or 100
            })
        return result
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product: raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0.0,
            "description": product.description or "",
            "quantity": int(product.quantity or 0),
            "image_url": product.image_url or "",
            
            # ✅ NEW: Include image2_url
            "image2_url": product.image2_url or "",
            
            "priority": product.priority or 100
        }
    except HTTPException: raise
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
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