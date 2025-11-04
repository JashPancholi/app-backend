from models.database import Base
from db import engine
import sys

def init_database():
    """
    Initialize the database by creating all tables.
    This will create tables if they don't exist, but won't modify existing tables.
    """
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        return True
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        return False

def drop_all_tables():
    """
    Drop all tables. Use with caution!
    """
    try:
        print("WARNING: Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped successfully!")
        return True
    except Exception as e:
        print(f"Error dropping tables: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            drop_all_tables()
            init_database()
        else:
            print("Operation cancelled.")
    else:
        init_database()
