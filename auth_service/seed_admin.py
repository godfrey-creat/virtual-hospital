from models import db, Admin
from app import app  # Your Flask app

with app.app_context():
    existing_admin = Admin.query.first()
    if existing_admin:
        print("⚠️ Admin already exists with email:", existing_admin.email)
    else:
        admin = Admin(email='admin-virtual@gmail.com', password='admin-virtual@2025')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")
