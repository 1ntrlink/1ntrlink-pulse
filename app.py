# app.py — FIXED: unpack 4 values (removed allocations/pie), all tweaks in place, with initial data for instant load, enable bounce, no scroll
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc  # Added for Collapse
import plotly.graph_objects as go
from generate_pulse import generate_pulse_data
from datetime import datetime, timedelta
import pytz
import os

# Fetch initial data once at app start (uses cache, so fast)
initial_df, initial_total_equity, initial_stats, initial_total_unrealized = generate_pulse_data()

# Create initial figure for the main chart
initial_fig = go.Figure()
initial_fig.add_trace(go.Scatter(
    x=initial_df['execTime'], y=initial_df['equity'],
    mode='lines',
    name='Realized Profit',
    line=dict(color="#FFFFFF", width=3)  # White curve
))
initial_fig.add_trace(go.Scatter(
    x=[initial_df['execTime'].iloc[-1]], 
    y=[initial_total_equity],
    mode='markers',
    name='Unrealized Profit',
    marker=dict(color="#FFFFFF", size=20, symbol="cross-thin", opacity=1, line=dict(color="#FFFFFF", width=2)),  # Fixed cross-thin with line width for visibility
    text=[],  # Remove numbers above marker
    showlegend=True
))

# Vertical dashed gray line for unrealized profit
unrealized_direction = "up" if initial_total_unrealized > 0 else "down"
initial_fig.add_trace(go.Scatter(
    x=[initial_df['execTime'].iloc[-1], initial_df['execTime'].iloc[-1]],
    y=[initial_df['equity'].iloc[-1], initial_total_equity],
    mode='lines',
    name='Unrealized Profit Line',
    line=dict(color="#808080", width=2, dash="dash"),
    showlegend=False
))

# Gray arrowed line following x-axis (pointing right)
initial_fig.add_shape(type="line",
    x0=initial_df['execTime'].iloc[0], y0=0, x1=initial_df['execTime'].iloc[-1], y1=0,
    line=dict(color="#808080", width=2),
    xref="x", yref="y"
)
initial_fig.add_annotation(
    x=initial_df['execTime'].iloc[-1], y=0,
    xref="x", yref="y",
    text="",
    showarrow=True,
    arrowhead=2,  # Arrow point right
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#808080",
    ax=30, ay=0  # Extend to right
)

# Better x-axis spacing: add buffer at start and end, no dates
start_date = initial_df['execTime'].iloc[0] - timedelta(hours=12)  # Buffer at start
end_date = initial_df['execTime'].iloc[-1] + timedelta(hours=12)  # Buffer at end
initial_fig.update_xaxes(
    range=[start_date, end_date],
    color="#FFFFFF",
    tickangle=45,
    title_text="",
    showticklabels=False,  # No dates for minimalism
)

initial_fig.update_layout(
    plot_bgcolor="#000", paper_bgcolor="#000",
    font_color="#FFF",
    xaxis=dict(showgrid=False, color="#FFFFFF", showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#808080", spikethickness=1, spikedash="dash"),  # Gray dashed hover line, thinner
    yaxis=dict(showgrid=False, color="#FFFFFF", tickformat=","),
    hovermode="x unified",
    height=500,
    margin=dict(l=40, r=40, t=40, b=40),
    legend=dict(
        y=0.01, x=1, xanchor="right",
        bgcolor="rgba(0,0,0,0)",
        orientation="h",
        font=dict(size=12)  # Smaller for mobile
    )
)

# Initial stats divs
initial_return_pct = initial_stats['return_pct']
initial_return_color = "#00FF00" if initial_return_pct > 0 else "#FF4444"
initial_stats_divs = [
    html.Div([html.Strong("Pulse Strategy", style={"color": "#FFFFFF", "marginRight": "1rem"})], style={"display": "inline-block"}),
    html.Div([html.Strong("Balance"), html.Br(), f"{initial_total_equity:,.0f} USDT"], style={"color": "#FFFFFF"}),  # Changed to "Balance"
    html.Div([html.Strong("Return"), html.Br(), html.Span(f"{initial_return_pct:+.1f}%", style={"color": initial_return_color})], style={"color": "#FFFFFF"}),
    html.Div([html.Strong("Days Live"), html.Br(), f"{initial_stats['days_live']}"], style={"color": "#FFFFFF"}),
    html.Div([html.Strong("Max DD"), html.Br(), html.Span(f"{initial_stats['max_dd']:.1f}%", style={"color": "#FF4444"})], style={"color": "#FFFFFF"})
]

# Initial last update
initial_now = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
initial_last_update = f"Last update: {initial_now}"

# Initial advanced stats (placeholders— we'll fill from generate_pulse_data later)
initial_advanced_stats = html.Div([
    html.Div("Effective Leverage: Placeholder", style={"color": "#FFF"}),
    html.Div("Win Rate: Placeholder", style={"color": "#FFF"}),
    # Add more as we implement
], style={"display": "flex", "flexDirection": "column", "gap": "0.5rem", "marginTop": "1rem"})

app = Dash(__name__, title="1ntrlink Pulse", external_stylesheets=[dbc.themes.CYBORG])  # Dark theme for bootstrap
server = app.server

# Add custom CSS to remove white border and enable bounce
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                background-color: #000;
                overflow-y: auto;  # Allow auto for bounce without bar if content fits
                -webkit-overflow-scrolling: touch;  # Enable momentum/bounce on Mac
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div(style={
    "backgroundColor": "#000",
    "color": "#FFF",
    "fontFamily": "system-ui, sans-serif",
    "minHeight": "100vh",
    "padding": "1rem",
    "border": "none",
    "margin": "0"
}, children=[
    html.Div(style={"textAlign": "left", "marginBottom": "1rem"}, children=[
        html.H1("1ntrlink", style={
            "fontSize": "4rem",
            "fontWeight": "900",
            "color": "#FFFFFF",  # Changed to white
            "margin": "0"
        }),
    ]),

    html.Div(style={"textAlign": "center", "marginBottom": "1rem"}, children=[
        html.P("Pulse Strategy – Live Performance", style={"fontSize": "1.2rem", "color": "#AAA", "margin": "0.5rem 0 0 0"})
    ]),

    dcc.Graph(id="live-chart", figure=initial_fig, config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': 'reset', 'showAxisDragHandles': False, 'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']}, style={
        "height": "500px",
        "margin": "0 auto",
        "maxWidth": "1200px"
    }),

    html.Div(id="stats", children=initial_stats_divs, style={
        "display": "flex", "justifyContent": "center", "gap": "2rem",
        "marginTop": "1rem", "fontSize": "1.3rem", "flexWrap": "wrap"
    }),

    # Toggle for advanced stats (centered)
    html.Div(style={"textAlign": "center", "marginTop": "1rem"}, children=[
        html.Button("Show Advanced Stats", id="advanced-toggle", n_clicks=0, style={
            "backgroundColor": "#808080", "color": "#FFF", "border": "none", "padding": "0.5rem 1rem", "cursor": "pointer"
        }),
    ]),

    dbc.Collapse(id="advanced-panel", is_open=False, children=[
        initial_advanced_stats  # Placeholder—will update with real data
    ]),

    dcc.Interval(id="interval", interval=45*1000, n_intervals=0),

    html.Div(style={
        "textAlign": "center", "marginTop": "2rem", "color": "#555", "fontSize": "0.8rem"
    }, children=[
        "Non-custodial • We link and trade things • ",
        html.Span(id="last-update", children=initial_last_update)
    ])
])

