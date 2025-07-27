import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from .models import db, User, DoctorProfile, Facility

# Session-based admin_required decorator
from functools import wraps

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user or user.role != "admin":
            flash("Admin access only", "danger")
            return redirect(url_for('admin_routes.admin_login'))
        return fn(*args, **kwargs)
    return wrapper

# Blueprint setup; templates will be found in auth_service/templates/
admin_routes = Blueprint(
    'admin_routes',
    __name__,
    template_folder='templates'  # Looks in auth_service/templates/
)

@admin_routes.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = User.query.filter_by(email=email, role='admin').first()
        if not admin or not check_password_hash(admin.password_hash, password):
            flash("Invalid credentials", "danger")
            return render_template('admin_login.html')

        session['user_id'] = admin.id
        flash("Admin login successful", "success")
        return redirect(url_for('admin_routes.admin_dashboard'))
    
    return render_template('admin_login.html')

@admin_routes.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@admin_routes.route('/admin/approve_users')
@admin_required
def approve_users():
    pending_users = User.query.filter(User.approved == False, User.role != 'admin').all()
    return render_template('admin/approve_users.html', pending_users=pending_users)

@admin_routes.route('/admin/approve_users/<int:user_id>', methods=['POST'])
@admin_required
def admin_approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    flash(f'User {user.email} approved!', "success")
    return redirect(url_for('admin_routes.approve_users'))


@admin_routes.route('/admin/approve_doctors')
@admin_required
def approve_doctors():
    doctors = DoctorProfile.query.join(User).filter(User.approved == False).all()
    return render_template('admin/approve_doctors.html', doctors=doctors)

@admin_routes.route('/admin/approve_doctors/<int:doctor_id>', methods=['POST'])
@admin_required
def admin_approve_doctor(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    doctor.user.approved = True
    doctor.approved = True  # Ensure both User and DoctorProfile show approved
    db.session.commit()
    flash(f'Doctor {doctor.user.email} approved!', "success")
    return redirect(url_for('admin_routes.approve_doctors'))

@admin_routes.route('/admin/reject_doctor/<int:doctor_id>', methods=['POST'])
@admin_required
def reject_doctor(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    user = doctor.user
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()
    flash(f'Doctor {user.email} rejected and deleted.', "info")
    return redirect(url_for('admin_routes.reject_doctor'))

@admin_routes.route('/admin/approve_facilities')
@admin_required
def approve_facilities():
    pending_facilities = Facility.query.filter_by(approved=False).all()
    return render_template('admin/approve_facilities.html', pending_facilities=pending_facilities)
@admin_routes.route('/admin/approve_facility/<int:facility_id>', methods=['POST'])
@admin_required
def admin_approve_facility(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    facility.approved = True
    db.session.commit()
    flash(f'Facility "{facility.name}" approved!', "success")
    return redirect(url_for('admin_routes.approve_facilities'))
@admin_routes.route('/admin/reject_facility/<int:facility_id>', methods=['POST'])
@admin_required
def admin_reject_facility(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    db.session.delete(facility)
    db.session.commit()
    flash(f'Facility "{facility.name}" rejected and deleted.', "info")
    return redirect(url_for('admin_routes.approve_facilities'))
