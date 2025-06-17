from flask import Flask
from auth_service.models import db
from auth_service.admin_routes import admin_routes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///virtual_hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Link db to app
db.init_app(app)

# Register blueprints
#app.register_blueprint(admin_routes)

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=3000, debug=True)
