from flask_sqlalchemy import SQLAlchemy
import datetime

from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()
db = SQLAlchemy()


class Medication(db.Model):
    __tablename__ = 'medications'

    id = db.Column(db.Integer, primary_key=True)
    medication_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    start_time = db.Column(db.Time, default=datetime.time)
    next_dose_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    next_dose_time = db.Column(db.Time, default=datetime.time)
    is_taken = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    purpose = db.Column(db.Text)
    indications_and_usage = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False,)


class User(db.Model):
    """User in the system"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    medications = db.relationship('Medication')

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,

        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


def connect_db(app):
    """Connect to database."""
    db.app = app
    db.init_app(app)
