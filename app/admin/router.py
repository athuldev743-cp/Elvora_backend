# app/admin/router.py - FIXED (remove email field)
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product,Order
import os
from app.cloudinary_setup import upload_to_cloudinary, delete_from_cloudinary
from app.email import send_order_confirmation_email 
from sqlalchemy import text
from fastapi import BackgroundTasks
from typing import Optional

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
     quantity: int = Form(0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_required)
):
    try:
        # Upload image to Cloudinary
        image_url = await upload_to_cloudinary(image, folder="ekabhumi/products")
        
        # Create product with Cloudinary URL
        product = Product(
            name=name,
            price=price,
            description=description,
            priority=priority,
             quantity=quantity,
            image_url=image_url  # Cloudinary URL
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
                 "quantity": product.quantity,
                "image_url": product.image_url
            }
        }
        
    except Exception as e:
        print(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")
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
                "quantity": int(product.quantity or 0),
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
async def delete_product(product_id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete image from Cloudinary if it exists
        if product.image_url and "cloudinary.com" in product.image_url:
         try:
             await delete_from_cloudinary(product.image_url)
         except Exception as e:
       
           print("Cloudinary delete failed:", e)
        
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
# -----------------------------
# GET ALL ORDERS (Admin)
# -----------------------------
@router.get("/orders")
def get_admin_orders(db: Session = Depends(get_db), admin=Depends(admin_required)):
    try:
        orders = db.query(Order).order_by(Order.id.desc()).all()

        result = []
        for o in orders:
            result.append({
                "id": o.id,
                "product_id": o.product_id,
                "product_name": o.product_name,
                "quantity": o.quantity,
                "unit_price": float(o.unit_price),
                "total_amount": float(o.total_amount),
                "customer_name": o.customer_name,
                "customer_email": o.customer_email,
                "customer_phone": o.customer_phone,
                "shipping_address": o.shipping_address,
                "notes": o.notes,
                "status": o.status,
                "payment_status": o.payment_status,
                "order_date": o.order_date.isoformat() if o.order_date else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            })

        return result
    except Exception as e:
     print(f"Error fetching admin products: {e}")
    raise HTTPException(status_code=500, detail="Failed to fetch admin products")



# -----------------------------
# TEMP: RESET ORDERS TABLE (Drops old schema)
# -----------------------------
@router.post("/reset-orders-table")
def reset_orders_table(db: Session = Depends(get_db), admin=Depends(admin_required)):
    """
    WARNING: Deletes ALL orders. Use once to fix schema mismatch on SQLite.
    After successful reset, REMOVE this endpoint.
    """
    db.execute(text("DROP TABLE IF EXISTS orders"))
    db.commit()
    return {"status": "ok", "message": "orders table dropped. Restart service to recreate it."}


@router.post("/orders/{order_id}/approve")
def approve_order(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin=Depends(admin_required)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "confirmed":
        return {"message": "Order already confirmed"}

    order.status = "confirmed"
    order.payment_status = "paid"
    db.commit()
    db.refresh(order)

    # 🔔 Send email in background (non-blocking)
    background_tasks.add_task(
        send_order_confirmation_email,
        to_email=order.customer_email,
        customer_name=order.customer_name,
        order_id=order.id,
        product_name=order.product_name,
        total_amount=order.total_amount,
    )

    return {
        "status": "success",
        "message": "Order approved; email queued",
        "order_id": order.id,
    }





@router.put("/update-product/{product_id}")
async def update_product(
    product_id: int,

    # all optional (update only what is sent)
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    priority: Optional[int] = Form(None),
    quantity: Optional[int] = Form(None),

    # optional image replace
    image: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    admin=Depends(admin_required)
):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # update fields only if provided
        if name is not None:
            product.name = name

        if price is not None:
            product.price = price

        if description is not None:
            product.description = description

        if priority is not None:
            product.priority = priority

        if quantity is not None:
            product.quantity = quantity

        # replace image (optional)
        if image is not None:
            # delete old from cloudinary if it was cloudinary url
            if product.image_url and "cloudinary.com" in product.image_url:
                try:
                    await delete_from_cloudinary(product.image_url)
                except Exception as e:
                    # don't fail update if delete fails
                    print("Cloudinary delete failed:", e)

            new_url = await upload_to_cloudinary(image, folder="ekabhumi/products")
            product.image_url = new_url

        db.commit()
        db.refresh(product)

        return {
            "status": "success",
            "message": "Product updated",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": float(product.price) if product.price else 0.0,
                "description": product.description or "",
                "quantity": int(product.quantity or 0),
                "image_url": product.image_url or "",
                "priority": product.priority or 100,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")
