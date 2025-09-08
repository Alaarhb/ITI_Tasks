import hashlib
from datetime import datetime
from validation import validate_email, validate_egyptian_phone, validate_name
import data_storage as storage

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def create_user(first_name, last_name, email, password, mobile):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password_hash': hash_password(password),
        'mobile': mobile,
        'is_active': False,
        'created_at': datetime.now().isoformat()
    }
    return user_data

def register_user():
    print("\n=== REGISTRATION ===")
    
    first_name = input("First Name: ").strip()
    if not validate_name(first_name):
        print("❌ First name must contain only letters and spaces!")
        return False
    
    last_name = input("Last Name: ").strip()
    if not validate_name(last_name):
        print("❌ Last name must contain only letters and spaces!")
        return False
    
    email = input("Email: ").strip().lower()
    if not validate_email(email):
        print("❌ Invalid email format!")
        return False
    if email in storage.users_data:
        print("❌ Email already exists!")
        return False
    
    password = input("Password: ").strip()
    if len(password) < 6:
        print("❌ Password must be at least 6 characters!")
        return False
    
    confirm_password = input("Confirm Password: ").strip()
    if password != confirm_password:
        print("❌ Passwords don't match!")
        return False
    
    mobile = input("Mobile Phone: ").strip()
    if not validate_egyptian_phone(mobile):
        print("❌ Invalid Egyptian phone number format!")
        return False
    
    user = create_user(first_name, last_name, email, password, mobile)
    storage.users_data[email] = user
    storage.save_data()
    
    print("✅ Registration successful!")
    print("⚠️  Account created but not activated. Please activate your account to login.")
    
    activate = input("Activate account now? (y/n): ").lower()
    if activate == 'y':
        storage.users_data[email]['is_active'] = True
        storage.save_data()
        print("✅ Account activated!")
    
    return True

def login_user():
    print("\n=== LOGIN ===")
    
    email = input("Email: ").strip().lower()
    password = input("Password: ").strip()
    
    if email not in storage.users_data:
        print("❌ Email not found!")
        return False
    
    user = storage.users_data[email]
    
    if not user['is_active']:
        print("❌ Account not activated!")
        return False
    
    if not verify_password(user['password_hash'], password):
        print("❌ Invalid password!")
        return False
    
    storage.set_current_user(email)
    print(f"✅ Welcome, {user['first_name']} {user['last_name']}!")
    return True

def logout_user():
    storage.clear_current_user()
    print("✅ Logged out successfully!")
