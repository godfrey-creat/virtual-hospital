from auth_service.models import db, User
from werkzeug.security import generate_password_hash
from app import app  # Adjusted import for Flask app

with app.app_context():
    if not User.query.filter_by(email='admin-virtual@gmail.com', role='admin').first():
        hashed_password = generate_password_hash("admin-virtual@2025")
        admin = User(email='admin-virtual@gmail.com', password_hash=hashed_password, role='admin', approved=True)
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("⚠️ Admin already exists.")