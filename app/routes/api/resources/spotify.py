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
        spotify = spotipy.Spotify(auth_manager=auth_manager)

        if SpotifyAccount.get_by_email(email=spotify.me()['email']):
            return {'message': 'This account has already been connected'}, HTTPStatus.BAD_REQUEST

        self.logger.debug(f"{spotify.me()['email']} has login successuly to Spotify")

        data = {"account_email": spotify.me()["email"],
                "uri": spotify.me()["uri"],
                "cache_path": cache_path}
        
        spotify_account = SpotifyAccount(**data)
        spotify_account.save()

        flash(f"Successfully connected spotify account: {spotify.me()['email']}", "success")

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
    