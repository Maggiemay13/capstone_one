from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, TimeField, DateField, PasswordField
from wtforms.validators import DataRequired, Length, Email


__all__ = (
    "DateTimeField",
    "DateField",
    "TimeField",
    "MonthField",
    "DateTimeLocalField",
)


class SearchMedicationForm(FlaskForm):
    """Search for new medication"""
    medication = StringField('Medication', validators=[DataRequired()])
    submit = SubmitField('Search')


class AddMedicationForm(FlaskForm):
    """Form for adding a new medication to list"""

    medication_name = StringField(
        'Medication Name', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    start_time = TimeField('Start Time', format='%H:%M')
    next_dose_date = DateField('Reminder Date', format='%Y-%m-%d')
    next_dose_time = TimeField('Reminder Time', format='%H:%M')
    notes = StringField('Add Notes')


class MedicationInfoForm(FlaskForm):
    """Show information about medication"""
    medication_name = StringField('Name')
    start_date = DateField('Start Date', format='%Y-%m-%d')
    start_time = TimeField('Start Time', format='%I:%M %p')
    next_dose_date = DateField('Reminder Date', format='%Y-%m-%d')
    next_dose_time = TimeField('Reminder Time', format='%I:%M %p')
    notes = StringField('Notes')
    purpose = TextAreaField('Purpose')
    indications_and_usage = TextAreaField('Indications and Usage')


class EditMedicationForm(FlaskForm):
    """Edit Medication"""

    medication_name = StringField(
        'Medication Name', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    start_time = TimeField('Start Time', format='%H:%M')
    next_dose_date = DateField('Next Dose Date', format='%Y-%m-%d')
    next_dose_time = TimeField('NextTime', format='%H:%M')
    notes = StringField('Notes')


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
