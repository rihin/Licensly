from database import engine, Base, SessionLocal
from models import User, LicenseRequest
from auth import get_password_hash
from sqlalchemy import text

def reset_database():
    print("Resetting database...")
    
    # Create tables (drops first if we want, or just drop all)
    # Easiest is to drop all tables and recreate
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped.")
    
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
    
    db = SessionLocal()
    
    # Seed Users
    users = [
        {"username": "support", "role": "support", "password": "password"},
        {"username": "accounts", "role": "accounts", "password": "password"},
        {"username": "license", "role": "license", "password": "password"},
    ]
    
    print("Seeding users...")
    for u in users:
        user = User(
            username=u["username"],
            role=u["role"],
            hashed_password=get_password_hash(u["password"])
        )
        db.add(user)
    
    db.commit()
    print("Users seeded successfully.")
    
    db.close()
    print("Database reset complete.")

if __name__ == "__main__":
    reset_database()
