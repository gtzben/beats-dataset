import os, uuid, spotipy, requests
from http import HTTPStatus
from flask import render_template, redirect, url_for, flash, session, request
from app.utils import verify_token
from app.routes.portal import portal_bp
from app.routes.portal.forms import( LoginForm, RegistrationForm, DeviceForm, ParticipantForm,
                                     AssociationForm, ResetPasswordRequestForm, ResetPasswordForm)

@portal_bp.route('/login',  methods=['GET', 'POST'])
def login():

    # Retrieve the token from the session
    token = session.get('access_token')
    if token is not None:
        return redirect(url_for('portal.dashboard'))

    flash("Please, log in to access the experimenter dashboard", "info")

    form = LoginForm()

    if form.validate_on_submit():

        session.pop('_flashes', None)

        data = {
        "email": form.email.data,
        "password": form.password.data
        }

        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.loginresource", _external=True), json=data)
        api_data = response.json()

        if response.status_code == HTTPStatus.OK:
            # Save tokens in the session
            session['access_token'] = api_data['access_token']
            session['refresh_token'] = api_data['refresh_token']
            flash('Login successful!', 'success')
            return redirect(url_for('portal.dashboard'))  # Redirect to the dashboard
        elif response.status_code in [HTTPStatus.UNAUTHORIZED,HTTPStatus.FORBIDDEN]:
            flash(api_data["message"], 'danger')
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('login_experimenter.html', title='Sign In', form=form, token=token)


@portal_bp.route('/register',  methods=['GET', 'POST'])
def register():

    flash("Please, enter your detail to create an experimenter account", "info")

    form = RegistrationForm()

    if form.validate_on_submit():

        data = {"email":form.email.data,
        "password":form.password.data,
        "institution":form.institution.data
        }

        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.userresource", _external=True), json=data)
        api_data = response.json()

        if response.status_code == HTTPStatus.CREATED:
            # Save tokens in the session
            flash('User created! Please, verify your email to login', 'success')
            return redirect(url_for('portal.login'))  # Redirect to the dashboard
        elif response.status_code == HTTPStatus.BAD_REQUEST:
            flash(api_data["message"], 'danger')
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('register_experimenter.html', title='Experimenter Registration', form=form, token=None)


@portal_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():

    # Retrieve the token from the session
    token = session.get('access_token')
    if token is not None:
        return redirect(url_for('portal.dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():

        data = {"email": form.email.data}
        
        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.resetpwdrequest", _external=True), json=data)
        api_data = response.json()

        if response.status_code == HTTPStatus.OK:
            flash(api_data["message"], 'success')
            return redirect(url_for('portal.login'))  # Redirect to the dashboard
        elif response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND]:
            flash(api_data["message"], 'danger')
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('reset_password_request.html', title='Reset Password', form=form, token=token)


@portal_bp.route('/reset-password/<reset_pwd_token>', methods=['GET', 'POST'])
def reset_password(reset_pwd_token):

    # Retrieve the token from the session
    token = session.get('access_token')
    if token is not None:
        return redirect(url_for('portal.dashboard'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():

        data = {"reset_pwd_token": reset_pwd_token,
                "password": form.password.data}
        
        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.resetpwd", _external=True), json=data)
        api_data = response.json()

        if response.status_code == HTTPStatus.OK:
            flash(api_data["message"], 'success')
            return redirect(url_for('portal.login'))  # Redirect to the dashboard
        elif response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND]:
            flash(api_data["message"], 'danger')
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('reset_password.html', form=form, token=token)


@portal_bp.route('/logout')
def logout():
    if 'access_token' in session:
        response = requests.post(
            url_for("api.logoutresource", _external=True),
            headers={"Authorization": f"Bearer {session['access_token']}"}
        )
        if response.status_code in [HTTPStatus.OK, HTTPStatus.UNAUTHORIZED]:
            # Clear the session
            session.clear()
            flash('Logged out successfully.', 'success')
            return redirect(url_for('portal.login'))

        else:
            flash('An error occurred during logout.', 'danger')

    return redirect(url_for('portal.dashboard'))


@portal_bp.route('/dashboard',  methods=['GET', 'POST'])
def dashboard():
    """

    """
    # Retrieve the token from the session
    token = session.get('access_token')
    if not token:
        flash("You must log in first.", "danger")
        return redirect(url_for("portal.login"))

    headers = {"Authorization": f"Bearer {token}"}

    return render_template('dashboard_experimenter.html', title='Dashboard Experimenter', token=token)


@portal_bp.route('/register-resources', methods=['GET', 'POST'])
def register_resources():
    """

    """

    participant_form = ParticipantForm()
    device_form = DeviceForm()
 
    if participant_form.validate_on_submit() and participant_form.submit.data:
        # Handle participant registration
        participant_data = {"pid":participant_form.pid.data,
                            "email": participant_form.email.data,
                            "ndh": participant_form.ndh.data}

        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.participantresource", _external=True),
                                headers={"Authorization": f"Bearer {session['access_token']}"},
                                json=participant_data)
        if response.status_code == HTTPStatus.CREATED:
            flash(f"Successfully registered participant: {participant_data['pid']}", "success")
            return redirect(url_for('portal.dashboard'))
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            # Try refreshing the token
            if refresh_access_token():
                return redirect(request.url)  # Retry the request
            else:
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('portal.login'))

        else:
            flash(response.json()['message'], 'warning')
            return  redirect(url_for('portal.dashboard'))


    if device_form.validate_on_submit() and device_form.submit.data:
        device_data = {"device_name":device_form.device_name.data,
                        "serial_number": device_form.serial_number.data,
                        "measurement_location": device_form.measurement_location.data}

        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.deviceresource", _external=True),
                                 headers={"Authorization": f"Bearer {session['access_token']}"},
                                 json=device_data)
        if response.status_code == HTTPStatus.CREATED:
            flash(f"Successfully registered device: {device_data['serial_number']}", "success")
            return redirect(url_for('portal.dashboard'))
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            # Try refreshing the token
            if refresh_access_token():
                return redirect(request.url)  # Retry the request
            else:
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('portal.login'))
        else:
            flash(response.json()['message'], 'warning')
            return  redirect(url_for('portal.dashboard'))

    return render_template(
        'register_resources.html',
        participant_form=participant_form,
        device_form=device_form
    )

