from flask import request, jsonify
from flask_jwt_extended import create_access_token
from app import app, db
from models import User, DoctorProfile
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import os

UPLOAD_FOLDER = 'uploaded_licenses'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['POST'])
def register():
    role = request.form.get('role')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    location = request.form.get('location')
    dob = request.form.get('dob')

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    # All registrations require admin approval by default
    user = User(
        email=email,
        phone=phone,
        location=location,
        dob=dob,
        role=role,
        approved=False  # All users require admin approval now
    )
    user.set_password(password)

    if role == "doctor":
        specialty = request.form.get('specialty')
        license_no = request.form.get('license_no')
        license_file = request.files.get('license')

        if not license_file or not allowed_file(license_file.filename):
            return jsonify({"error": "Invalid or missing license PDF file"}), 400

        filename = secure_filename(f"{email}_license.pdf")
        license_path = os.path.join(UPLOAD_FOLDER, filename)
        license_file.save(license_path)

        doctor_profile = DoctorProfile(
            specialty=specialty,
            license_no=license_no,
            license_pdf_path=license_path
        )
        user.doctor_profile = doctor_profile

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration submitted. Account pending admin approval"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.approved:
        return jsonify({"error": "Account not approved by admin yet"}), 403

    access_token = create_access_token(identity=user.email, additional_claims={"role": user.role})
    return jsonify({"access_token": access_token}), 200

auth_routes = Blueprint('auth_routes', __name__)

jwt_blacklist = set()

@auth_routes.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    jwt_blacklist.add(jti)
    return jsonify({"message": "Successfully logged out"}), 200
