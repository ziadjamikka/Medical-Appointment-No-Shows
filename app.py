# app.py
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

df = pd.read_csv("KaggleV2-May-2016.csv")

df.columns = df.columns.str.strip().str.lower().str.replace('-', '_')

df['appointmentday'] = pd.to_datetime(df['appointmentday'])
df['scheduledday'] = pd.to_datetime(df['scheduledday'])
df['waiting_days'] = (df['appointmentday'] - df['scheduledday']).dt.days
df['day_of_week'] = df['appointmentday'].dt.day_name()

df['no_show_flag'] = df['no_show'].map({'No': 0, 'Yes': 1})

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])
server = app.server

sidebar = dbc.Card([
    html.H5("Filters", className="mb-3"),
    dbc.Label("Gender"),
    dcc.Dropdown(
        id="gender-filter",
        options=[{"label": g, "value": g} for g in sorted(df['gender'].unique())],
        value=[],
        multi=True
    ),
    dbc.Label("Age Range"),
    dcc.RangeSlider(
        id="age-slider",
        min=int(df['age'].min()),
        max=int(df['age'].max()),
        value=[0, 100],
        marks={0: "0", 50: "50", 100: "100"}
    ),
    html.Br(),
    dbc.Label("Neighborhood"),
    dcc.Dropdown(
        id="neighborhood-filter",
        options=[{"label": n, "value": n} for n in sorted(df['neighbourhood'].unique())],
        value=[],
        multi=True
    ),
    html.Br(),
    dbc.Button("Apply Filters", id="apply-btn", color="primary", className="w-100"),
    html.Hr(),
    dbc.Button("Download Filtered CSV", id="download-btn", color="secondary", className="w-100"),
    dcc.Download(id="download-data")
], body=True)

content = dbc.Container([
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Total Appointments"), html.H4(id="total-appointments")])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("No-Show Rate"), html.H4(id="no-show-rate")])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Avg Waiting Days"), html.H4(id="avg-waiting")])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Unique Patients"), html.H4(id="unique-patients")])), md=3)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="show-vs-noshow"), md=6),
        dbc.Col(dcc.Graph(id="age-distribution"), md=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="weekday-patterns"), md=6),
        dbc.Col(dcc.Graph(id="neighborhood-noshow"), md=6)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id="data-table",
            columns=[{"name": i, "id": i} for i in df.columns],
            page_size=10,
            filter_action="native",
            sort_action="native",
            style_table={"overflowX": "auto"}
        ), md=12)
    ])
], fluid=True)

app.layout = dbc.Container([
    html.H2("Medical Appointments Dashboard", className="my-3"),
    dbc.Row([
        dbc.Col(sidebar, md=3),
        dbc.Col(content, md=9)
    ])
], fluid=True)



def filter_data(gender, age_range, neighborhood):
    filtered = df.copy()
    if gender:
        filtered = filtered[filtered['gender'].isin(gender)]
    if age_range:
        filtered = filtered[(filtered['age'] >= age_range[0]) & (filtered['age'] <= age_range[1])]
    if neighborhood:
        filtered = filtered[filtered['neighbourhood'].isin(neighborhood)]
    return filtered




@app.callback(
    Output("total-appointments", "children"),
    Output("no-show-rate", "children"),
    Output("avg-waiting", "children"),
    Output("unique-patients", "children"),
    Output("show-vs-noshow", "figure"),
    Output("age-distribution", "figure"),
    Output("weekday-patterns", "figure"),
    Output("neighborhood-noshow", "figure"),
    Output("data-table", "data"),
    Input("apply-btn", "n_clicks"),
    State("gender-filter", "value"),
    State("age-slider", "value"),
    State("neighborhood-filter", "value"),
    prevent_initial_call=False
)
def update_dashboard(n_clicks, gender, age_range, neighborhood):
    filtered = filter_data(gender, age_range, neighborhood)

    total_appointments = len(filtered)
    no_show_rate = f"{filtered['no_show_flag'].mean() * 100:.2f}%"
    avg_waiting = f"{filtered['waiting_days'].mean():.1f} days"
    unique_patients = filtered['patientid'].nunique()

    fig_show = px.pie(filtered, names='no_show', title="Show vs No-show")
    fig_age = px.histogram(filtered, x="age", color="no_show", barmode="overlay", title="Age Distribution")
    fig_weekday = px.histogram(filtered, x="day_of_week", color="no_show", barmode="group",
                               category_orders={"day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
                               title="Appointments by Day of Week")
    top_neigh = (filtered.groupby('neighbourhood')['no_show_flag']
                 .mean()
                 .sort_values(ascending=False)
                 .head(10)
                 .reset_index())
    fig_neigh = px.bar(top_neigh, x="neighbourhood", y="no_show_flag", title="Top 10 Neighborhoods by No-show Rate")

    return total_appointments, no_show_rate, avg_waiting, unique_patients, fig_show, fig_age, fig_weekday, fig_neigh, filtered.to_dict("records")

@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    State("gender-filter", "value"),
    State("age-slider", "value"),
    State("neighborhood-filter", "value"),
    prevent_initial_call=True
)
def download_filtered(n_clicks, gender, age_range, neighborhood):
    filtered = filter_data(gender, age_range, neighborhood)
    return dcc.send_data_frame(filtered.to_csv, "filtered_medical_appointments.csv", index=False)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