@portal_bp.route('/view-resources', methods=["GET"])
def view_resources():
    # Fetch resources from the database

    # sending get request to obtain participants data
    response_participants = requests.get(url=url_for("api.participantportal", _external=True),
                            headers={"Authorization": f"Bearer {session['access_token']}"} )
    participants_data = response_participants.json()

    # sending get request to obtain devices data
    response_devices = requests.get(url=url_for("api.deviceresource", _external=True),
                            headers={"Authorization": f"Bearer {session['access_token']}"} )
    devices_data = response_devices.json()

    # sending get request to obtain spotify accounts data
    response_spotify = requests.get(url=url_for("api.spotifyaccountsresource", _external=True),
                            headers={"Authorization": f"Bearer {session['access_token']}"} )
    spotify_data = response_spotify.json()

    if (response_participants.status_code == response_devices.status_code ==
        response_spotify.status_code == HTTPStatus.OK):

        participants_header = list(participants_data["data"][0].keys()) if participants_data["data"] else []
        participants_values = [tuple(d.values()) for d in participants_data["data"]]

        devices_header = list(devices_data["data"][0].keys()) if devices_data["data"] else []
        devices_values = [tuple(d.values()) for d in devices_data["data"]]

        spotify_header = list(spotify_data["data"][0].keys()) if spotify_data["data"] else []
        spotify_values = [tuple(d.values()) for d in spotify_data["data"]]

        return render_template('view_resources.html',
                           participants_header=participants_header, participants_values=participants_values,
                           spotify_header=spotify_header, spotify_values=spotify_values,
                           device_header=devices_header, device_values=devices_values)
    
    elif (response_participants.status_code == response_devices.status_code ==
        response_spotify.status_code == HTTPStatus.UNAUTHORIZED):
        # Try refreshing the token
        if refresh_access_token():
            return redirect(request.url)  # Retry the request
        else:
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('portal.login'))
    else:
        return  f"<h1>{participants_data['message']}<h1>"



@portal_bp.route('/associate-resources', methods=['GET', 'POST'])
def associate_resources():
    # Fetch participants, devices and accounts available for dropdowns
    participants_url = url_for("api.participantportal", _external=True) + "?is-verified=true&is-active=true"
    response_participants = requests.get(url=participants_url,
                            headers={"Authorization": f"Bearer {session['access_token']}"})
    participants_data = response_participants.json()


    device_url = url_for("api.deviceresource", _external=True) + "?available-only=true"
    response_devices = requests.get(url=device_url,
                            headers={"Authorization": f"Bearer {session['access_token']}"})
    devices_data = response_devices.json()



    spotify_url = url_for("api.spotifyaccountsresource", _external=True) + "?available-only=true"
    response_spotify = requests.get(url=spotify_url,
                            headers={"Authorization": f"Bearer {session['access_token']}"})
    spotify_data = response_spotify.json()


    if (response_participants.status_code == response_devices.status_code ==
        response_spotify.status_code == HTTPStatus.UNAUTHORIZED):
        # Try refreshing the token
        if refresh_access_token():
            return redirect(request.url)  # Retry the request
        else:
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('portal.login'))

    elif (response_participants.status_code == response_devices.status_code ==
        response_spotify.status_code != HTTPStatus.OK):

        return  f"<h1>{participants_data['message']}<h1>"
    

    association_form = AssociationForm()
    association_form.participants.choices = [(p.get("pid"),p.get("pid")) for p in participants_data['data']]
    association_form.devices.choices = [(d.get("serial_number"),d.get("serial_number")) for d in devices_data['data']]
    association_form.spotify_accounts.choices = [(s.get("account_email"),s.get("account_email")) for s in spotify_data['data']]

    if association_form.validate_on_submit():

        data = {
        "serial_number": association_form.devices.data,
        "account_email": association_form.spotify_accounts.data
        }
        associate_url = url_for("api.participantlinkresources", _external=True,
                                participant_pid=association_form.participants.data)

        # sending post request and saving response as response object
        response = requests.patch(url=associate_url, json=data,
                                   headers={"Authorization": f"Bearer {session['access_token']}"})
        api_data = response.json()

        if response.status_code == HTTPStatus.OK:
            # Save tokens in the session
            flash(api_data["message"], 'success')
            return redirect(url_for('portal.dashboard'))  # Redirect to the dashboard
        elif response.status_code == HTTPStatus.BAD_REQUEST:
            flash(api_data["message"], 'danger')
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            # Try refreshing the token
            if refresh_access_token():
                return redirect(request.url)  # Retry the request
            else:
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('portal.login'))
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('associate_resources.html', association_form=association_form)


@portal_bp.route('/connect-spotify')
def connect_spotify():
    return redirect(url_for('api.spotifylogin', _external=True))


def refresh_access_token():
    if 'refresh_token' in session:
        response = requests.post(
            url_for("api.refreshresource", _external=True),
            headers={"Authorization": f"Bearer {session['refresh_token']}"}
        )
        if response.status_code == HTTPStatus.OK:
            session['access_token'] = response.json()['access_token']
            return True
    return False
