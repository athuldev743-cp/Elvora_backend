# app/products/router.py - Return real database products
from fastapi import  APIRouter, Depends
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
                "quantity": int(product.quantity or 0),  # ✅ NEW

                "image_url": product.image_url or "",
                "priority": product.priority or 100
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []  # Return empty array on error
    
# Add this to app/products/router.py after the get_products function
@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        # Get single product by ID
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            # Return 404 if product not found
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Return product data
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0.0,
            "description": product.description or "",
            "quantity": int(product.quantity or 0),  # ✅ NEW

            "image_url": product.image_url or "",
            "priority": product.priority or 100
        }
        
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")    