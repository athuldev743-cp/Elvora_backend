from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Order as OrderModel
from app.schemas import OrderResponse, OrderCreate, OrderUpdate
from app.dependencies.admin import admin_only

router = APIRouter()

# -----------------------------
# ADMIN ENDPOINTS
# -----------------------------
@router.get("/admin", response_model=List[OrderResponse])
def get_all_orders(db: Session = Depends(get_db), admin=Depends(admin_only)):
    orders = db.query(OrderModel).order_by(OrderModel.created_at.desc()).all()
    return orders

@router.put("/admin/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order_update.status:
        order.status = order_update.status
    
    db.commit()
    db.refresh(order)
    return order

@router.delete("/admin/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}

# -----------------------------
# PUBLIC ENDPOINTS
# -----------------------------
@router.post("/", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    order_dict = order_data.model_dump()
    order = OrderModel(**order_dict, status="pending")
    
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order