# create_tables.py
from app.database import Base, engine
from app.models import User, Product, Order  # Make sure Product is imported

print("Dropping and recreating tables...")
Base.metadata.drop_all(bind=engine)  # This drops all tables
Base.metadata.create_all(bind=engine)  # This recreates them with current schema
print("Tables updated successfully!")