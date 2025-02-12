"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-02-07
"""
import math
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly_calplot import calplot

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_bar_chart(df):
    """
    
    """

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

def create_radial_barchart(df, account, context, avail_accounts, avail_contexts):
    """
    
    """

    # Step 1
    df_hourly_counts = df.copy()
    df_hourly_counts["hour"] = pd.to_datetime(df_hourly_counts["started_at"], format="ISO8601").dt.hour
    df_hourly_counts["account_email"] = df_hourly_counts["account_email"].apply(lambda x: x.split("@")[0])
    df_hourly_counts = df_hourly_counts.groupby(["hour", "account_email", "context"]).size().reset_index(name='n_tracks')
    df_hourly_counts.set_index("hour", inplace=True)

    # Step 2: Create a complete index of hours for each participant and context
    all_hours = list(range(0,24))

    # Step 3: Create a MultiIndex of all possible combinations
    index = pd.MultiIndex.from_product(
        [all_hours, avail_accounts, avail_contexts],
        names=["hour", "account_email", "context"]
    )

    # Step 4: Reindex the dataset
    df_hourly_counts = df_hourly_counts.reset_index().set_index(["hour", "account_email", "context"])
    df_hourly_counts = df_hourly_counts.reindex(index, fill_value=0).reset_index()

    # Step 5: Select subset account
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


def create_barcharts_demo(df_responses):
    """

    """

    # Dictionary of demographic variables
    demo_vars = {
        "Gender": 1,  
        "Age Group": 3,  
        "Ethnicity": 4,  
        "Employment": 10,  
        "Workplace": 13,  
        "People Nearby": 15,  
        "Tech Proficiency": 20,  
        "Non-Dom Hand": 21,  
        "Streaming Likely": 24,  
        "Main Streaming": 25
    }

    # Define number of rows and columns for subplots
    num_vars = len(demo_vars)
    cols = 5  # Set number of columns
    rows = (num_vars + cols - 1) // cols  # Calculate required rows

    # Create subplots
    bar_charts_demo = make_subplots(
        rows=rows, cols=cols, 
        subplot_titles=list(demo_vars.keys())
    )

    # Loop through demographic variables and add bar plots
    for idx, (demo_name, demo_id) in enumerate(demo_vars.items()):
        row = (idx // cols) + 1
        col = (idx % cols) + 1

        # Filter responses for the current demographic variable
        data = df_responses[(df_responses["questionnaire"] == "demo") & 
                            (df_responses["item"] == demo_id)]
        
        # Create bar plot
        count_data = data["response"].value_counts()
        bar_plot = go.Bar(x=count_data.index, y=count_data.values, text=count_data.values, textposition='auto')

        # Add trace to subplot
        bar_charts_demo.add_trace(bar_plot, row=row, col=col)
        bar_charts_demo.update_traces(hoverinfo="none", hovertemplate=None)
        

    # Update layout
    bar_charts_demo.update_layout(
        height=600, width=1100, # Update size accordingly
        title_text="Demographics Participants",
        template="plotly_white",
        showlegend=False, bargap=0.3
    )

    return bar_charts_demo


def create_calendar_heatmap(df, account, context, avail_accounts, avail_contexts):
    """
    
    """

    # Step 1:
    df_daily_counts = df.copy()
    df_daily_counts["started_at"] = pd.to_datetime(df_daily_counts["started_at"], format='ISO8601').dt.date
    df_daily_counts["account_email"] = df_daily_counts["account_email"].apply(lambda x: x.split("@")[0])
    df_daily_counts = df_daily_counts.groupby(["started_at", "account_email", "context"]).size().reset_index(name='n_tracks')
    df_daily_counts.set_index("started_at", inplace=True)

    # Step 2: Create a complete index of dates for each participant and context
    all_dates = pd.date_range(df_daily_counts.index.min(), pd.to_datetime("today").normalize())

    # Step 3: Create a MultiIndex of all possible combinations
    index = pd.MultiIndex.from_product(
        [all_dates, avail_accounts, avail_contexts],
        names=["started_at", "account_email", "context"]
    )

    # Step 4: Reindex the dataset
    df_daily_counts = df_daily_counts.reset_index().set_index(["started_at", "account_email", "context"])
    df_daily_counts = df_daily_counts.reindex(index, fill_value=0).reset_index()

    # Step 5: Select subset account
    if account == "All":
        df_subset = (df_daily_counts.groupby(["started_at", "context"])[["n_tracks"]].sum()
                    .query(f"context=='{context}'")
                    .reset_index()
                    .copy())
    else:
        df_subset = df_daily_counts.query(f"account_email == '{account}' & context=='{context}'").copy()

    colour_mapping = {"Affective":"blues",
                      "Eudaimonic":"oranges",
                      "Goal-Attainment":"greens",
                      "Other":"purples"}

    # Step 6: Creating the plot
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

