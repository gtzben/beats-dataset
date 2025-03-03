"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-05
"""
import dash
import dash_daq as daq
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.schemas.spotify import SpotifyAccountSchema

from app.routes.analytics.callbacks import register_callbacks


def create_dash_app(server):
    """
    
    """

    avail_contexts = ["Affective", "Eudaimonic", "Goal-Attainment", "Other"]

    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/analytics/',
        suppress_callback_exceptions=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    dash_app.index_string = """
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
        accounts_dict = (SpotifyAccountSchema(many=True, only=["account_email", "cache_path"]).dump(accounts_obj)).get("data")
        avail_accounts = [item.get("account_email").split("@")[0] for item in accounts_dict]

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
                [dbc.Col(
                    daq.ToggleSwitch(
                        id="toggle-switch",
                        label=["All Songs", "Stable Playback"],
                        value=True,
                        style={"margin": "10px", "textAlign": "center"}
                    ),
                    width={"size": 6, "offset": 3}
                ),
                dcc.Store(id="data-store")],  # Stores fetched data,
                className="mb-4"
            ),

            # Heatmap Filters
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            ["All"] + avail_accounts,
                            "All",
                            clearable=False,
                            id="accounts-dropdown",
                            placeholder="Select an account"
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            avail_contexts,
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

            # Barcharts Subplots
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="barcharts-subplot-demo", style={"height": "700px"}),
                    width=12
                ),
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

    # Register callbacks
    register_callbacks(dash_app, server, avail_accounts, avail_contexts, server.config["PROGRESS_TRACKING"])