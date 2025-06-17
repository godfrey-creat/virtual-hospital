from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from .models import db, User, DoctorProfile
import os

auth_routes = Blueprint('auth_routes', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploaded_licenses')
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        location = request.form.get('location')
        dob = request.form.get('dob')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash("User already exists", "danger")
            return render_template('register.html')

        user = User(
            email=email,
            phone=phone,
            location=location,
            dob=dob,
            role=role,
            approved=False
        )
        user.set_password(password)

        if role == "doctor":
            specialty = request.form.get('specialty')
            license_no = request.form.get('license_no')
            license_file = request.files.get('license')

            if not license_file or not allowed_file(license_file.filename):
                flash("Invalid or missing license PDF file", "danger")
                return render_template('register.html')

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
        flash("Registration submitted. Account pending admin approval.", "info")
        return redirect(url_for('auth_routes.login'))

    return render_template('register.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid credentials", "danger")
            return render_template('login.html')

        if not user.approved:
            flash("Account not approved by admin yet", "warning")
            return render_template('login.html')

        session['user_id'] = user.id
        flash("Login successful", "success")
        return redirect(url_for('auth_routes.dashboard'))

    return render_template('login.html')

@auth_routes.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('auth_routes.login'))

@auth_routes.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth_routes.login'))
    user = User.query.get(user_id)
    return render_template('dashboard.html', user=user)