from flask import Flask, render_template
from auth_service.models import db
from auth_service.auth_routes import auth_routes
from auth_service.admin_routes import admin_routes
from facilities.facilities_routes import facilities_routes
import os

# Initialize the Flask app
app = Flask(
    __name__,
    template_folder=os.path.join('auth_service', 'templates')  # Shared template folder
)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///virtual_hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Needed for sessions and flash messages

# Initialize database
db.init_app(app)

# Landing page route
@app.route('/')
def landing_page():
    return render_template('landing_page/index.html')

# Register blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(facilities_routes, url_prefix='/facilities_routes')

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Run the app
if __name__ == '__main__':
    app.run(port=3000, debug=True)