import requests
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_debugtoolbar import DebugToolbarExtension
from apscheduler.schedulers.background import BackgroundScheduler


from secret import api_key
from models import db, connect_db, Medication
from forms import SearchMedicationForm, AddMedicationForm, MedicationInfoForm, EditMedicationForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///med-reminder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "I'LL NEVER TELL!!"
toolbar = DebugToolbarExtension(app)


connect_db(app)


# API_LABEL_BASE_URL = 'https://api.fda.gov/drug/label.json'
API_BASE_URL = 'https://api.fda.gov/drug'

scheduler = BackgroundScheduler()


def send_notification(medication_name):
    message = f"It's time to take your {medication_name}."
    flash(message, 'info')


scheduler.start()


def get_generic_or_brand_names(medication):
    """Search for both generic and brand names of medication"""
    medication_names = []

    # Search for generic name
    generic_res = requests.get(
        f"{API_BASE_URL}/label.json",
        params={'api_key': api_key,
                'search': f'openfda.generic_name:"{medication}"'}
    )
    generic_data = generic_res.json()

    if "results" in generic_data and generic_data["results"]:
        # Loop through all matching results and collect the medication names
        for result in generic_data["results"]:
            generic_name = result["openfda"]["generic_name"][0]
            medication_names.append(generic_name)

    # If generic name was not found, search for brand name
    if not medication_names:
        brand_res = requests.get(
            f"{API_BASE_URL}/label.json",
            params={'api_key': api_key,
                    'search': f'openfda.brand_name:"{medication}"'}
        )
        brand_data = brand_res.json()
        if "results" in brand_data and brand_data["results"]:
            # Loop through all matching results and collect the medication names
            for result in brand_data["results"]:
                brand_name = result["openfda"]["brand_name"][0]
                medication_names.append(brand_name)

    return medication_names


def get_medication_info(medication_name):
    purpose = None
    indications_and_usage = None

    # Search for medication information - Purpose (First API Route)
    purpose_res = requests.get(
        f"{API_BASE_URL}/label.json",
        params={'api_key': api_key, 'search': f'purpose:"{medication_name}"'}
    )
    purpose_data = purpose_res.json()
    if "results" in purpose_data and purpose_data["results"]:
        purpose = purpose_data["results"][0].get("purpose", [None])[0]

    # If purpose is not found in the first API route, search the second API route
    if purpose is None:
        purpose_res2 = requests.get(
            f"{API_BASE_URL}/label.json",
            params={'api_key': api_key, 'search': f'"{medication_name}"'}
        )
        purpose_data2 = purpose_res2.json()
        if "results" in purpose_data2 and purpose_data2["results"]:
            purpose = purpose_data2["results"][0].get("purpose", ['*'])[0]

    # Search for medication information - Indications and Usage (First API Route)
    indications_and_usage_res = requests.get(
        f"{API_BASE_URL}/label.json",
        params={'api_key': api_key,
                'search': f'indications_and_usage:"{medication_name}"'}
    )
    indications_and_usage_data = indications_and_usage_res.json()
    if "results" in indications_and_usage_data and indications_and_usage_data["results"]:
        indications_and_usage = indications_and_usage_data["results"][0].get(
            "indications_and_usage", ['*'])[0]

    # If indications and usage is not found in the first API route, search the second API route
    if indications_and_usage is None:
        indications_and_usage_res2 = requests.get(
            f"{API_BASE_URL}/label.json",
            params={'api_key': api_key, 'search': f'"{medication_name}"'}
        )
        indications_and_usage_data2 = indications_and_usage_res2.json()
        if "results" in indications_and_usage_data2 and indications_and_usage_data2["results"]:
            indications_and_usage = indications_and_usage_data2["results"][0].get(
                "indications_and_usage", [None])[0]

    return {'Purpose': purpose, 'Indications and Usage': indications_and_usage}


@app.route("/")
def home_page():
    """Render home page with list of medications"""
    medications = Medication.query.all()
    return render_template("home.html", medications=medications)


@app.route("/medication_list")
def medication_list():
    """Render home page with list of medications"""
    medications = Medication.query.all()
    return render_template("home_med_list.html", medications=medications)


@app.route('/search', methods=['GET', 'POST'])
def search_medication():
    form = SearchMedicationForm()
    medications = None

    if form.validate_on_submit():
        medication_name = form.medication.data
        medications = get_generic_or_brand_names(medication_name)

    return render_template("search_medication.html", form=form, medications=medications)


@app.route('/add_medication', methods=["GET", "POST"])
def add_medication():

    form = AddMedicationForm()
    # how to prefill the add medication form with name of medication that was clicked on with the /seach route
    medication_name = request.args.get('medication_name')

    if medication_name:
        form.medication_name.data = medication_name

    if form.validate_on_submit():

        medication_name = form.medication_name.data
        start_date = form.start_date.data
        start_time = form.start_time.data
        next_dose_date = form.next_dose_date.data
        next_dose_time = form.next_dose_time.data
        notes = form.notes.data
        new_medication = Medication(medication_name=medication_name,
                                    start_date=start_date, start_time=start_time, next_dose_date=next_dose_date, next_dose_time=next_dose_time,  notes=notes)
        db.session.add(new_medication)
        db.session.commit()
        flash('Medication added successfully.', 'success')
        return redirect('/medication_list')
    else:
        return render_template("add_medication.html", form=form)


@app.route('/medication/<int:medication_id>', methods=['GET'])
def show_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    medication_info_form = MedicationInfoForm()
    medication_info_form.medication_name.data = medication.medication_name
    medication_info_form.start_date.data = medication.start_date
    medication_info_form.start_time.data = medication.start_time
    medication_info_form.next_dose_date.data = medication.next_dose_date
    medication_info_form.next_dose_time.data = medication.next_dose_time
    medication_info_form.notes.data = medication.notes

    # Fetch purpose and indications and usage from the API using get_medication_info
    medication_info = get_medication_info(medication.medication_name)
    medication_info_form.purpose.data = medication_info.get('Purpose')
    medication_info_form.indications_and_usage.data = medication_info.get(
        'Indications and Usage')

    return render_template("medication_info.html", medication_info_form=medication_info_form, medication=medication)


@app.route('/edit_medication/<int:medication_id>', methods=["GET", "POST"])
def edit_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    form = EditMedicationForm()

    if request.method == "GET":
        # Populate the form fields with the existing data for the medication
        form.medication_name.data = medication.medication_name
        form.start_date.data = medication.start_date
        form.start_time.data = medication.start_time
        form.next_dose_date.data = medication.next_dose_date
        form.next_dose_time.data = medication.next_dose_time
        form.notes.data = medication.notes

    if form.validate_on_submit():
        # Update the medication with the new data
        medication.medication_name = form.medication_name.data
        medication.start_date = form.start_date.data
        medication.start_time = form.start_time.data
        medication.next_dose_date = form.next_dose_date.data
        medication.next_dose_time = form.next_dose_time.data
        medication.notes = form.notes.data

        # Commit the changes to the database
        db.session.commit()
        flash('Medication updated successfully.', 'success')
        return redirect('/')
    return render_template("edit_medication.html", form=form, medication=medication)


@app.route('/delete_medication/<int:medication_id>', methods=['GET', 'POST'])
def delete_medication(medication_id):
    # Retrieve the medication by ID and delete it from the database
    medication = Medication.query.get_or_404(medication_id)
    db.session.delete(medication)
    db.session.commit()

    flash('Medication deleted successfully', 'success')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
