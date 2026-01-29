from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order
from app.schemas import OrderResponse, OrderCreate
from datetime import datetime

router = APIRouter()

# -----------------------------
# PUBLIC ORDER ENDPOINTS ONLY
# -----------------------------
@router.post("/orders", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        print("🔵 [Backend] Received order data:", order_data.dict())
        
        # Convert Pydantic model to dict
        order_dict = order_data.dict()
        
        # Create order instance
        order = Order(
            product_id=order_dict["product_id"],
            product_name=order_dict["product_name"],
            quantity=order_dict["quantity"],
            unit_price=order_dict["unit_price"],
            total_amount=order_dict["total_amount"],
            customer_name=order_dict["customer_name"],
            customer_email=order_dict["customer_email"],
            customer_phone=order_dict["customer_phone"],
            shipping_address=order_dict["shipping_address"],
            notes=order_dict.get("notes", ""),
            status=order_dict.get("status", "pending"),
            payment_status=order_dict.get("payment_status", "pending"),
            order_date=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f"✅ [Backend] Order created successfully: Order ID {order.id}")
        
        return order
        
    except Exception as e:
        print(f"❌ [Backend] Error creating order: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        print(f"❌ [Backend] Error fetching order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch order")