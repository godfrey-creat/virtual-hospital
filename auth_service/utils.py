from flask_jwt_extended import create_access_token
from datetime import timedelta
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from .models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access only"}), 403
        return fn(*args, **kwargs)
    return wrapper

def generate_token(identity, role):
    return create_access_token(identity={"email": identity, "role": role}, expires_delta=timedelta(days=1))
