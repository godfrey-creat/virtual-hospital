from models import db, User
from werkzeug.security import generate_password_hash
from app import app  # your Flask app

with app.app_context():
    if not User.query.filter_by(role='admin').first():
        hashed_password = generate_password_hash("AdminPassword123")
        admin = User(email='admin@example.com', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("⚠️ Admin already exists.")
