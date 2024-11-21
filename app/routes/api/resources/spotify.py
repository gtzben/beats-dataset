"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""

import os
import uuid
import spotipy

from http import HTTPStatus
from flask import current_app, redirect, url_for, request, session, render_template, make_response

from flask_restful import Resource

from app.routes.api.models.spotifyaccount import SpotifyAccount

class SpotifyResource(Resource):
    """
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    def get(self):

        """
        TODO: Prevent duplicated permissions and cache files for the same account.

        """

        # Ensure the user has a unique cache ID
        if 'uuid' not in session:
            session['uuid'] = str(uuid.uuid4())

        scope = "user-read-playback-state user-read-email"

        cache_path = os.path.join(os.path.abspath("."),"data", "cache", f".cache-{session['uuid']}")
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=cache_path)

        self.logger.debug(cache_path)

        auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=current_app.config["SPOTIPY_CLIENT_ID"],
                                                   client_secret=current_app.config["SPOTIPY_CLIENT_SECRET"],
                                                   scope=scope,
                                                   cache_handler=cache_handler,
                                                   redirect_uri=url_for("api.spotifyresource", _external=True),
                                                   show_dialog=True)

        if request.args.get("code"):
            # Step 2. Being redirected from Spotify auth page
            auth_manager.get_access_token(request.args.get("code"))
            return redirect(url_for("api.spotifyresource", _external=False))

        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            # Step 1. Redirect to sign in when no token
            auth_url = auth_manager.get_authorize_url()
            return redirect(auth_url)

        # Step 3. Signed in, display data
        spotify = spotipy.Spotify(auth_manager=auth_manager)

        if SpotifyAccount.get_by_email(email=spotify.me()['email']):
            return {'message': 'This account has already been connected'}, HTTPStatus.BAD_REQUEST

        self.logger.debug(f"{spotify.me()['email']} has login successuly to Spotify")

        data = {"account_email": spotify.me()["email"],
                "uri": spotify.me()["uri"],
                "cache_path": cache_path}
        
        spotify_account = SpotifyAccount(**data)
        spotify_account.save()

        return (make_response(render_template('spotify_login_sucessful.html', display_name=spotify.me()["display_name"]),
                               HTTPStatus.OK, {'Content-Type': 'text/html'}))
    