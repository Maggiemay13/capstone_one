from flask_sqlalchemy import SQLAlchemy
import datetime

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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)


def connect_db(app):
    """Connect to database."""
    db.app = app
    db.init_app(app)
