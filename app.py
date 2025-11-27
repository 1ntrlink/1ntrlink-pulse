# app.py — THE PERFECT VERSION (from when everything looked amazing)
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from generate_pulse import generate_pulse_data
from datetime import datetime
import pytz
import os

app = Dash(__name__, title="1ntrlink Pulse")
server = app.server

app.layout = html.Div(style={
    "backgroundColor": "#000",
    "color": "#FFF",
    "fontFamily": "system-ui, sans-serif",
    "minHeight": "100vh",
    "padding": "2rem 1rem"
}, children=[
    html.Div(style={"textAlign": "center", "marginBottom": "3rem"}, children=[
        html.H1("1ntrlink", style={
            "fontSize": "5rem",
            "fontWeight": "900",
    "background": "linear-gradient(90deg, #FFF, #FF0000)",
            "-webkit-background-clip": "text",
            "color": "transparent",
            "margin": "0"
        }),
        html.P("Pulse Strategy – Live Performance", style={"fontSize": "1.5rem", "color": "#AAA", "margin": "1rem 0 0 0"})
    ]),

    dcc.Graph(id="live-chart", config={'displayModeBar': False}),
    
    html.Div(id="stats", style={
        "display": "flex", "justifyContent": "center", "gap": "4rem",
        "marginTop": "2rem", "fontSize": "1.4rem", "flexWrap": "wrap"
    }),

    dcc.Interval(id="interval", interval=45*1000, n_intervals=0),  # 45 seconds

    html.Div(style={
        "textAlign": "center", "marginTop": "4rem", "color": "#555", "fontSize": "0.9rem"
    }, children=[
        "Zero custody • Clients link their own exchange APIs • ",
        html.Span(id="last-update")
    ])
])

@app.callback(
    Output("live-chart", "figure"),
    Output("stats", "children"),
    Output("last-update", "textContent"),
    Input("interval", "n_intervals")
)
def update_chart(n):
    df, total_equity, stats = generate_pulse_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['execTime'], y=df['equity'],
        mode='lines',
        name='Realized Equity',
        line=dict(color="#00FFFF", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=[df['execTime'].iloc[-1]], 
        y=[total_equity],
        mode='markers+text',
        name='Total Equity',
        marker=dict(color="#FF0000", size=16, symbol="diamond"),
        text=[f"{total_equity:,.0f}"],
        textposition="top center",
        textfont=dict(color="#FF0000", size=16)
    ))

    fig.update_layout(
        plot_bgcolor="#000", paper_bgcolor="#000",
        font_color="#FFF",
        xaxis=dict(showgrid=False, color="#333"),
        yaxis=dict(showgrid=False, color="#333", tickformat=","),
        hovermode="x unified",
        height=660,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    stats_divs = [
        html.Div([html.Strong("Total Equity"), html.Br(), f"{total_equity:,.0f} USDT"], style={"color": "#FF0000"}),
        html.Div([html.Strong("Return"), html.Br(), f"{stats['return_pct']:+.1f}%"], style={"color": "#00FFFF"}),
        html.Div([html.Strong("Days Live"), html.Br(), f"{stats['days_live']}"]),
        html.Div([html.Strong("Max DD"), html.Br(), f"{stats['max_dd']:.1f}%"], style={"color": "#FF4444" if stats['max_dd'] < -5 else "#AAA"}),
    ]

    now = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return fig, stats_divs, f"Last update: {now}"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)