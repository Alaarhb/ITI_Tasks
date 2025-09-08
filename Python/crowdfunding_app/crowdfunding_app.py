import data_storage as storage
from user_auth import register_user, login_user, logout_user
from project_manager import (
    create_new_project, view_all_projects, view_my_projects,
    edit_user_project, delete_user_project, search_projects_by_date
)

def show_guest_menu():
    print("\n=== MAIN MENU ===")
    print("1. Register")
    print("2. Login")
    print("3. View All Projects")
    print("4. Search Projects by Date")
    print("0. Exit")

def show_user_menu():
    current_user = storage.get_current_user()
    print(f"\n=== USER MENU ({current_user['first_name']}) ===")
    print("1. Create Project")
    print("2. View All Projects")
    print("3. View My Projects")
    print("4. Edit My Project")
    print("5. Delete My Project")
    print("6. Search Projects by Date")
    print("7. Logout")
    print("0. Exit")

def handle_guest_menu(choice):
    if choice == '1':
        register_user()
    elif choice == '2':
        login_user()
    elif choice == '3':
        view_all_projects()
    elif choice == '4':
        search_projects_by_date()
    elif choice == '0':
        return False
    else:
        print("❌ Invalid option!")
    return True

def handle_user_menu(choice):
    if choice == '1':
        create_new_project()
    elif choice == '2':
        view_all_projects()
    elif choice == '3':
        view_my_projects()
    elif choice == '4':
        edit_user_project()
    elif choice == '5':
        delete_user_project()
    elif choice == '6':
        search_projects_by_date()
    elif choice == '7':
        logout_user()
    elif choice == '0':
        return False
    else:
        print("❌ Invalid option!")
    return True

def main():
    # Initialize data
    storage.load_data()
    
    print("🎉 Welcome to the Crowdfunding Platform!")
    
    while True:
        current_user = storage.get_current_user()
        
        if not current_user:
            show_guest_menu()
            choice = input("\nSelect option: ").strip()
            if not handle_guest_menu(choice):
                break
        else:
            show_user_menu()
            choice = input("\nSelect option: ").strip()
            if not handle_user_menu(choice):
                break
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()