from flask import Flask
from auth_service.models import db  # just import db here
from auth_service.admin_routes import admin_routes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///virtual_hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Link db to app
db.init_app(app)

with app.app_context():
    db.create_all()

#app.register_blueprint(admin_routes)
