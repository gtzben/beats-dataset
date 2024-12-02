import os, click, logging
from datetime import datetime

from app.routes.api.models.user import User
from app.routes.api.models.participant import Participant
from app.routes.api.models.spotifyaccount import SpotifyAccount

from app.routes.api.resources.spotify import cache_dir

from flask.cli import with_appcontext

#
LOGGER =logging.getLogger("scheduled_monitoring")

def __setup_logger(daily_log_path):
    """
    
    """

    global LOGGER

    #
    LOGGER.setLevel(logging.DEBUG)

    #
    file_handler = logging.FileHandler(daily_log_path)

    # Create formatters and add them to handlers
    formatter = logging.Formatter("[%(levelname)s] - [%(asctime)s.%(msecs)03d] - %(name)s - %(filename)s:%(lineno)s - %(funcName)s(): message: %(message)s",
                                   datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    #
    LOGGER.addHandler(file_handler)

    return


@with_appcontext
def purge_cache_and_not_verified(max_days_users=1, max_days_participants = 21):
    """
    Delete users and participants whose account was not verified, as well as cache files not
    associated to Spotify accounts in DB
    """

    not_verified_users = User.get_all_users(is_verified=False)
    not_verified_participants = Participant.get_all_participants(is_verified=False)
    valid_cache_spotify = [account.cache_path for account in SpotifyAccount.get_all_accounts()]
    all_cache_spotify = [os.path.join(cache_dir,cache) for cache in os.listdir(cache_dir) if cache.startswith(".cache-")]

    for user in not_verified_users:
        delta_days = (datetime.now()-user.created_at).days
        if delta_days >= max_days_users:
            user.delete()
            LOGGER.debug(f"User {user.email} was deleted from db since email verification expired")

    for participant in not_verified_participants:
        delta_days = (datetime.now()-participant.created_at).days
        if delta_days >= max_days_participants:
            participant.delete()
            LOGGER.debug(f"Participant {participant.pid} was deleted from db since email verification expired")
    
    removed_cache=0
    for cache in all_cache_spotify:
        if cache not in valid_cache_spotify:
            os.remove(cache)
            removed_cache+=1
    LOGGER.debug(f"Removed {removed_cache} cache files not linked to Spotify accounts in DB")


@click.command()
def run_daily_jobs():
    """
    Execute daily jobs
    """
    #
    daily_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs", f"daily_jobs.log")
    __setup_logger(daily_log_path)

    #
    purge_cache_and_not_verified()

        
