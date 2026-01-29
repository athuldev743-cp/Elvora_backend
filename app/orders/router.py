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

        order = Order(
            product_id=order_data.product_id,
            product_name=order_data.product_name,
            quantity=order_data.quantity,
            unit_price=order_data.unit_price,
            total_amount=order_data.total_amount,
            customer_name=order_data.customer_name,
            customer_email=order_data.customer_email,
            customer_phone=order_data.customer_phone,
            shipping_address=order_data.shipping_address,
            notes=order_data.notes or "",
            status=order_data.status or "pending",
            payment_status=order_data.payment_status or "pending",
            order_date=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        print(f"✅ [Backend] Order created successfully: Order ID {order.id}")
        return order

    except Exception as e:
        db.rollback()
        print(f"❌ [Backend] Error creating order: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Backend] Error fetching order {order_id}: {repr(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch order")
