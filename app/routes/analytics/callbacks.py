"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-02-07
"""

import json

import pandas as pd

from dash.dependencies import Input, Output

from app.routes.api.models.survey import Response
from app.routes.api.models.music import MusicListening
from app.routes.api.models.participant import Participant

from app.routes.api.schemas.music import MusicListeningSchema
from app.routes.api.schemas.participant import ParticipantFlatSchema

from app.routes.analytics.visualizations.tables import create_table_progress, get_scores_psychometrics, top_tracks_listened
from app.routes.analytics.visualizations.charts import (create_bar_chart, create_radial_barchart,
                                                         create_calendar_heatmap, create_hist, create_barcharts_demo)





def get_update_data_from_db(server, full_track_only=True):
    """
    
    """

    #
    with server.app_context():
        music_episodes = MusicListening().get_all_songs()
        music_data = (MusicListeningSchema(many=True).dump(music_episodes)).get("data")

        participant_obj = Participant.get_all_participants(is_verified=True)
        participant_data= (ParticipantFlatSchema(many=True, only=["id","pid","created_at","is_withdrawn"]).dump(participant_obj)).get("data")

        survey_data = []
        for par in participant_data:
            responses = Response.query.filter_by(participant_pid=par["pid"]).all()
            for response in responses:
                question = response.question
                survey_record = {"participant_id": par["id"], "questionnaire":question.questionnaire_name,
                                  "item":question.n_item, "response":response.response, "response_created_at":response.created_at}
                survey_data.append(survey_record)

    #
    df_participants = pd.DataFrame.from_records(participant_data).fillna(False)
    df_participants["id"] = df_participants["id"].apply(lambda x: f"P{str(x).zfill(2)}")
    df_participants["created_at"] = pd.to_datetime(df_participants["created_at"])
    # df_participants.loc[df_participants["id"]=="P02", "is_withdrawn"]=True # Simulate particpant withdrew
    df_participants = df_participants[df_participants["is_withdrawn"]==False].reset_index(drop=True).copy()

    #
    df_music_history = pd.DataFrame.from_records(music_data)
    df_music_history = (pd.merge(df_music_history, df_participants.rename({"id":"participant_id", "pid":"participant_pid"}, axis=1),
                        on="participant_pid", how="inner"))

    #
    df_responses = pd.DataFrame.from_records(survey_data)
    df_responses["response_created_at"] = pd.to_datetime(df_responses["response_created_at"])
    df_responses["participant_id"] = df_responses["participant_id"].apply(lambda x: f"P{str(x).zfill(2)}")
    df_responses = (pd.merge(df_responses, df_participants.rename({"id":"participant_id", "pid":"participant_pid"}, axis=1),
                            on="participant_id", how="inner"))
    
    # Save raw data for notebooks 
    # df_music_history.to_csv("music_sample_feb2.csv", index=False)
    # df_participants.to_csv("participant_sample_feb2.csv", index=False)
    # df_responses.to_csv("survey_sample_feb2.csv", index=False)

    if full_track_only:
        df_music_history = df_music_history[df_music_history["playback_inconsistency"]==0] 

    return df_music_history, df_participants, df_responses 



def register_callbacks(dash_app, server, avail_accounts, avail_contexts, progress_tracking):
    """Registers all callbacks for Dash app"""

    #
    @dash_app.callback(
        Output("data-store", "data"),
        [Input("toggle-switch", "value")]  # This ensures data updates when toggled
    )
    def fetch_and_store_data(playback_bool):
        """Fetches data once and stores it in dcc.Store"""
        data = get_update_data_from_db(server, playback_bool)

        # Convert data to JSON (Pandas DataFrames should be converted before storing)
        stored_data = {
            "music_history": data[0].to_json(),
            "participants": data[1].to_json(),
            "survey_data": data[2].to_json(),
        }

        return json.dumps(stored_data)
    
    #
    @dash_app.callback(
        Output("heatmap-tracks-calendar", "figure"),
        [Input("data-store", "data"), Input("accounts-dropdown", "value"), Input("context-dropdown", "value")]
    )
    def update_calendar_heatmap(stored_data, account, context):
        """Update calendar heatmap using stored data"""
        data = json.loads(stored_data)
        df_music_history = pd.read_json(data["music_history"])
        return create_calendar_heatmap(df_music_history, account, context, avail_accounts, avail_contexts)
    
    #
    @dash_app.callback(
        Output("hour-radial-barchart", "figure"),
        [Input("data-store", "data"), Input("accounts-dropdown", "value"), Input("context-dropdown", "value")]
    )
    def update_radial_chart(stored_data, account, context):
        """Update radial chart using stored data"""
        data = json.loads(stored_data)
        df_music_history = pd.read_json(data["music_history"])
        return create_radial_barchart(df_music_history, account, context, avail_accounts, avail_contexts)
    

    #
    @dash_app.callback(
        Output("barcharts-subplot-demo", "figure"),
        [Input("data-store", "data")]
    )
    def update_demo_barcharts(stored_data):
        """Update demographics subplots"""
        #
        data = json.loads(stored_data)
        
        #
        df_responses = pd.read_json(data["survey_data"])
        return create_barcharts_demo(df_responses)

    #
    @dash_app.callback(
        [
            Output("table-progress", "data"),
            Output("table-progress", "columns"),
            Output("table-progress", "style_data_conditional"),
        ],
        [Input("data-store", "data")]
    )
    def update_progress_table(stored_data):
        """Update radial chart using stored data"""
        #
        data = json.loads(stored_data)
        
        #
        df_music_history = pd.read_json(data["music_history"])
        df_participants = pd.read_json(data["participants"])

        #
        table_progress = create_table_progress(server, df_music_history, df_participants, progress_tracking)

        # Unpack progress table data
        data_progress, columns_progress, style_data_conditional = table_progress

        return data_progress, columns_progress, style_data_conditional
    
    #
    @dash_app.callback(
        [
            Output("table-scores", "data"),
            Output("table-scores", "columns"),
        ],
        [Input("data-store", "data")]
    )
    def update_psychometrics_table(stored_data):
        """Update radial chart using stored data"""
        #
        data = json.loads(stored_data)
        
        #
        df_responses = pd.read_json(data["survey_data"])

        #
        table_scores = get_scores_psychometrics(df_responses)

        # Unpack scores table data
        data_scores, columns_scores = table_scores

        return data_scores, columns_scores
    
    #
    @dash_app.callback(
        [
            Output("table-top", "data"),
            Output("table-top", "columns")
        ],
        [Input("data-store", "data")]
    )
    def update_topsongs_table(stored_data):
        """Update radial chart using stored data"""
        #
        data = json.loads(stored_data)
        
        #
        df_music_history = pd.read_json(data["music_history"])

        #
        table_top_tracks = top_tracks_listened(df_music_history)

        # Unpack scores table data
        data_top, columns_top = table_top_tracks

        return data_top, columns_top

    #
    @dash_app.callback(
        Output("hist-time-context", "figure"),
        [Input("data-store", "data")]
    )
    def update_hist_chart(stored_data):
        """Update bar chart using stored data"""
        data = json.loads(stored_data)
        df_music_history = pd.read_json(data["music_history"])
        return create_hist(df_music_history)
    
    #
    @dash_app.callback(
        Output("counts-song-participants", "figure"),
        [Input("data-store", "data")]
    )
    def update_bar_chart(stored_data):
        """Update bar chart using stored data"""
        data = json.loads(stored_data)
        df_music_history = pd.read_json(data["music_history"])
        return create_bar_chart(df_music_history)