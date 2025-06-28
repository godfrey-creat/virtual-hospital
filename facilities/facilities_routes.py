from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from auth_service.models import db, Facility
import os

facilities_routes = Blueprint('facilities_routes', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploaded_facility_licenses')
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@facilities_routes.route('/register', methods=['GET', 'POST'])
def register_facility():
    if request.method == 'POST':
        facility_type = request.form.get('facility_type')
        name = request.form.get('name')
        location = request.form.get('location')
        bio = request.form.get('bio')
        email = request.form.get('email')
        password = request.form.get('password')

        if Facility.query.filter_by(email=email).first():
            flash("Facility with this email already exists", "danger")
            return render_template('facility/register.html', facility_types=["hospital", "pharmacy", "laboratory", "imaging"])

        license_file = request.files.get('license')
        if not license_file or not allowed_file(license_file.filename):
            flash("Invalid or missing license PDF file", "danger")
            return render_template('facility/register.html', facility_types=["hospital", "pharmacy", "laboratory", "imaging"])

        license_filename = secure_filename(f"{email}_license.pdf")
        license_path = os.path.join(UPLOAD_FOLDER, license_filename)
        license_file.save(license_path)

        extra_info = {}
        if facility_type == 'hospital':
            extra_info = {'level': request.form.get('level'), 'services': request.form.get('services')}
        elif facility_type == 'pharmacy':
            extra_info = {'operation_hours': request.form.get('operation_hours'), 'services': request.form.get('services')}
        elif facility_type in ['laboratory', 'imaging']:
            extra_info = {'services': request.form.get('services')}

        facility = Facility(
            facility_type=facility_type,
            name=name,
            location=location,
            bio=bio,
            email=email,
            license_pdf_path=license_path,
            approved=False,
            extra_info=extra_info
        )
        facility.set_password(password)
        db.session.add(facility)
        db.session.commit()
        flash("Facility registration submitted for admin approval", "info")
        return redirect(url_for('facilities_routes.login_facility'))

    # GET request
    return render_template('facility/register.html', facility_types=["hospital", "pharmacy", "laboratory", "imaging"])

@facilities_routes.route('/login', methods=['GET', 'POST'])
def login_facility():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        facility = Facility.query.filter_by(email=email).first()
        if not facility or not facility.check_password(password):
            flash("Invalid login credentials", "danger")
            return render_template('facility/login.html')

        if not facility.approved:
            flash("Facility not approved by admin yet", "warning")
            return render_template('facility/login.html')

        session['facility_id'] = facility.id
        flash("Facility login successful", "success")
        return redirect(url_for('facilities_routes.facility_dashboard'))

    return render_template('facility/login.html')


@facilities_routes.route('/facility/dashboard')
def facility_dashboard():
    facility_id = session.get('facility_id')
    if not facility_id:
        return redirect(url_for('facilities_routes.login_facility'))

    facility = Facility.query.get(facility_id)
    return render_template('facility/dashboard.html', facility=facility)


@facilities_routes.route('/facility/logout')
def logout_facility():
    session.pop('facility_id', None)
    flash("Facility logged out", "info")
    return redirect(url_for('facilities_routes.login_facility'))
