from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, VARCHAR
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # ✅ REQUIRED
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, nullable=True)
    role = Column(String, default="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    image_url = Column(VARCHAR)  # Change from String to VARCHAR
    priority = Column(Integer, default=100)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)  # ✅ REQUIRED
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="placed")
