"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-05
"""
import os, spotipy, math, dash
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

    counts_df = (df.groupby("participant_pid", as_index=False)["context"]
                 .value_counts()
                 .sort_values(by="context"))
    
    barplot = px.bar(
        counts_df,
        x="participant_pid",
        y="count",
        color="context",
        text_auto=True
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


def create_table(server, df, n_tracks_playlists):

    with server.app_context():
        participant_obj = Participant.get_all_participants(is_verified=True)
        participant_pid= (ParticipantFlatSchema(many=True, only=["pid"]).dump(participant_obj)).get("data")
        participant_pid = [item.get("pid") for item in participant_pid]
    
    default_table = pd.DataFrame(0, index=participant_pid, columns=list(n_tracks_playlists.keys()))

    try:
        table = (df.groupby(["participant_pid", "context"])["track_uri"]
                .apply(lambda x: len(x.unique()))
                .reset_index(name="counts")
                .pivot_table(index="participant_pid", columns="context", values="counts")
                .fillna(0)
                .drop("Other",axis=1))
        table = pd.concat([table, default_table[~default_table.index.isin(table.index)].dropna()])
    except Exception as e:
        server.logger.error(f"Error while obtaining participants progress: {e}")
        table = default_table.copy()

    table = (table.div(pd.Series(n_tracks_playlists)).applymap(lambda x: f"{x*100:,.2f}%")
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
            duration_sesisons, x="total_minutes", color="context", marginal="box", nbins=nbins,
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


def create_all_charts(server, counts_playlist_tracks, account, context, full_track_only=True):
    with server.app_context():
        music_episodes = MusicListening().get_all_songs()
        data = (MusicListeningSchema(many=True).dump(music_episodes)).get("data")

    df_music_history = pd.DataFrame.from_records(data)
    # df_music_history.to_csv("sample.csv", index=False)
    if full_track_only:
        df_music_history = df_music_history[df_music_history["playback_inconsistency"]==0] 

    bar_chart = create_bar_chart(df_music_history)
    radial_barchart = create_radial_barchart(df_music_history, account, context)
    calendar_heatmap = create_calendar_heatmap(df_music_history, account, context)
    table = create_table(server, df_music_history, counts_playlist_tracks)
    hist = create_hist(df_music_history)


    return bar_chart, radial_barchart, calendar_heatmap, table, hist




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
    playlists_n_tracks = {"Affective":170, "Eudaimonic":149,"Goal-Attainment":167}

    dash_app.layout = dbc.Container(
    [
        # Title Section
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Participant Music Engagement Insights",
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
                width={"size": 6, "offset": 3}  # Center align
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
        
        # Heatmap and Radial Bar Chart Section
        dbc.Row([
            # Radial Bar Chart
            dbc.Col(
                dcc.Graph(
                    id="hour-radial-barchart",
                    style={"height": "300px"}  # Adjust chart height
                ),
                width=3,
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"}  # Center vertically and horizontally
            ),
            
            # Heatmap Calendar
            dbc.Col(
                dcc.Graph(id="heatmap-tracks-calendar", style={"height": "300px"}),
                width=9
            )
        ], className="mb-4"),

        # Table and Histogram Section
        dbc.Row(
            [
                # Table Column
                dbc.Col(
                    dash_table.DataTable(
                        id="table-progress",
                        style_table={
                            "maxHeight": "400px",  # Reduce the height of the table row
                            "overflowY": "auto",   # Scrollable rows
                            "overflowX": "auto",   # Scrollable columns
                            "border": "thin lightgrey solid"
                        },
                        style_cell={
                            "textAlign": "left", 
                            "padding": "5px", 
                            "whiteSpace": "normal"
                        },
                        style_header={"fontWeight": "bold"}
                    ),
                    width=6
                ),

                # Histogram Column
                dbc.Col(
                    dcc.Graph(
                        id="hist-time-context",
                        style={"height": "400px"}  # Reduce the height of the histogram
                    ),
                    width=6
                )
            ],
            className="mb-4",
            style={"alignItems": "center"}  # Align contents vertically
        ),

        # Barchart Section
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
    [Output("counts-song-participants", "figure"), 
     Output("hour-radial-barchart", "figure"),
     Output("heatmap-tracks-calendar", "figure"),
     Output("hist-time-context", "figure"),
     Output("table-progress", "data"),
     Output("table-progress", "columns"),
     Output("table-progress", "style_data_conditional")
     ],[
     Input("toggle-switch", "value"),
     Input("accounts-dropdown", "value"), 
     Input("context-dropdown", "value")
     ] 
    )
    def update_graph(playback_bool, account, context):
        # Generate updated charts
        barchart, radial, heatmap, table, hist = create_all_charts(server, playlists_n_tracks,
                                              account, context, playback_bool)
        
        # Convert data to Dash-friendly format
        data_records, columns, style_data_conditional = table

        return barchart, radial, heatmap, hist, data_records, columns, style_data_conditional

    
    return dash_app