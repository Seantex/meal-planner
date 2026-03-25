"""
Einmalig ausführen um den Admin-Account zu erstellen.
Usage: python3 create_admin.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
import database as db

EMAIL    = "admin@mealplanner.at"
NAME     = "Admin"
PASSWORD = "MealAdmin2024!"   # Bitte nach dem ersten Login ändern

def main():
    db.init_db()

    if db.email_exists(EMAIL):
        print(f"Admin '{EMAIL}' existiert bereits.")
        return

    pw_hash = generate_password_hash(PASSWORD, method="pbkdf2:sha256")
    user_id = db.create_user(EMAIL, NAME, pw_hash, is_admin=True)
    print(f"Admin-Account erstellt:")
    print(f"  E-Mail:   {EMAIL}")
    print(f"  Passwort: {PASSWORD}")
    print(f"  User-ID:  {user_id}")
    print()
    print("WICHTIG: Bitte nach dem ersten Login das Passwort ändern!")

if __name__ == "__main__":
    main()
