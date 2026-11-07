
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from defect_analytics import (
    load_defect_data,
    get_station_defect_analysis,
    get_defect_type_analysis,
    get_station_defect_breakdown
)


def show_quality_intelligence():

    st.title("🏭 Quality Intelligence")

    st.caption(
        "PostgreSQL-powered manufacturing defect monitoring, "
        "station quality analysis and defect intelligence."
    )

    try:
        defects = load_defect_data()

    except Exception as error:
        st.error(f"Unable to load defect data: {error}")
        return

    if defects.empty:
        st.warning("No defect records available in PostgreSQL.")
        return

    station_report = get_station_defect_analysis(defects)
    type_report = get_defect_type_analysis(defects)
    breakdown = get_station_defect_breakdown(defects)

    # ---------------------------------
    # KPI METRICS
    # ---------------------------------

    st.subheader("Manufacturing Quality Overview")

    total_defects = int(defects["defect_count"].sum())
    total_units = int(defects["units_inspected"].sum())
    total_stations = defects["station_id"].nunique()
    total_types = defects["defect_type"].nunique()

    overall_defect_rate = (
        total_defects / total_units * 100
        if total_units > 0 else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Defects", total_defects)
    col2.metric("Units Inspected", total_units)
    col3.metric("Stations Analyzed", total_stations)
    col4.metric("Defect Rate", f"{overall_defect_rate:.2f}%")

    st.divider()

    # ---------------------------------
    # STATION DEFECT ANALYSIS
    # ---------------------------------

    st.subheader("1. Station-wise Defect Analysis")

    st.dataframe(
        station_report,
        use_container_width=True,
        hide_index=True
    )

    fig_station = px.bar(
        station_report,
        x="station_id",
        y="defect_rate",
        text="defect_rate",
        title="Defect Rate by Manufacturing Station",
        labels={
            "station_id": "Station",
            "defect_rate": "Defect Rate (%)"
        }
    )

    st.plotly_chart(fig_station, use_container_width=True)

    # ---------------------------------
    # DEFECT RADAR CHART
    # ---------------------------------

    st.subheader("2. Manufacturing Station Defect Radar")

    fig_radar = go.Figure()

    fig_radar.add_trace(
        go.Scatterpolar(
            r=station_report["defect_rate"].tolist(),
            theta=station_report["station_id"].tolist(),
            fill="toself",
            name="Defect Rate"
        )
    )

    max_rate = float(station_report["defect_rate"].max())

    fig_radar.update_layout(
        title="Station Defect Rate Comparison",
        polar=dict(
            radialaxis=dict(
                visible=True,
                title="Defect Rate (%)",
                range=[0, max_rate + 1]
            )
        ),
        showlegend=True
    )

    st.plotly_chart(fig_radar, use_container_width=True)

    # ---------------------------------
    # DEFECT TYPE ANALYSIS
    # ---------------------------------

    st.subheader("3. Defect Type Analysis")

    st.dataframe(
        type_report,
        use_container_width=True,
        hide_index=True
    )

    fig_type = px.bar(
        type_report,
        x="defect_type",
        y="total_defects",
        color="defect_type",
        text="total_defects",
        title="Defects by Type"
    )

    st.plotly_chart(fig_type, use_container_width=True)

    # ---------------------------------
    # STATION DEFECT BREAKDOWN
    # ---------------------------------

    st.subheader("4. Station-wise Defect Breakdown")

    st.dataframe(
        breakdown,
        use_container_width=True
    )

    # ---------------------------------
    # HIGHEST DEFECT RATE
    # ---------------------------------

    highest_station = station_report.loc[
        station_report["defect_rate"].idxmax()
    ]

    st.subheader("5. Quality Improvement Priority")

    st.warning(
        f"Station {highest_station['station_id']} "
        f"has the highest defect rate: "
        f"{highest_station['defect_rate']:.2f}%."
    )

    # ---------------------------------
    # DOWNLOAD REPORTS
    # ---------------------------------

    st.divider()

    st.subheader("Download Quality Reports")

    col1, col2 = st.columns(2)

    col1.download_button(
        "Download Station Defect Report",
        station_report.to_csv(index=False),
        "station_defect_report.csv",
        "text/csv"
    )

    col2.download_button(
        "Download Defect Type Report",
        type_report.to_csv(index=False),
        "defect_type_report.csv",
        "text/csv"
    )
