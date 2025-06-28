from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.sqlite import JSON
from auth_service.models import db

#db = SQLAlchemy()

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facility_type = db.Column(db.String(50), nullable=False)  # e.g. hospital, pharmacy
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    license_pdf_path = db.Column(db.String(255), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    extra_info = db.Column(JSON, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
