"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-02-07
"""

import numpy as np
import pandas as pd
from datetime import datetime
from plotly.colors import sequential

from app.routes.analytics.visualizations import scoring



# Function to map percentage to a color
def get_color_scale(value):
    """
    Map percentage string (e.g., '50%') to a color on the Greens color scale.
    """
    greens = sequential.Greens  # Access the predefined Greens scale
    scale_position = float(value.strip('%')) / 100  # Normalize percentage (0 to 1)
    idx = int(scale_position * (len(greens) - 1))  # Map scale position to index
    return greens[idx]  # Return the corresponding color



def create_table_progress(server, df, participants, progress_tracking):
    
    participants_id = list(participants["id"])
    default_table = pd.DataFrame(0, index=participants_id, columns=list(progress_tracking.keys()))

    try:
        table = (df.groupby(["participant_id", "context"])["track_uri"]
                .apply(lambda x: len([t for t in x.unique() if t in progress_tracking.get(x.name[-1],[])]))
                .reset_index(name="counts")
                .pivot_table(index="participant_id", columns="context", values="counts")
                .fillna(0)
                .drop("Other",axis=1, errors="ignore"))
        # If context not listened by active participants, turn NaNs to 0
        table = pd.concat([table, default_table[~default_table.index.isin(table.index)].dropna()]).fillna(0)
    except Exception as e:
        server.logger.error(f"Error while obtaining participants progress: {e}")
        table = default_table.copy()

    table["Participation Time"] = ((datetime.today() - participants.set_index("id")["created_at"])).clip(upper=progress_tracking["Participation Time"])

    # Replace when fixed issue with spotify hanging request
    progress_tracking_len = {key:(len(value) if hasattr(value, "__iter__") else value) for key, value in progress_tracking.items()} 

    # If unable to fetch tracks uris, progress of functions will show 0
    table = (table.div(pd.Series(progress_tracking_len).replace(0,np.nan).astype(object))
         .fillna(0)
         .applymap(lambda x: f"{x*100:,.2f}%")
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


def get_scores_psychometrics(df_answers):
    """

    """

    questionnaire_scoring = {"tipi":scoring.score_tipi, "panas":scoring.score_panas,
                             "pss":scoring.score_pss,"phq9":scoring.score_phq9,
                             "stompr":scoring.score_stompr, "gms": scoring.score_gms}

    grouped = df_answers.groupby("participant_id")

    # Iterate questionnares scoring functions and 
    # participants
    scores_all = []
    for name, group in grouped:
        scores_participant = {"ID": name}

        # Identify distinct timestamps for pre/post classification
        unique_times = sorted(group["response_created_at"].unique())

        if len(unique_times) == 1:
            pre_time = unique_times[0]
            post_time = None  # No post-study responses yet
        elif len(unique_times) >= 2:
            pre_time = unique_times[0]
            post_time = unique_times[1]  # Take the second timestamp as post-study

        for survey, func_score in questionnaire_scoring.items():
            # Get respones for items of current questionnaire and participant
            group_survey = group[group["questionnaire"]==survey].copy()

            if survey in ["panas", "pss", "phq9"]:
                # Separate pre-study and post-study responses
                pre_study = group_survey[group_survey["response_created_at"] == pre_time].copy()
                post_study = group_survey[group_survey["response_created_at"] == post_time].copy() if post_time else pd.DataFrame()

                # Compute scores separately
                if not pre_study.empty:
                    pre_scores = func_score(pre_study, pre_study=True)
                    scores_participant = {**scores_participant, **pre_scores}

                if not post_study.empty:
                    post_scores = func_score(post_study, pre_study=False)
                    scores_participant = {**scores_participant, **post_scores}
                else:
                    # Ensure post-study columns exist but are empty
                    for key in func_score(pd.DataFrame(columns=group_survey.columns), pre_study=False).keys():
                        scores_participant[key] = None
            
            else:
                # Compute scores normally for other questionnaires
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