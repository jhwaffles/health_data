from flask import Flask, render_template
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# Initialize Flask app
server = Flask(__name__)

# Sample dataset
df = px.data.gapminder()

#divide subsets.
list(df.columns)
active=[i for i in df.columns if "Active_" in i]
bowel=[i for i in df.columns if"Bowel Movements_" in i]
creative=[i for i in df.columns if "Creative_" in i]
lifestyle=[i for i in df.columns if "Lifestyle_" in i]
meds=[i for i in df.columns if "Meds/Supplements_" in i]
energy=[i for i in df.columns if "Energy_" in i]
mood=[i for i in df.columns if "Mood_" in i]
nutrition=[i for i in df.columns if "Nutrition_" in i]
sleep=[i for i in df.columns if "Sleep_" in i]
symptom=[i for i in df.columns if "Symptom_" in i]
weather=[i for i in df.columns if "Weather_" in i]
sleep_metrics=['deep_sleep','efficiency_x','latency','rem_sleep','restfulness','timing','total_sleep']  #what is efficiency y?
hrv=['average_breath','average_heart_rate','average_hrv','lowest_heart_rate']
sleep_times=['awake_time','deep_sleep_duration','latency_duration','light_sleep_duration','rem_sleep_duration','restless_periods','time_in_bed','total_sleep_duration']
readiness=[i for i in df.columns if "readiness_" in i]

# Initialize Dash app inside Flask
dash_app = dash.Dash(__name__, server=server, url_base_pathname="/dashboard/")

# Define Dash layout
dash_app.layout = html.Div([
    html.H4("Metrics Over Time"),
    dcc.Graph(id="graph"),
    dcc.Checklist(
        id="checklist",
        options=[{"label": m, "value": m} for m in sleep_metrics],
        value=["lifeExp"],  # Default selection
        inline=True
    ),
])

# Dash callback
@dash_app.callback(
    dash.Output("graph", "figure"),
    dash.Input("checklist", "value")
)
def update_chart(selected_metrics):
    fig = px.line(
        df[df["continent"] == "Americas"], 
        x="year", 
        y=selected_metrics, 
        color="country", 
        markers=True
    )
    
    fig.update_traces(marker=dict(size=6))  # Adjust marker size for better visibility
    fig.update_layout(title="Metrics Over Time with Markers", xaxis_title="Year", yaxis_title="Value")
    
    return fig

# Flask route for home
@server.route("/")
def home():
    return render_template("index.html")

# Run Flask app locally
if __name__ == "__main__":
    server.run(debug=True, host="0.0.0.0", port=5000)