@app.callback(
    Output("advanced-panel", "is_open"),
    Input("advanced-toggle", "n_clicks"),
    prevent_initial_call=True
)
def toggle_advanced(n):
    return n % 2 == 1  # Toggle on/off

@app.callback(
    Output("live-chart", "figure"),
    Output("stats", "children"),
    Output("last-update", "textContent"),
    Input("interval", "n_intervals")
)
def update_chart(n):
    df, total_equity, stats, total_unrealized = generate_pulse_data()  # Unpack 4 values
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['execTime'], y=df['equity'],
        mode='lines',
        name='Realized Profit',
        line=dict(color="#FFFFFF", width=3)  # White curve
    ))
    fig.add_trace(go.Scatter(
        x=[df['execTime'].iloc[-1]], 
        y=[total_equity],
        mode='markers',
        name='Unrealized Profit',
        marker=dict(color="#FFFFFF", size=20, symbol="cross-thin", opacity=1, line=dict(color="#FFFFFF", width=2)),  # Fixed cross-thin with line width for visibility
        text=[],  # Remove numbers above marker
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

    # Better x-axis spacing: add buffer at start and end, no dates
    start_date = df['execTime'].iloc[0] - timedelta(hours=12)  # Buffer at start
    end_date = df['execTime'].iloc[-1] + timedelta(hours=12)  # Buffer at end
    fig.update_xaxes(
        range=[start_date, end_date],
        color="#FFFFFF",
        tickangle=45,
        title_text="",
        showticklabels=False,  # No dates for minimalism
    )

    fig.update_layout(
        plot_bgcolor="#000", paper_bgcolor="#000",
        font_color="#FFF",
        xaxis=dict(showgrid=False, color="#FFFFFF", showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#808080", spikethickness=1, spikedash="dash"),  # Gray dashed hover line, thinner
        yaxis=dict(showgrid=False, color="#FFFFFF", tickformat=","),
        hovermode="x unified",
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(
            y=0.01, x=1, xanchor="right",
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            font=dict(size=12)  # Smaller for mobile
        ),
        dragmode=False  # Disable drag/zoom
    )

    # Stats with "Pulse Strategy" left of Total Equity
    return_pct = stats['return_pct']
    return_color = "#00FF00" if return_pct > 0 else "#FF4444"

    stats_divs = [
        html.Div([html.Strong("Pulse Strategy", style={"color": "#FFFFFF", "marginRight": "1rem"})], style={"display": "inline-block"}),
        html.Div([html.Strong("Balance"), html.Br(), f"{total_equity:,.0f} USDT"], style={"color": "#FFFFFF"}),  # Changed to "Balance"
        html.Div([html.Strong("Return"), html.Br(), html.Span(f"{return_pct:+.1f}%", style={"color": return_color})], style={"color": "#FFFFFF"}),
        html.Div([html.Strong("Days Live"), html.Br(), f"{stats['days_live']}"], style={"color": "#FFFFFF"}),
        html.Div([html.Strong("Max DD"), html.Br(), html.Span(f"{stats['max_dd']:.1f}%", style={"color": "#FF4444"})], style={"color": "#FFFFFF"})
    ]

    now = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return fig, stats_divs, f"Last update: {now}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)