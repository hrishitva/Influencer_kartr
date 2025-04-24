# import os
# import logging
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
# from sqlalchemy.orm import DeclarativeBase

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Base class for SQLAlchemy models
# class Base(DeclarativeBase):
#     pass

# # Initialize SQLAlchemy
# db = SQLAlchemy(model_class=Base)

# # Initialize Flask app
# app = Flask(__name__)
# app.secret_key = os.environ.get("SESSION_SECRET", "kartr_secret_key_for_development")

# # Configure database - for development using SQLite
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///kartr.db")
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
#     "pool_recycle": 300,
#     "pool_pre_ping": True,
# }

# # Initialize the database with the app
# db.init_app(app)

# # Set up Flask-Login
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'
# login_manager.login_message_category = 'info'

# # Import models and create tables
# with app.app_context():
#     from models import User
#     db.create_all()
#     logger.debug("Database tables created")

# # Load user from user ID (required by Flask-Login)
# @login_manager.user_loader
# def load_user(user_id):
#     from models import User
#     return User.query.get(int(user_id))





import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kartr_secret_key_for_development")

# Configure database - for development using SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///kartr.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set YouTube API key from environment variable
app.config["YOUTUBE_API_KEY"] = os.environ.get("YOUTUBE_API_KEY", "")

# Initialize the database with the app
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models and create tables
with app.app_context():
    from models import User
    db.create_all()
    logger.debug("Database tables created")

# Load user from user ID (required by Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# --------------------------------------
# API Route: Toggle Email Visibility
# --------------------------------------
@app.route('/api/toggle-email-visibility', methods=['POST'])
def toggle_email_visibility():
    try:
        data = request.get_json()

        if not data or "email_visible" not in data:
            return jsonify({"error": "Invalid data"}), 400

        email_visible = data["email_visible"]

        # Optional: Update the user's email visibility in the DB
        # from flask_login import current_user
        # user = User.query.get(current_user.id)
        # user.email_visible = email_visible
        # db.session.commit()

        logger.debug(f"Email visibility set to: {email_visible}")
        return jsonify({"success": True, "email_visible": email_visible}), 200

    except Exception as e:
        logger.error(f"Error in toggle-email-visibility: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# --------------------------------------
# Optional: Handle 404 errors with JSON
# --------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404
