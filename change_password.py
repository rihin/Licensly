from database import SessionLocal
from models import User
from auth import get_password_hash
import sys

def change_password(username, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return

        print(f"Updating password for {username}...")
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print("Password updated successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python change_password.py <username> <new_password>")
        print("Example: python change_password.py support mynewpassword123")
    else:
        change_password(sys.argv[1], sys.argv[2])
