# debug_db.py
try:
    import sqlite3
    print("SQLite imported successfully")
    
    conn = sqlite3.connect("eka_bhumi.db")
    print("Connected to database")
    
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check products table specifically
    print("\nChecking 'products' table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
    products_table = cursor.fetchone()
    
    if products_table:
        print(f"✓ 'products' table exists")
        
        # Get columns
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        
        print(f"\n'products' table has {len(columns)} columns:")
        for col in columns:
            col_id, col_name, col_type, notnull, default_val, pk = col
            print(f"  {col_id}. {col_name} ({col_type})")
    else:
        print("✗ 'products' table does NOT exist")
    
    conn.close()
    print("\nDatabase check complete")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()