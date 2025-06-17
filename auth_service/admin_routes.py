from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, DoctorProfile, Appointment, Department
from .utils import admin_required
import datetime

admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/admin/register', methods=['POST'])
def admin_register():
    if User.query.filter_by(role='admin').first():
        return jsonify({"error": "Admin already exists"}), 403

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    hashed_password = generate_password_hash(password)
    new_admin = User(email=email, password_hash=hashed_password, role="admin", approved=True)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "Admin account created"}), 201

@admin_routes.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    admin = User.query.filter_by(email=email, role='admin').first()
    if not admin or not check_password_hash(admin.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=email, expires_delta=datetime.timedelta(hours=3))
    return jsonify({"access_token": token}), 200

@admin_routes.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required
def list_all_users():
    users = User.query.filter(User.role != 'admin').all()
    return jsonify([{
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "location": user.location,
        "phone": user.phone,
        "dob": user.dob,
        "approved": user.approved
    } for user in users]), 200

@admin_routes.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    return jsonify({"message": "User approved"}), 200

@admin_routes.route('/admin/doctors', methods=['GET'])
@jwt_required()
@admin_required
def list_all_doctors():
    doctors = DoctorProfile.query.all()
    return jsonify([{
        "id": doc.id,
        "email": doc.user.email,
        "specialty": doc.specialty,
        "license_no": doc.license_no,
        "is_approved": doc.user.approved,
        "license_pdf_path": doc.license_pdf_path
    } for doc in doctors]), 200

@admin_routes.route('/admin/doctor/<int:doctor_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_doctor(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    doctor.user.approved = True
    db.session.commit()
    return jsonify({"message": "Doctor approved"}), 200

@admin_routes.route('/admin/doctor/<int:doctor_id>/reject', methods=['POST'])
@jwt_required()
@admin_required
def reject_doctor(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor registration rejected and deleted"}), 200
