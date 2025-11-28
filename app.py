# app.py — FIXED: total_unrealized from generate_pulse_data, all tweaks in place
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from generate_pulse import generate_pulse_data
from datetime import datetime, timedelta
import pytz
import os

app = Dash(__name__, title="1ntrlink Pulse")
server = app.server

app.layout = html.Div(style={
    "backgroundColor": "#000",
    "color": "#FFF",
    "fontFamily": "system-ui, sans-serif",
    "minHeight": "100vh",
    "overflow": "hidden",
    "padding": "1rem",
    "border": "none",
    "margin": "0"
}, children=[
    html.Div(style={"textAlign": "left", "marginBottom": "1rem"}, children=[
        html.H1("1ntrlink", style={
            "fontSize": "4rem",
            "fontWeight": "900",
            "background": "linear-gradient(90deg, #FFF, #FFF)",
            "-webkit-background-clip": "text",
            "color": "transparent",
            "margin": "0"
        }),
    ]),

    html.Div(style={"textAlign": "center", "marginBottom": "1rem"}, children=[
        html.P("Pulse Strategy – Live Performance", style={"fontSize": "1.2rem", "color": "#AAA", "margin": "0.5rem 0 0 0"})
    ]),

    dcc.Graph(id="live-chart", config={'displayModeBar': False}, style={
        "height": "500px",
        "margin": "0 auto",
        "maxWidth": "1200px"
    }),
    
    html.Div(id="stats", style={
        "display": "flex", "justifyContent": "center", "gap": "3rem",
        "marginTop": "1rem", "fontSize": "1.3rem", "flexWrap": "wrap"
    }),

    dcc.Interval(id="interval", interval=45*1000, n_intervals=0),

    html.Div(style={
        "textAlign": "center", "marginTop": "2rem", "color": "#555", "fontSize": "0.8rem"
    }, children=[
        "Non-custodial • We link and trade things • ",
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
    df, total_equity, stats, total_unrealized = generate_pulse_data()  # Added total_unrealized unpack
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['execTime'], y=df['equity'],
        mode='lines',
        name='Realized Equity',
        line=dict(color="#FFFFFF", width=3)  # White curve
    ))
    fig.add_trace(go.Scatter(
        x=[df['execTime'].iloc[-1]], 
        y=[total_equity],
        mode='markers',
        name='Total Equity',
        marker=dict(color="#FF0000", size=16, symbol="diamond"),
        text=[],  # Remove numbers above diamond
        showlegend=True
    ))

    # Vertical dashed gray line for unrealized profit
    unrealized_direction = "up" if total_unrealized > 0 else "down"
    fig.add_trace(go.Scatter(
        x=[df['execTime'].iloc[-1], df['execTime'].iloc[-1]],
        y=[df['equity'].iloc[-1], total_equity],
        mode='lines',
        name='Unrealized Profit Line',
        line=dict(color="#808080", width=2, dash="dash"),
        showlegend=False
    ))

    # Gray arrowed line following x-axis (pointing right)
    fig.add_shape(type="line",
        x0=df['execTime'].iloc[0], y0=0, x1=df['execTime'].iloc[-1], y1=0,
        line=dict(color="#808080", width=2),
        xref="x", yref="y"
    )
    fig.add_annotation(
        x=df['execTime'].iloc[-1], y=0,
        xref="x", yref="y",
        text="",
        showarrow=True,
        arrowhead=2,  # Arrow point right
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#808080",
        ax=30, ay=0  # Extend to right
    )

    # Better x-axis spacing: add buffer at start and end
    start_date = df['execTime'].iloc[0] - timedelta(hours=12)  # Buffer at start
    end_date = df['execTime'].iloc[-1] + timedelta(hours=12)  # Buffer at end
    fig.update_xaxes(range=[start_date, end_date], color="#FFFFFF", tickangle=45, title_text="")

    fig.update_layout(
        plot_bgcolor="#000", paper_bgcolor="#000",
        font_color="#FFF",
        xaxis=dict(showgrid=False, color="#FFFFFF", showticklabels=False),  # No date ticks
        yaxis=dict(showgrid=False, color="#FFFFFF", tickformat=","),
        hovermode="x unified",
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(y=0.01, x=1, xanchor="right", bgcolor="rgba(0,0,0,0)", orientation="h")  # Legend right of Max DD at bottom
    )

    # Stats with "Pulse Strategy" left of Total Equity
    return_pct = stats['return_pct']
    return_color = "#00FF00" if return_pct > 0 else "#FF4444"

    stats_divs = [
        html.Div([html.Strong("Pulse Strategy", style={"color": "#FFFFFF", "marginRight": "1rem"})], style={"display": "inline-block"}),
        html.Div([html.Strong("Total Equity"), html.Br(), f"{total_equity:,.0f} USDT"], style={"color": "#FFFFFF"}),
        html.Div([html.Strong("Return"), html.Br(), html.Span(f"{return_pct:+.1f}%", style={"color": return_color})], style={"color": "#FFFFFF"}),
        html.Div([html.Strong("Days Live"), html.Br(), f"{stats['days_live']}"], style={"color": "#FFFFFF"}),
        html.Div([html.Strong("Max DD"), html.Br(), html.Span(f"{stats['max_dd']:.1f}%", style={"color": "#FF4444"})], style={"color": "#FFFFFF"})
    ]

    now = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return fig, stats_divs, f"Last update: {now}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)