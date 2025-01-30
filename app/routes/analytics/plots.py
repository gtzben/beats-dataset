"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-05
"""
import os, spotipy, math, dash
from datetime import datetime
from dash import dcc, html, dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import numpy as np
import pandas as pd

import plotly.express as px
from plotly_calplot import calplot
from plotly.colors import sequential
import plotly.graph_objects as go

from app.routes.api.models.music import MusicListening
from app.routes.api.schemas.music import MusicListeningSchema

from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.schemas.spotify import SpotifyAccountSchema

from app.routes.api.models.participant import Participant
from app.routes.api.schemas.participant import ParticipantFlatSchema

from app.routes.api.models.survey import Response

# Function to map percentage to a color
def get_color_scale(value):
    """
    Map percentage string (e.g., '50%') to a color on the Greens color scale.
    """
    greens = sequential.Greens  # Access the predefined Greens scale
    scale_position = float(value.strip('%')) / 100  # Normalize percentage (0 to 1)
    idx = int(scale_position * (len(greens) - 1))  # Map scale position to index
    return greens[idx]  # Return the corresponding color


def create_bar_chart(df):

    counts_df = (df.groupby("participant_id", as_index=False)["context"]
                 .value_counts()
                 .sort_values(by="participant_id"))
    
    barplot = px.bar(
        counts_df,
        x="participant_id",
        y="count",
        color="context",
        text_auto=True,
        color_discrete_map={"Affective":"coral",
                        "Eudaimonic":"royalblue",
                        "Goal-Attainment":"lightgreen",
                        "Other":"mediumpurple"}
    )

    barplot.update_layout(
        xaxis_title='Participant ID',
        yaxis_title='Counts',
        title='Number of Songs Listened by Participants',
        template="plotly_white"
    )

    return barplot

def create_radial_barchart(df, account, context):

    # Step 1
    df_hourly_counts = df.copy()
    df_hourly_counts["hour"] = pd.to_datetime(df_hourly_counts["started_at"], format="ISO8601").dt.hour
    df_hourly_counts["account_email"] = df_hourly_counts["account_email"].apply(lambda x: x.split("@")[0])
    df_hourly_counts = df_hourly_counts.groupby(["hour", "account_email", "context"]).size().reset_index(name='n_tracks')
    df_hourly_counts.set_index("hour", inplace=True)

    # Step 2: Create a complete index of hours for each participant and context
    accounts = df_hourly_counts["account_email"].unique()
    contexts = df_hourly_counts["context"].unique()
    all_hours = list(range(0,24))

    # Step 4: Create a MultiIndex of all possible combinations
    index = pd.MultiIndex.from_product(
        [all_hours, accounts, contexts],
        names=["hour", "account_email", "context"]
    )

    # Step 5: Reindex the dataset
    df_hourly_counts = df_hourly_counts.reset_index().set_index(["hour", "account_email", "context"])
    df_hourly_counts = df_hourly_counts.reindex(index, fill_value=0).reset_index()

    # Step 6:
    colour_mapping = {"Affective":"blues",
                        "Eudaimonic":"oranges",
                        "Goal-Attainment":"greens",
                        "Other":"purples"}
    if account == "All":
        df_subset = (df_hourly_counts.groupby(["hour", "context"])[["n_tracks"]].sum()
                    .query(f"context=='{context}'")
                    .reset_index()
                    .copy())
    else:
        df_subset = df_hourly_counts.query(f"account_email == '{account}' & context=='{context}'").copy()

    r = df_subset['n_tracks'].tolist()
    theta = np.arange(7.5,368,15)
    width = [15]*24
    colorscale = colour_mapping.get(context, "blues")  # Default to "blues" if context not in mapping

    # Adjusting tick texts
    ticktexts = [f"<b>{i}</b>" if i % 6 == 0 else "" for i in np.arange(24)]

    # Create radial bar plot
    radial_chart = go.Figure(go.Barpolar(
        r=r,
        theta=theta,
        width=width,
        marker_color=r,
        marker_colorscale=colorscale,
        marker_line_color="white",
        marker_line_width=2,
        opacity=0.8,
        hoverinfo='text',  # Custom hover text
        text=[f"Hour: {hour}<br>n_tracks: {n}" for hour, n in zip(df_subset['hour'], r)]
    ))

    # Update layout
    radial_chart.update_layout(
        template=None,
        polar=dict(
            hole=0.4,
            bgcolor='rgb(223, 223, 223)',
            radialaxis=dict(
                showticklabels=False,
                ticks='',
                linewidth=2,
                linecolor='white',
                showgrid=False,
            ),
            angularaxis=dict(
                tickvals=np.arange(0, 360, 15),
                ticktext=ticktexts,
                showline=True,
                direction='clockwise',
                period=24,
                linecolor='white',
                gridcolor='white',
                showticklabels=True,
                ticks=''
            )
        ),
        title=f"Counts Listened Tracks per Hour",
    )

    return radial_chart

def create_calendar_heatmap(df, account, context):

    # Step 1:
    df_daily_counts = df.copy()
    df_daily_counts["started_at"] = pd.to_datetime(df_daily_counts["started_at"], format='ISO8601').dt.date
    df_daily_counts["account_email"] = df_daily_counts["account_email"].apply(lambda x: x.split("@")[0])
    df_daily_counts = df_daily_counts.groupby(["started_at", "account_email", "context"]).size().reset_index(name='n_tracks')
    df_daily_counts.set_index("started_at", inplace=True)

    # Step 2: Create a complete index of dates for each participant and context
    accounts = df_daily_counts["account_email"].unique()
    contexts = df_daily_counts["context"].unique()
    all_dates = pd.date_range(df_daily_counts.index.min(), pd.to_datetime("today").normalize())

    # Step 4: Create a MultiIndex of all possible combinations
    index = pd.MultiIndex.from_product(
        [all_dates, accounts, contexts],
        names=["started_at", "account_email", "context"]
    )

    # Step 5: Reindex the dataset
    df_daily_counts = df_daily_counts.reset_index().set_index(["started_at", "account_email", "context"])
    df_daily_counts = df_daily_counts.reindex(index, fill_value=0).reset_index()

    # Step 6:
    colour_mapping = {"Affective":"blues",
                      "Eudaimonic":"oranges",
                      "Goal-Attainment":"greens",
                      "Other":"purples"}
    
    if account == "All":
        df_subset = (df_daily_counts.groupby(["started_at", "context"])[["n_tracks"]].sum()
                    .query(f"context=='{context}'")
                    .reset_index()
                    .copy())
    else:
        df_subset = df_daily_counts.query(f"account_email == '{account}' & context=='{context}'").copy()

    # creating the plot
    cal_heatmap = calplot(
            df_subset,
            x="started_at",
            y="n_tracks",
            colorscale = colour_mapping[context],
            name="n_tracks",
            month_lines_width=2,
            gap=5,
            dark_theme=False,
            years_title=True
    )

    return cal_heatmap


def create_table_progress(server, df, participants, progress_tracking):
    
    participants_id = list(participants["id"])
    default_table = pd.DataFrame(0, index=participants_id, columns=list(progress_tracking.keys()))

    try:
        table = (df.groupby(["participant_id", "context"])["track_uri"]
                .apply(lambda x: len(x.unique()))
                .reset_index(name="counts")
                .pivot_table(index="participant_id", columns="context", values="counts")
                .fillna(0)
                .drop("Other",axis=1))
        table = pd.concat([table, default_table[~default_table.index.isin(table.index)].dropna()])
    except Exception as e:
        server.logger.error(f"Error while obtaining participants progress: {e}")
        table = default_table.copy()
    table["Participation Time"] = ((datetime.today() - participants.set_index("id")["created_at"])).clip(upper=progress_tracking["Participation Time"])

    table = (table.div(pd.Series(progress_tracking)).applymap(lambda x: f"{x*100:,.2f}%")
         .reset_index()
         .rename(columns={'index': 'PID'}))
    
    percentage_values = set(
        float(cell.strip('%')) for col in table.columns[1:] for cell in table[col] if isinstance(cell, str)
    )

    # Generate conditional styles
    style_data_conditional = []
    for col in table.columns[1:]:  # Skip the first column (PID)
        for value in percentage_values:
            style_data_conditional.append({
                "if": {"column_id": col, "filter_query": f'{{{col}}} = "{value:.2f}%"'},
                "backgroundColor": get_color_scale(f"{value:.2f}%"),
                "color": "black" if float(value) < 50 else "white"  # Ensure text contrast
                
            })

    # Convert data to Dash-friendly format
    data_records = table.to_dict("records")
    columns = [{"name": col, "id": col} for col in table.columns]

    return data_records, columns, style_data_conditional


def create_hist(df, bin_width=20):
    
    #
    df_session = df.copy()

    #
    df_session['started_at'] = pd.to_datetime(df['started_at'], format='ISO8601')
    df_session['ended_at'] = pd.to_datetime(df['ended_at'], format='ISO8601')
    df_session["duration_min"] =  (df_session['ended_at'] - df_session['started_at'])/pd.Timedelta('60s')

    #
    duration_sesisons = df_session.groupby(['listening_session_id',"participant_pid", "context"])["duration_min"].sum().reset_index(name="total_minutes")

    #
    nbins = math.ceil((duration_sesisons["total_minutes"].max() - duration_sesisons["total_minutes"].min()) / bin_width)
    hist = px.histogram(
            duration_sesisons, x="total_minutes", color="context", color_discrete_map={"Affective":"coral",
                        "Eudaimonic":"royalblue",
                        "Goal-Attainment":"lightgreen",
                        "Other":"mediumpurple"},
            
            marginal="box", nbins=nbins,
            range_x=[-10, duration_sesisons["total_minutes"].max()+30 ], 
            histnorm='density'  # Normalize to density
    )

    # Customize axes
    hist.update_layout(
        xaxis_title='Total Minutes',
        yaxis_title='Density',
        title='Distribution of Total Minutes by Context',
        template="plotly_white"
    )
    
    return hist


# TIPI scoring function
def score_tipi(df_grouped):
    """
    Compute TIPI scores for participant. 
    Five Personality Traits:

    Extraversion (EXT): 1 and 6R
    Agreeableness (AGR): 2R and 7
    Conscientiousness (CON): 3 and 8R
    Emotional Stability (ES): 4R and 9
    Openness (OPN): 5 and 10R

    Reverse score: recode a 7 with a 1, a 6 with a 2, a 5 with a 3, etc.)
    """

    # Define scoring logic
    tipi_scores = {
        ("TIPI", "EXT"): lambda df: (df.loc[df["item"] == 1, "response"].values[0] +
                           (8 - df.loc[df["item"] == 6, "response"].values[0])) / 2,
        ("TIPI", "AGR"): lambda df: (df.loc[df["item"] == 7, "response"].values[0] +
                           (8 - df.loc[df["item"] == 2, "response"].values[0])) / 2,
        ("TIPI", "CON"): lambda df: (df.loc[df["item"] == 3, "response"].values[0] +
                           (8 - df.loc[df["item"] == 8, "response"].values[0])) / 2,
        ("TIPI","ES"): lambda df: (df.loc[df["item"] == 9, "response"].values[0] +
                           (8 - df.loc[df["item"] == 4, "response"].values[0])) / 2,
        ("TIPI","OPN"): lambda df: (df.loc[df["item"] == 5, "response"].values[0] +
                           (8 - df.loc[df["item"] == 10, "response"].values[0])) / 2,
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    # Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in tipi_scores.items()}
    return scores


def score_panas(df_grouped):
    """
    Compute PANAS scores.
    Postive Affect Score (PAS): 1, 3, 5, 9, 10, 12, 14, 16, 17, 19
    Negative Affect Score (NAS): 2, 4, 6, 7, 8, 11, 13, 15, 18, 20

    """

    panas_scores = {
        ("PANAS","PAS"): lambda df: df.loc[df["item"].isin([1, 3, 5, 9, 10, 12, 14, 16, 17, 19])]["response"].sum(),
        ("PANAS", "NAS"): lambda df: df.loc[df["item"].isin([2, 4, 6, 7, 8, 11, 13, 15, 18, 20])]["response"].sum()
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in panas_scores.items()}

    return scores


def score_stompr(df_grouped):
    """
    Compute STOMP-R scores.
    Four broad music-preference dimensions:

    Reflective & Complex (RC): 2, 3, 4, 7, 11, 12, 13, 15
    Intense & Rebellious (IR): 1, 10, 17, 21
    Upbeat & Conventional (UC): 5, 9, 14, 16, 20, 23
    Energetic & Rhythmic (ER): 6, 8, 18, 19, 22

    """

    stompr_scores = {
        ("STOMPR","RC"): lambda df: df.loc[df["item"].isin([2, 3, 4, 7, 11, 12, 13, 15])]["response"].mean().round(2),
        ("STOMPR", "IR"): lambda df: df.loc[df["item"].isin([1, 10, 17, 21])]["response"].mean().round(2),
        ("STOMPR", "UC"): lambda df: df.loc[df["item"].isin([5, 9, 14, 16, 20, 23])]["response"].mean().round(2),
        ("STOMPR", "ER"): lambda df: df.loc[df["item"].isin([6, 8, 18, 19, 22])]["response"].mean().round(2)
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in stompr_scores.items()}

    return scores


def score_gms(df_grouped):
    """
    Compute Goldsmiths scores.
    Five independent dimensions and one overal score:

    Active Engagement (AE): 1, 3, 8, 15, 21, 24, 28, 34, 38
    Perceptual Abilities (PA): 5, 6, 11, 12, 13, 18, 22, 23, 26
    Musical Training (MT): 14, 27, 32, 33, 35, 36, 37
    Singing Abilities (SA): 4, 7, 10, 17, 25, 29, 30
    Emotions (EMO): 2, 9, 16, 19, 20, 31

    General Sophistication (GS): 1, 3, 4, 7, 10, 12, 14, 15, 17, 19, 23, 24, 25, 27, 29, 32, 33, 37

    Categorial Items: 32, 33, 34, 35, 36 37, 38 
    Reverse-scored items: 9, 11, 13, 14, 17, 21, 23, 25, 27
    """

    gsm_cat = {32: ["0", "1", "2", "3", "4-5", "6-9", "10 or more"],
               33: ["0", "0.5", "1", "1.5", "2", "3-4", "5 or more"],
               34: ["0", "1", "2", "3", "4-6", "7-10", "11 or more"],
               35: ["0", "0.5", "1", "2", "3", "4-6", "7 or more"],
               36: ["0", "0.5", "1", "2", "3-5", "6-9", "10 or more"],
               37: ["0", "1", "2", "3", "4", "5", "6 or more"],
               38: ["0-15 min", "15-30 min", "30-60 min", "60-90 min", "2 hrs", "2-3 hrs", "4 hrs or more"]} 

    gms_scores = {
        ("GMS","AE"): lambda df_num, df_cat: (df_num[df_num["item"].isin([1, 3, 8, 15, 24, 28])]["response"].sum() +
                                     (8 - df_num[df_num["item"].isin([21])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [34,38] ])),
                                           
        ("GMS", "PA"): lambda df_num, _: (df_num.loc[df_num["item"].isin([5, 6, 12, 18, 22, 26])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([11, 13, 23])]["response"]).sum() ),

        ("GMS", "MT"): lambda df_num, df_cat: ((8 - df_num[df_num["item"].isin([14, 27])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [32, 33, 35, 36, 37] ])),


        ("GMS", "SA"): lambda df_num, _: (df_num.loc[df_num["item"].isin([4, 7, 10, 29, 30])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([17, 25])]["response"]).sum() ),

        ("GMS", "EMO"): lambda df_num, _: (df_num.loc[df_num["item"].isin([2, 16, 19, 20, 31])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([9])]["response"]).sum() ),

        ("GMS", "GS"): lambda df_num, df_cat: (df_num[df_num["item"].isin([1, 3, 4, 7, 10, 12, 15, 19, 24, 29])]["response"].sum() +
                                     (8 - df_num[df_num["item"].isin([14, 17, 23, 25, 27])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [32,33,37] ])),
    }

    # Separate categorical and numerical items in different dataframes
    df_grouped_num = df_grouped.sort_values(by="item").iloc[:-8].copy()
    df_grouped_num["response"] = df_grouped_num["response"].astype(int)
    df_grouped_cat = df_grouped.sort_values(by="item").iloc[-8:-1].copy()

    #Calculate scores
    scores = {dimension: score_func(df_grouped_num, df_grouped_cat) for dimension, score_func in gms_scores.items()}

    return scores


def get_scores_psychometrics(df_answers):
    """

    """

    questionnaire_scoring = {"tipi":score_tipi, "panas":score_panas,
                             "stompr":score_stompr, "gms": score_gms}

    grouped = df_answers.groupby("participant_id")

    # Iterate questionnares scoring functions and 
    # participants
    scores_all = []
    for name, group in grouped:
        scores_participant = {"ID": name}
        for survey, func_score in questionnaire_scoring.items():
            # Get respones for items of current questionnaire and participant
            group_survey = group[group["questionnaire"]==survey].copy()
            survey_scores = func_score(group_survey)
            scores_participant = {**scores_participant, **survey_scores}
        # Include all in same list    
        scores_all.append(scores_participant)

    #
    df_scores_all = pd.DataFrame(scores_all)
    df_scores_all.set_index("ID", inplace=True)
    df_scores_all.columns = pd.MultiIndex.from_tuples(df_scores_all.columns, names=["QUEST", "DIM"])

    #
    df_scores_all.reset_index(inplace=True)
    scores_columns = [{"name": list(col), "id": "".join(col)} for col in df_scores_all.columns]
    df_scores_all.columns = [''.join(col) for col in df_scores_all.columns]
    scores_records = df_scores_all.to_dict("records")

    return scores_records, scores_columns

def top_tracks_listened(df_music_hist):

    df_top = (
        df_music_hist.groupby(['track_name','context', 'track_uri'])  # Include song_name in grouping
        .agg(
            n_listens=('track_uri', 'size'),
            unique_par=('participant_id', pd.Series.nunique)
        )
        .reset_index()
        .sort_values(['context', 'n_listens'], ascending=[True, False])  # Sort by context and listens
        .groupby('context')  # Group by context again to get the top 3 tracks
        .head(3)
        .drop(columns=['track_uri'])
    )

    top_records = df_top.to_dict("records")
    top_columns = [{"name": col, "id": col} for col in df_top.columns]

    return top_records, top_columns



def create_all_charts(server, participation_progress, account, context, full_track_only=True):
    
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
                survey_record = {"participant_id": par["id"], "questionnaire":question.questionnaire_name, "item":question.n_item, "response":response.response}
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
    df_responses["participant_id"] = df_responses["participant_id"].apply(lambda x: f"P{str(x).zfill(2)}")
    df_responses = (pd.merge(df_responses, df_participants.rename({"id":"participant_id", "pid":"participant_pid"}, axis=1),
                            on="participant_id", how="inner"))

    # df_music_history.to_csv("music_sample.csv", index=False)
    # df_participants.to_csv("participant_sample.csv", index=False)
    # df_responses.to_csv("survey_sample.csv", index=False)

    if full_track_only:
        df_music_history = df_music_history[df_music_history["playback_inconsistency"]==0] 

    bar_chart = create_bar_chart(df_music_history)
    radial_barchart = create_radial_barchart(df_music_history, account, context)
    calendar_heatmap = create_calendar_heatmap(df_music_history, account, context)
    hist = create_hist(df_music_history)
    table_progress = create_table_progress(server, df_music_history, df_participants, participation_progress)
    table_scores = get_scores_psychometrics(df_responses)
    table_top_tracks = top_tracks_listened(df_music_history)



    return bar_chart, radial_barchart, calendar_heatmap, hist, table_progress, table_scores, table_top_tracks




def create_dash_app(server):

    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/analytics/',
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    dash_app.index_string =  """
                <!doctype html>
                <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>Insights From Data Collected</title>
                    <link
                        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
                        rel="stylesheet"
                        integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
                        crossorigin="anonymous">
                    <link rel="shortcut icon" href="http://127.0.0.1:5000/static/favicon.ico">
                </head>
                <body>
                    <nav class="navbar navbar-expand-lg" style="background-color: #003865;" data-bs-theme="dark">
                    <div class="container">
                        <a class="navbar-brand" href="https://www.gla.ac.uk">
                        <img src="/static/images/assets/logo.png" alt="The University of Glasgow" width="150" height="45">
                        </a>
                        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                            <span class="navbar-toggler-icon"></span>
                        </button>
                        <div class="collapse navbar-collapse" id="navbarSupportedContent">
                            <div class="navbar-nav">
                                <a class="nav-link active" aria-current="page" href="/">The BEATS Dataset</a>
                            </div>
                        </div>
                    </div>
                    </nav>
                    <div class="container mt-3">
                    <div id="dash-container">
                        {%app_entry%}
                    </div>
                    </div>
                    <footer class="text-center mt-4 py-3" style="background-color: #f8f9fa; color: #4f5961;">
                        <div class="container">
                            <p>&copy; 2024 The BEATS Dataset. All rights reserved.</p>
                        </div>

                        {%config%}
                        {%scripts%}
                        {%renderer%}

                    </footer>
                    <script
                        src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
                        integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
                        crossorigin="anonymous">
                    </script>
                </body>
                </html>
                """
    
    #
    with server.app_context():
        #
        accounts_obj = SpotifyAccount.get_all_accounts()
        accounts_email = (SpotifyAccountSchema(many=True, only=["account_email", "cache_path"]).dump(accounts_obj)).get("data")
        accounts_email = [item.get("account_email").split("@")[0] for item in accounts_email]

        # This chunk of code may require user intervention to loging to Spotify API 
        # ccm = spotipy.SpotifyClientCredentials(client_id=os.environ.get("SPOTIPY_CLIENT_ID"),client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET"))
        # sp_ccm = spotipy.Spotify(client_credentials_manager=ccm, requests_timeout=10, retries=10)
        # playlists_n_tracks = {value:sp_ccm.playlist(key)["tracks"]["total"] for key,value in server.config.get("STUDY_PLAYLISTS").items()}

    # Hardcoding track numbers per playlist as workaround
    # to avoid the script hanging  and waiting for authorization
    # playlists_n_tracks = {"Affective":170, "Eudaimonic":149,"Goal-Attainment":167}
    progress_tracking = {"Participation Time":pd.Timedelta(days=int(server.config.get("BATCH_PERIOD_DAYS"))), "Affective":170, "Eudaimonic":149,"Goal-Attainment":167}

    dash_app.layout = dbc.Container(
        [
            # Title Section
            dbc.Row(
                dbc.Col(
                    html.H1(
                        "Music Engagement Analytics: Participant Insights",
                        style={'textAlign': 'center', 'margin': '20px 0'}
                    )
                )
            ),
            dbc.Row(
                dbc.Col(
                    html.P(
                        "Explore trends and insights from participants' music listening habits. "
                        "Use the filters below to customize the analysis.",
                        style={'textAlign': 'center', 'fontSize': '18px'}
                    )
                )
            ),

            # ToggleSwitch Section
            dbc.Row(
                dbc.Col(
                    daq.ToggleSwitch(
                        id="toggle-switch",
                        label=["All Songs", "Stable Playback"],
                        value=True,
                        style={"margin": "10px", "textAlign": "center"}
                    ),
                    width={"size": 6, "offset": 3}
                ),
                className="mb-4"
            ),

            # Heatmap Filters
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            ["All"] + accounts_email,
                            "All",
                            clearable=False,
                            id="accounts-dropdown",
                            placeholder="Select an account"
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            ["Affective", "Eudaimonic", "Goal-Attainment", "Other"],
                            "Affective",
                            clearable=False,
                            id="context-dropdown",
                            placeholder="Select a context"
                        ),
                        width=6
                    )
                ],
                justify="center",
                className="mb-3"
            ),

            # Heatmap Calendar
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="heatmap-tracks-calendar", style={"height": "300px"}),
                    width=12
                ),
                className="mb-4"
            ),

            # Radial Bar Chart and Progress Table
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="hour-radial-barchart",
                            style={"height": "300px"}
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H4("Participants' Progress", style={"textAlign": "center", "margin": "0"})
                                ),
                                 dbc.CardBody(
                                        dash_table.DataTable(
                                            id="table-progress",
                                            style_table={
                                                "maxHeight": "400px",
                                                "overflowY": "auto",
                                                "overflowX": "auto",
                                                "border": "thin lightgrey solid"
                                            },
                                            style_cell={
                                                "textAlign": "left",
                                                "padding": "5px",
                                                "whiteSpace": "normal"
                                            },
                                            style_header={"fontWeight": "bold"}
                                        ),
                                    )
                                ]
                        ),              
                        width=6
                    )
                ],
                className="mb-4"
            ),

            # Scores Table and Top Table with Titles
            dbc.Row(
                [
                    # Scores Table
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H4("Psychometrics Scores", style={"textAlign": "center", "margin": "0"})
                                ),
                                dbc.CardBody(
                                    dash_table.DataTable(
                                        id="table-scores",
                                        style_table={
                                            "maxHeight": "400px",
                                            "overflowY": "auto",
                                            "overflowX": "auto",
                                            "border": "thin lightgrey solid"
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "5px",
                                            "whiteSpace": "normal"
                                        },
                                        style_header={"fontWeight": "bold"},
                                        merge_duplicate_headers=True,
                                    )
                                )
                            ]
                        ),
                        width=6
                    ),
                    # Top Table
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H4("Top Tracks Listened", style={"textAlign": "center", "margin": "0"})
                                ),
                                dbc.CardBody(
                                    dash_table.DataTable(
                                        id="table-top",
                                        style_table={
                                            "maxHeight": "400px",
                                            "overflowY": "auto",
                                            "overflowX": "auto",
                                            "border": "thin lightgrey solid"
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "5px",
                                            "whiteSpace": "normal"
                                        },
                                        style_header={"fontWeight": "bold"}
                                    )
                                )
                            ]
                        ),
                        width=6
                    )
                ],
                className="mb-4"
            ),

            # Histogram
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="hist-time-context", style={"height": "400px"}),
                    width=12
                ),
                className="mb-4"
            ),

            # Bar Chart
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="counts-song-participants"),
                    width=12
                ),
                className="mb-4"
            )
        ],
        fluid=True,
        style={"padding": "20px"}
    )


    @dash_app.callback(
        [
            Output("counts-song-participants", "figure"),
            Output("hour-radial-barchart", "figure"),
            Output("heatmap-tracks-calendar", "figure"),
            Output("hist-time-context", "figure"),
            Output("table-progress", "data"),
            Output("table-progress", "columns"),
            Output("table-progress", "style_data_conditional"),
            Output("table-scores", "data"),
            Output("table-scores", "columns"),
            Output("table-top", "data"),
            Output("table-top", "columns")
        ],
        [
            Input("toggle-switch", "value"),
            Input("accounts-dropdown", "value"),
            Input("context-dropdown", "value")
        ]
    )
    def update_graph(playback_bool, account, context):
        # Generate updated charts and tables
        barchart, radial, heatmap, hist, table_progress, table_scores, table_top = create_all_charts(
            server, progress_tracking, account, context, playback_bool
        )

        # Unpack progress table data
        data_progress, columns_progress, style_data_conditional = table_progress

        # Unpack scores and top table data
        data_scores, columns_scores = table_scores
        data_top, columns_top = table_top

        print(type(barchart))

        return (
            barchart,
            radial,
            heatmap,
            hist,
            data_progress,
            columns_progress,
            style_data_conditional,
            data_scores,
            columns_scores,
            data_top,
            columns_top
        )

    
    return dash_app