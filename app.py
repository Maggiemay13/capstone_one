from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, flash, url_for, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
from pytz import timezone
from models import db, connect_db, Medication, User
from forms import SearchMedicationForm, AddMedicationForm, MedicationInfoForm, EditMedicationForm, LoginForm, UserAddForm, UserEditForm
import os

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
#
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", 'postgresql:///med-reminder')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = 'any secret string'
# toolbar = DebugToolbarExtension(app)
# postgresql:///med-reminder

connect_db(app)


API_BASE_URL = 'https://api.fda.gov/drug'


###################################################################################################
# Send Email
def send_simple_message():
    return requests.post(
        "https://api.mailgun.net/v3/sandbox5fd139902c914fb48adf37184fa70950.mailgun.org/messages",
        auth=("api", "34cf11b275ddc9b52c475a735597ac25-5465e583-45ce96c3"),
        data={"from": "Excited User <mailgun@sandbox5fd139902c914fb48adf37184fa70950.mailgun.org>",
              "to": ["margaret13.may@gmail.com", "YOU@sandbox5fd139902c914fb48adf37184fa70950.mailgun.org"],
              "subject": "Hello",
              "text": "Testing some Mailgun awesomeness!"})

##########################################################################################
# Notification information and messages.


# The "apscheduler." prefix is hard coded
scheduler = BackgroundScheduler({

    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': 'sqlite:///jobs.sqlite'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '20'
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': '5'
    },
    'apscheduler.job_defaults.coalesce': 'false',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.timezone': 'UTC',
})


def send_flash_message():
    flash("Time to take your medicine!")


def schedule_flash_message(user_input_datetime):
    try:
        # Convert user_input_datetime to a datetime object
        reminder_time = datetime.strptime(
            user_input_datetime, '%Y-%m-%d %H:%M')
        current_time = datetime.now()

        if reminder_time <= current_time:
            flash("Invalid reminder time. Please choose a future date and time.")
            # Redirect back to the form
            return redirect(url_for('add_medication'))

        # Calculate the run_date as a datetime object
        run_date = reminder_time

        # Convert datetime objects to your desired formats
        formatted_reminder_time = reminder_time.strftime('%B %d, %Y')
        formatted_run_date = run_date.strftime('%I:%M %p %Z')

        # Schedule the flash message with the calculated run_date
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(send_flash_message, DateTrigger(run_date=run_date))

        # Display formatted dates and times in the flash message
        flash(
            f"Notification message scheduled for {formatted_reminder_time} at {formatted_run_date}.")

        return scheduler
    except ValueError:
        flash("Invalid date or time format. Please use YYYY-MM-DD HH:MM.")


###########################################################################################
# retreive API information
def get_generic_or_brand_names(medication):
    """Search for both generic and brand names of medication"""
    medication_names = []

    # Search for generic name
    generic_res = requests.get(
        f"{API_BASE_URL}/label.json",
        params={'os.environ.get("api_key")': os.environ.get("api_key"),
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
            params={'os.environ.get("api_key")': os.environ.get("api_key"),
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
        params={'os.environ.get("api_key")': os.environ.get(
            "api_key"), 'search': f'purpose:"{medication_name}"'}
    )
    purpose_data = purpose_res.json()
    if "results" in purpose_data and purpose_data["results"]:
        purpose = purpose_data["results"][0].get("purpose", [None])[0]

    # If purpose is not found in the first API route, search the second API route
    if purpose is None:
        purpose_res2 = requests.get(
            f"{API_BASE_URL}/label.json",
            params={'os.environ.get("api_key")': os.environ.get(
                "api_key"), 'search': f'"{medication_name}"'}
        )
        purpose_data2 = purpose_res2.json()
        if "results" in purpose_data2 and purpose_data2["results"]:
            purpose = purpose_data2["results"][0].get("purpose", ['*'])[0]

    # Search for medication information - Indications and Usage (First API Route)
    indications_and_usage_res = requests.get(
        f"{API_BASE_URL}/label.json",
        params={'os.environ.get("api_key")': os.environ.get("api_key"),
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
            params={'os.environ.get("api_key")': os.environ.get(
                "api_key"), 'search': f'"{medication_name}"'}
        )
        indications_and_usage_data2 = indications_and_usage_res2.json()
        if "results" in indications_and_usage_data2 and indications_and_usage_data2["results"]:
            indications_and_usage = indications_and_usage_data2["results"][0].get(
                "indications_and_usage", [None])[0]

    return {'Purpose': purpose, 'Indications and Usage': indications_and_usage}


##############################################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/")


###############################################################################################

@app.route("/")
def home_page():
    """Render home page"""
    medications = Medication.query.all()
    return render_template("home.html", medications=medications)


@app.route("/medication_list")
def medication_list():
    """Render home page with list of medications"""

    if not g.user:
        flash("Access unauthorized please sign in to access medications.", "danger")
        return redirect("/")

    medications = Medication.query.all()
    return render_template("home_med_list.html", medications=medications, datetime=datetime)


@app.route('/search', methods=['GET', 'POST'])
def search_medication():

    if not g.user:
        flash("Access unauthorized please sign in to access medications.", "danger")
        return redirect("/")

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

    user = g.user

    if form.validate_on_submit():

        medication_name = form.medication_name.data
        start_date = form.start_date.data
        start_time = form.start_time.data
        next_dose_date = form.next_dose_date.data
        next_dose_time = form.next_dose_time.data
        notes = form.notes.data
        user.user_id = user.id
        new_medication = Medication(medication_name=medication_name,
                                    start_date=start_date, start_time=start_time, next_dose_date=next_dose_date, next_dose_time=next_dose_time,  notes=notes, user_id=user.id)

        next_dose_date = request.form['next_dose_date']
        next_dose_time = request.form['next_dose_time']

        # next_dose_date = next_dose_date.strftime('%Y-%m-%d')
        # next_dose_time = next_dose_time.strftime('%H:%M:%S')

        # Combine date and time into user_input_datetime with the expected format
        user_input_datetime = f"{next_dose_date} {next_dose_time}"
        # Schedule the flash message
        schedule_flash_message(user_input_datetime)

        db.session.add(new_medication)
        db.session.commit()
        flash('Medication successfully added.', 'success')
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
        return redirect('/medication_list')
    return render_template("edit_medication.html", form=form, medication=medication)


@app.route('/delete_medication/<int:medication_id>', methods=['GET', 'POST'])
def delete_medication(medication_id):
    # Retrieve the medication by ID and delete it from the database
    medication = Medication.query.get_or_404(medication_id)
    db.session.delete(medication)
    db.session.commit()

    flash('Medication deleted successfully', 'success')
    return redirect('/medication_list')


if __name__ == '__main__':
    app.run(debug=True)
