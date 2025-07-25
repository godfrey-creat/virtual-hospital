from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # e.g., 'user', 'doctor', 'admin'
    approved = db.Column(db.Boolean, default=False)  # Default for all users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    doctor_profile = db.relationship(
        'DoctorProfile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Admin(User):
    __mapper_args__ = {'polymorphic_identity': 'admin'}

    def __init__(self, email, password):
        self.email = email
        self.role = 'admin'
        self.approved = True
        self.set_password(password)


class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    license_no = db.Column(db.String(100), nullable=False)
    license_pdf_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='doctor_profile')


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('DoctorProfile', foreign_keys=[doctor_id])


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)  # e.g. active, closed

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
