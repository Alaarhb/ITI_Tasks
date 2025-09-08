import os
from typing import Dict, List

users_data = {}
projects_data = []
current_user_email = None

USERS_FILE = 'users.txt'
PROJECTS_FILE = 'projects.txt'

def load_data():
    global users_data, projects_data
    
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users_data = {}
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('|')
                        if len(parts) == 7:
                            email = parts[0]
                            users_data[email] = {
                                'first_name': parts[1],
                                'last_name': parts[2],
                                'email': email,
                                'password_hash': parts[3],
                                'mobile': parts[4],
                                'is_active': parts[5].lower() == 'true',
                                'created_at': parts[6]
                            }
        except:
            users_data = {}
    
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                projects_data = []
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('|')
                        if len(parts) == 8:
                            projects_data.append({
                                'title': parts[0],
                                'details': parts[1],
                                'total_target': float(parts[2]),
                                'start_date': parts[3],
                                'end_date': parts[4],
                                'owner_email': parts[5],
                                'created_at': parts[6],
                                'current_amount': float(parts[7])
                            })
        except:
            projects_data = []

def save_data():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        for email, user in users_data.items():
            line = f"{user['email']}|{user['first_name']}|{user['last_name']}|{user['password_hash']}|{user['mobile']}|{user['is_active']}|{user['created_at']}\n"
            f.write(line)
    
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        for project in projects_data:
            line = f"{project['title']}|{project['details']}|{project['total_target']}|{project['start_date']}|{project['end_date']}|{project['owner_email']}|{project['created_at']}|{project['current_amount']}\n"
            f.write(line)

def get_current_user():
    global current_user_email
    if current_user_email and current_user_email in users_data:
        return users_data[current_user_email]
    return None

def set_current_user(email):
    global current_user_email
    current_user_email = email

def clear_current_user():
    global current_user_email
    current_user_email = None