"""
Seed admin user script.
Creates an admin user if one doesn't already exist.
"""
import os
import sys
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base
from models.user_model import User
from models.role_model import Role
from db import engine, get_db_context

def seed_admin():
    """Create admin user if it doesn't exist"""
    # Initialize database tables
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")
    
    # Get admin credentials from environment
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_phone = os.getenv("ADMIN_PHONE", "")
    admin_first_name = os.getenv("ADMIN_FIRST_NAME", "Admin")
    admin_last_name = os.getenv("ADMIN_LAST_NAME", "User")
    
    if not admin_password:
        print("WARNING: ADMIN_PASSWORD not set. Admin user will be created without password.")
    
    # Check if admin already exists
    with get_db_context() as db:
        from models.database import UserDB
        
        # Check by email
        existing_admin = db.query(UserDB).filter(
            (UserDB.email == admin_email) | (UserDB.role == Role.ADMIN.value)
        ).first()
        
        if existing_admin:
            print(f"Admin user already exists with email: {existing_admin.email}")
            print(f"Admin user ID: {existing_admin.unique_id}")
            return
        
        # Create admin user
        print(f"Creating admin user with email: {admin_email}")
        admin_user = User(
            first_name=admin_first_name,
            last_name=admin_last_name,
            email=admin_email,
            phone_number=admin_phone,
            is_admin=True,
            credits=0
        )
        
        admin_user.save(db)
        print(f"Admin user created successfully!")
        print(f"Admin user ID: {admin_user.unique_id}")
        print(f"Admin email: {admin_user.email}")
        print(f"Admin role: {admin_user.role.value}")

if __name__ == "__main__":
    try:
        seed_admin()
    except Exception as e:
        print(f"Error seeding admin user: {str(e)}")
        sys.exit(1)

