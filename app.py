# Inside update_chart callback, replace the fig.update_layout with this:
    fig.update_layout(
        plot_bgcolor="#000", paper_bgcolor="#000",
        font_color="#FFF",
        xaxis=dict(showgrid=False, color="#333", tickangle=45),
        yaxis=dict(showgrid=False, color="#333", tickformat=","),
        hovermode="x unified",
        height=700,
        margin=dict(l=50, r=50, t=50, b=80),  # ← more bottom margin = breathing room
        legend=dict(y=1.1, x=0.7, bgcolor="rgba(0,0,0,0)", font=dict(color="#FFF"))
    )

    # And make line thicker + diamond bigger
    fig.data[0].line.width = 3.5
    fig.data[1].marker.size = 18