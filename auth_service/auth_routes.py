from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from .models import db, User, DoctorProfile, Facility  # Add Facility model
from .ai_model import classify_condition  # ← Pretrained CO model you integrate
#from geopy.distance import geodesic  # Optional for proximity
import os

auth_routes = Blueprint('auth_routes', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploaded_licenses')
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------- Register -----------------
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


# ----------------- Login -----------------
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


# ----------------- Logout -----------------
@auth_routes.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('auth_routes.login'))


# ----------------- Dashboard -----------------
@auth_routes.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth_routes.login'))
    
    user = User.query.get(user_id)
    return render_template('users/dashboard.html', user=user)


# ----------------- Doctors -----------------
@auth_routes.route('/doctors')
def view_doctors():
    specialty = request.args.get('specialty', '').strip().lower()
    location = request.args.get('location', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = User.query.filter_by(role='doctor', approved=True).join(DoctorProfile)

    if specialty:
        query = query.filter(db.func.lower(DoctorProfile.specialty).like(f"%{specialty}%"))
    if location:
        query = query.filter(db.func.lower(User.location).like(f"%{location}%"))

    pagination = query.paginate(page=page, per_page=per_page)
    doctors = pagination.items

    return render_template(
        'doctors/list.html',
        doctors=doctors,
        pagination=pagination,
        specialty=specialty,
        location=location
    )


@auth_routes.route('/doctors/<int:doctor_id>')
def doctor_detail(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role='doctor', approved=True).first_or_404()
    return render_template('doctors/detail.html', doctor=doctor)


# ----------------- Facilities -----------------
@auth_routes.route('/facilities')
def view_facilities():
    facilities = Facility.query.filter_by(approved=True).all()
    return render_template('facility/list.html', facilities=facilities)


# ----------------- CoPilot Placeholder -----------------
@auth_routes.route('/copilot', methods=['GET', 'POST'])
def copilot():
    if request.method == 'POST':
        # Collect user input
        user_location = request.form.get('location')
        age = request.form.get('age')
        gender = request.form.get('gender')
        symptoms = request.form.get('symptoms')
        preference = request.form.get('preference')  # doctor or hospital

        # Step 1: Ask model to classify the case
        try:
            recommendation = classify_condition(symptoms, age, gender)  # returns something like 'pharmacy', 'hospital', etc.
        except Exception as e:
            flash("AI model failed to process your input. Try again.", "danger")
            return render_template('copilot.html')

        # Step 2: Fetch closest approved facilities/doctors
        nearby_entities = []
        all_entities = []

        if recommendation == 'doctor':
            all_entities = User.query.filter_by(role='doctor', approved=True).all()
        elif recommendation in ['hospital', 'pharmacy', 'laboratory', 'imaging']:
            all_entities = Facility.query.filter_by(facility_type=recommendation, approved=True).all()

        # You may use a function to compute distance — simplified here
        def simple_match(entity_location):
            return entity_location.lower().strip() in user_location.lower().strip()

        nearby_entities = [e for e in all_entities if simple_match(e.location)]

        if not nearby_entities:
            flash(f"No nearby {recommendation}s found, but here are a few options.", "warning")
            nearby_entities = all_entities[:3]

        return render_template(
            'model/copilot_results.html',
            recommendation=recommendation,
            symptoms=symptoms,
            preference=preference,
            entities=nearby_entities
        )

    return render_template('model/copilot.html')
