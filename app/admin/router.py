# app/admin/router.py - FIXED (remove email field)
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
import os

router = APIRouter()

# -----------------------------
# SIMPLE AUTH
# -----------------------------
def admin_required(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
    else:
        token = authorization
    
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"email": "admin@ekabhumi.com", "role": "admin"}

# -----------------------------
# CREATE PRODUCT - WITHOUT EMAIL
# -----------------------------
@router.post("/create-product")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    image: UploadFile = File(...),  # REMOVED: email parameter
    db: Session = Depends(get_db),
    admin=Depends(admin_required)
):
    try:
        # Save image file
        UPLOAD_DIR = "uploaded_images"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # Create product WITHOUT email field
        product = Product(
            name=name,
            price=price,
            description=description,
            priority=priority,
            image_url = f"/uploaded_images/{image.filename}"  # Only fields that exist in model
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return {
            "status": "success", 
            "message": "Product created",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
                "priority": product.priority,
                "image_url": product.image_url
            }
        }
        
    except Exception as e:
        print(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

# -----------------------------
# GET ALL PRODUCTS (Admin view)
# -----------------------------
@router.get("/admin-products")
def get_admin_products(db: Session = Depends(get_db), admin=Depends(admin_required)):
    try:
        products = db.query(Product).order_by(Product.priority.asc()).all()
        
        if not products:
            return []
        
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price) if product.price else 0.0,
                "description": product.description or "",
                "image_url": product.image_url or "",
                "priority": product.priority or 100
                # No email field here either
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching admin products: {e}")
        return []

# -----------------------------
# DELETE PRODUCT
# -----------------------------
@router.delete("/delete-product/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(product)
        db.commit()
        
        return {"message": f"Product {product_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

# -----------------------------
# GET ALL ORDERS
# -----------------------------
@router.get("/orders")
def get_admin_orders(db: Session = Depends(get_db), admin=Depends(admin_required)):
    # Return empty array for now
    return []