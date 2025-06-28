from functools import wraps
from flask import redirect, url_for, flash, session
from auth_service.models import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_routes.login'))

        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth_routes.login'))

        return f(*args, **kwargs)
    return decorated_function
