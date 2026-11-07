
import plotly.graph_objects as go

from defect_analytics import (
    load_defect_data,
    get_station_defect_analysis
)


# Load defect records from PostgreSQL
defects = load_defect_data()

if defects.empty:
    print("No defect records found in PostgreSQL.")

else:
    # Calculate station defect rates
    df = get_station_defect_analysis(defects)

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=df["defect_rate"].tolist(),
            theta=df["station_id"].tolist(),
            fill="toself",
            name="Defect Rate"
        )
    )

    fig.update_layout(
        title="Manufacturing Station Defect Radar",
        polar=dict(
            radialaxis=dict(
                visible=True,
                title="Defect Rate (%)",
                range=[0, max(df["defect_rate"]) + 1]
            )
        ),
        showlegend=True
    )

    # Display chart
    fig.show()

    # Export chart as HTML
    fig.write_html("data/defect_radar_chart.html")

    print("\nStation defect rates:")
    print(df.to_string(index=False))

    print("\nDefect radar chart generated successfully!")
    print("Saved: data/defect_radar_chart.html")
