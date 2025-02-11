"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""

import os
import uuid
import spotipy

from http import HTTPStatus
from flask import current_app, redirect, url_for, request, session, flash

from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.models.user import User

from app.routes.api.schemas.spotify import SpotifyAccountSchema

cache_dir = os.path.join(os.path.abspath("."),"data", "cache")

class SpotifyLogin(Resource):
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
        # scope = "user-read-playback-state user-read-email playlist-read-private"

        cache_path = os.path.join(cache_dir, f".cache-{session['uuid']}")
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=cache_path)

        self.logger.debug(cache_path)

        auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=current_app.config["SPOTIPY_CLIENT_ID"],
                                                   client_secret=current_app.config["SPOTIPY_CLIENT_SECRET"],
                                                   scope=scope,
                                                   cache_handler=cache_handler,
                                                   redirect_uri=url_for("api.spotifylogin", _external=True),
                                                   show_dialog=True) 

        if request.args.get("code"):
            # Step 2. Being redirected from Spotify auth page
            auth_manager.get_access_token(request.args.get("code"))
            return redirect(url_for("api.spotifylogin", _external=False))

        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            # Step 1. Redirect to sign in when no token
            auth_url = auth_manager.get_authorize_url()
            return redirect(auth_url)

        # Step 3. Signed in, display data
        try:
            spotify = spotipy.Spotify(auth_manager=auth_manager, retries=0)
            account_info = spotify.me()
            account_email = account_info["email"]
            account_uri = account_info["uri"]
        except spotipy.exceptions.SpotifyBaseException as e:
             self.logger.error(f"Spotify login request failed: {e} - {e.headers}")
             flash(f"Unable to login to Spotify with provided account", "danger")
             return redirect(url_for('portal.dashboard'))

        data = {"account_email": account_email,
                "uri": account_uri,
                "cache_path": cache_path}
    
        account_in_db = SpotifyAccount.get_by_email(email=account_email)
        
        self.logger.debug(f"{account_email} has login successuly to Spotify")


        if account_in_db is None:
            spotify_account = SpotifyAccount(**data)
            spotify_account.save()
        else:
            account_in_db.cache_path = cache_path
            account_in_db.save()
            self.logger.warning(f"{account_email} already connected, updating cache path")


        flash(f"Successfully connected spotify account: {account_email}", "success")

        session.pop('uuid', default=None)

        return redirect(url_for('portal.dashboard'))
    

class SpotifyAccountsResource(Resource):
    """
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def get(self, account_id=None, only_available=False):
        """
        
        """

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:
            if account_id:
                account = SpotifyAccount.get_by_id(id=account_id)

                if account is None:
                    return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
                
                data = SpotifyAccountSchema(exclude=["cache_path"])().dump(account)

            else:
                only_available = request.args.get("available-only", default=False, type=bool)
                all_accounts = SpotifyAccount.get_all_accounts(available_only=only_available)
                data = SpotifyAccountSchema(many=True, exclude=["cache_path"]).dump(all_accounts)

            return data
        else:
            return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN
    