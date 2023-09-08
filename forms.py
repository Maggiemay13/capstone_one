from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, widgets, DateField
from wtforms.validators import DataRequired
import datetime
from wtforms.fields.core import Field
from wtforms.widgets import Input
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
    next_dose_time = DateField('Next Dose Time', format='%Y-%m-%d')
    notes = StringField('Add Notes')


class MedicationInfoForm(FlaskForm):
    """Show information about medication"""
    medication_name = StringField('Name')
    start_date = DateField('Start Date', format='%Y-%m-%d')
    next_dose_time = DateField('Next Dose', format='%Y-%m-%d')
    notes = StringField('Notes')
    purpose = TextAreaField('Purpose')
    indications_and_usage = TextAreaField('Indications and Usage')


class EditMedicationForm(FlaskForm):
    """Edit Medication"""

    medication_name = StringField(
        'Medication Name', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    next_dose_time = DateField('Next Dose Time', format='%Y-%m-%d')
    notes = StringField('Notes')


# class WarningsandQuestions(FlaskForm):
