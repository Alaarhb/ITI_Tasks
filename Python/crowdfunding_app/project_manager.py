from datetime import datetime
from validation import validate_date, validate_date_range
import data_storage as storage

def create_project_data(title, details, total_target, start_date, end_date, owner_email):
    return {
        'title': title,
        'details': details,
        'total_target': total_target,
        'start_date': start_date,
        'end_date': end_date,
        'owner_email': owner_email,
        'created_at': datetime.now().isoformat(),
        'current_amount': 0.0
    }

def create_new_project():
    current_user = storage.get_current_user()
    if not current_user:
        print("❌ Please login first!")
        return False
    
    print("\n=== CREATE PROJECT ===")
    
    title = input("Project Title: ").strip()
    if not title:
        print("❌ Title cannot be empty!")
        return False
    
    details = input("Project Details: ").strip()
    if not details:
        print("❌ Details cannot be empty!")
        return False
    
    try:
        total_target = float(input("Total Target (EGP): "))
        if total_target <= 0:
            print("❌ Target must be positive!")
            return False
    except ValueError:
        print("❌ Invalid target amount!")
        return False
    
    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    if not validate_date(start_date):
        print("❌ Invalid start date format!")
        return False
    
    end_date = input("End Date (YYYY-MM-DD): ").strip()
    if not validate_date(end_date):
        print("❌ Invalid end date format!")
        return False
    
    is_valid, error_msg = validate_date_range(start_date, end_date)
    if not is_valid:
        print(f"❌ {error_msg}")
        return False
    
    project = create_project_data(title, details, total_target, start_date, end_date, current_user['email'])
    storage.projects_data.append(project)
    storage.save_data()
    
    print("✅ Project created successfully!")
    return True

def view_all_projects():
    print("\n=== ALL PROJECTS ===")
    
    if not storage.projects_data:
        print("No projects available.")
        return
    
    for i, project in enumerate(storage.projects_data, 1):
        progress = (project['current_amount'] / project['total_target']) * 100
        print(f"\n{i}. {project['title']}")
        print(f"   Owner: {project['owner_email']}")
        print(f"   Details: {project['details']}")
        print(f"   Target: {project['total_target']:,.2f} EGP")
        print(f"   Progress: {project['current_amount']:,.2f} EGP ({progress:.1f}%)")
        print(f"   Duration: {project['start_date']} to {project['end_date']}")

def get_user_projects(email):
    return [p for p in storage.projects_data if p['owner_email'] == email]

def view_my_projects():
    current_user = storage.get_current_user()
    if not current_user:
        print("❌ Please login first!")
        return
    
    print("\n=== MY PROJECTS ===")
    
    my_projects = get_user_projects(current_user['email'])
    
    if not my_projects:
        print("You haven't created any projects yet.")
        return
    
    for i, project in enumerate(my_projects, 1):
        progress = (project['current_amount'] / project['total_target']) * 100
        print(f"\n{i}. {project['title']}")
        print(f"   Details: {project['details']}")
        print(f"   Target: {project['total_target']:,.2f} EGP")
        print(f"   Progress: {project['current_amount']:,.2f} EGP ({progress:.1f}%)")
        print(f"   Duration: {project['start_date']} to {project['end_date']}")

def edit_user_project():
    current_user = storage.get_current_user()
    if not current_user:
        print("❌ Please login first!")
        return False
    
    my_projects = get_user_projects(current_user['email'])
    
    if not my_projects:
        print("❌ You have no projects to edit!")
        return False
    
    print("\n=== EDIT PROJECT ===")
    print("Your projects:")
    for i, project in enumerate(my_projects, 1):
        print(f"{i}. {project['title']}")
    
    try:
        choice = int(input("Select project number to edit: ")) - 1
        if choice < 0 or choice >= len(my_projects):
            print("❌ Invalid selection!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    project = my_projects[choice]
    
    print(f"\nEditing: {project['title']}")
    print("Press Enter to keep current value.")
    
    new_title = input(f"Title ({project['title']}): ").strip()
    if new_title:
        project['title'] = new_title
    
    new_details = input(f"Details ({project['details']}): ").strip()
    if new_details:
        project['details'] = new_details
    
    new_target = input(f"Target ({project['total_target']}): ").strip()
    if new_target:
        try:
            target_value = float(new_target)
            if target_value > 0:
                project['total_target'] = target_value
            else:
                print("⚠️  Invalid target, keeping current value.")
        except ValueError:
            print("⚠️  Invalid target format, keeping current value.")
    
    storage.save_data()
    print("✅ Project updated successfully!")
    return True

def delete_user_project():
    current_user = storage.get_current_user()
    if not current_user:
        print("❌ Please login first!")
        return False
    
    my_projects = get_user_projects(current_user['email'])
    
    if not my_projects:
        print("❌ You have no projects to delete!")
        return False
    
    print("\n=== DELETE PROJECT ===")
    print("Your projects:")
    for i, project in enumerate(my_projects, 1):
        print(f"{i}. {project['title']}")
    
    try:
        choice = int(input("Select project number to delete: ")) - 1
        if choice < 0 or choice >= len(my_projects):
            print("❌ Invalid selection!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    project = my_projects[choice]
    
    confirm = input(f"Are you sure you want to delete '{project['title']}'? (y/N): ").lower()
    if confirm == 'y':
        storage.projects_data.remove(project)
        storage.save_data()
        print("✅ Project deleted successfully!")
        return True
    else:
        print("❌ Deletion cancelled.")
        return False

def search_projects_by_date():
    print("\n=== SEARCH PROJECTS BY DATE ===")
    
    date_str = input("Enter date (YYYY-MM-DD): ").strip()
    if not validate_date(date_str):
        print("❌ Invalid date format!")
        return
    
    search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    matching_projects = []
    for project in storage.projects_data:
        start_date = datetime.strptime(project['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(project['end_date'], '%Y-%m-%d').date()
        
        if start_date <= search_date <= end_date:
            matching_projects.append(project)
    
    if not matching_projects:
        print(f"No projects found running on {date_str}")
        return
    
    print(f"\nProjects running on {date_str}:")
    for i, project in enumerate(matching_projects, 1):
        progress = (project['current_amount'] / project['total_target']) * 100
        print(f"\n{i}. {project['title']}")
        print(f"   Owner: {project['owner_email']}")
        print(f"   Details: {project['details']}")
        print(f"   Target: {project['total_target']:,.2f} EGP")
        print(f"   Progress: {project['current_amount']:,.2f} EGP ({progress:.1f}%)")
        print(f"   Duration: {project['start_date']} to {project['end_date']}")
