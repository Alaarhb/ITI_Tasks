import re
from datetime import datetime

def validate_egyptian_phone(phone):
    patterns = [
        r'^(\+20|0020|20)?01[0125][0-9]{8}$',  # Mobile numbers
        r'^(\+20|0020|20)?02[0-9]{8}$'          # Landline numbers
    ]
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    return any(re.match(pattern, phone) for pattern in patterns)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_name(name):
    if not name or not name.strip():
        return False
   
    return all(char.isalpha() or char.isspace() for char in name.strip()) and name.strip()

def validate_date_range(start_date, end_date):
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt >= end_dt:
            return False, "End date must be after start date!"
        
        if start_dt < datetime.now():
            return False, "Start date cannot be in the past!"
        
        return True, ""
    except:
        return False, "Invalid date format!"