import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Simulasi Servis Mobil",
    layout="wide"
)

st.title("🚗 Dashboard Simulasi Antrian Servis Mobil")
st.write("Upload dataset hasil simulasi atau hasil model untuk dianalisis.")

uploaded_file = st.file_uploader(
    "Upload file CSV atau Excel",
    type=["csv", "xlsx", "xls"]
)

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if uploaded_file is not None:

    df = load_data(uploaded_file)

    st.success("Dataset berhasil diupload.")

    # ======================
    # FILTER SCENARIO
    # ======================
    if "scenario" in df.columns:

        scenario_list = df["scenario"].dropna().unique().tolist()

        selected_scenario = st.multiselect(
            "Filter Scenario",
            scenario_list,
            default=scenario_list
        )

        if selected_scenario:
            df = df[df["scenario"].isin(selected_scenario)]

    # ======================
    # PREVIEW DATA
    # ======================
    st.subheader("📄 Preview Data")

    st.dataframe(
        df,
        use_container_width=True
    )

    # ======================
    # VALIDASI KOLOM
    # ======================
    for c in [
        "avgwaitingtime",
        "avgtimeinsystem",
        "carsfinished",
        "carsrejected",
        "utilization"
    ]:
        if c not in df.columns:
            df[c] = 0

    # ======================
    # KPI UTAMA
    # ======================
    st.subheader("📊 Ringkasan Statistik")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Avg Waiting Time",
            f"{df['avgwaitingtime'].mean():.2f}"
        )

    with col2:
        st.metric(
            "Avg Time In System",
            f"{df['avgtimeinsystem'].mean():.2f}"
        )

    with col3:
        st.metric(
            "Cars Finished",
            f"{df['carsfinished'].sum():.0f}"
        )

    with col4:
        st.metric(
            "Cars Rejected",
            f"{df['carsrejected'].sum():.0f}"
        )

    with col5:
        st.metric(
            "Utilization",
            f"{df['utilization'].mean():.3f}"
        )

    # ======================
    # KPI TAMBAHAN
    # ======================
    st.subheader("📈 Indikator Kinerja")

    total_cars = (
        df["carsfinished"].sum() +
        df["carsrejected"].sum()
    )

    service_rate = (
        (df["carsfinished"].sum() / total_cars) * 100
        if total_cars > 0 else 0
    )

    rejection_rate = (
        (df["carsrejected"].sum() / total_cars) * 100
        if total_cars > 0 else 0
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Service Success Rate",
            f"{service_rate:.2f}%"
        )

    with col2:
        st.metric(
            "Rejection Rate",
            f"{rejection_rate:.2f}%"
        )

    # ======================
    # STATUS SISTEM
    # ======================
    st.subheader("⚙️ Status Sistem")

    avg_util = df["utilization"].mean()

    if avg_util < 0.50:
        st.info(
            "Kapasitas servis masih berlebih."
        )
    elif avg_util < 0.80:
        st.success(
            "Kapasitas servis berada pada kondisi optimal."
        )
    else:
        st.warning(
            "Sistem sangat sibuk, risiko antrian meningkat."
        )

    # ======================
    # SKENARIO TERBAIK
    # ======================
    if (
        "scenario" in df.columns and
        len(df) > 0 and
        "avgwaitingtime" in df.columns
    ):

        st.subheader("🏆 Evaluasi Skenario")

        best_waiting = df.loc[
            df["avgwaitingtime"].idxmin()
        ]

        worst_waiting = df.loc[
            df["avgwaitingtime"].idxmax()
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.success(
                f"""
                Skenario Terbaik

                {best_waiting['scenario']}

                Waiting Time:
                {best_waiting['avgwaitingtime']:.2f}
                """
            )

        with col2:
            st.error(
                f"""
                Skenario Terburuk

                {worst_waiting['scenario']}

                Waiting Time:
                {worst_waiting['avgwaitingtime']:.2f}
                """
            )

    # ======================
    # VISUALISASI
    # ======================
    st.subheader("📉 Visualisasi")

    if (
        "scenario" in df.columns and
        "avgwaitingtime" in df.columns
    ):

        fig1 = px.bar(
            df,
            x="scenario",
            y="avgwaitingtime",
            color="scenario",
            title="Perbandingan Average Waiting Time"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    if (
        "scenario" in df.columns and
        "utilization" in df.columns
    ):

        fig2 = px.bar(
            df,
            x="scenario",
            y="utilization",
            color="scenario",
            title="Perbandingan Utilization"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # ======================
    # SCATTER PLOT
    # ======================
    numeric_cols = df.select_dtypes(
        include="number"
    ).columns.tolist()

    if len(numeric_cols) >= 2:

        st.subheader("🔍 Analisis Hubungan Variabel")

        x_axis = st.selectbox(
            "Sumbu X",
            numeric_cols,
            index=0
        )

        y_axis = st.selectbox(
            "Sumbu Y",
            numeric_cols,
            index=1
        )

        fig3 = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color="scenario"
            if "scenario" in df.columns
            else None
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    # ======================
    # PIE CHART
    # ======================
    st.subheader("🥧 Proporsi Hasil Pelayanan")

    pie_df = pd.DataFrame({
        "Status": ["Finished", "Rejected"],
        "Jumlah": [
            df["carsfinished"].sum(),
            df["carsrejected"].sum()
        ]
    })

    fig_pie = px.pie(
        pie_df,
        names="Status",
        values="Jumlah"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

    # ======================
    # HISTOGRAM
    # ======================
    st.subheader("📊 Distribusi Waiting Time")

    fig_hist = px.histogram(
        df,
        x="avgwaitingtime",
        nbins=15
    )

    st.plotly_chart(
        fig_hist,
        use_container_width=True
    )

    # ======================
    # HEATMAP KORELASI
    # ======================
    if len(numeric_cols) >= 2:

        st.subheader("🔥 Korelasi Antar Variabel")

        corr = df[numeric_cols].corr()

        fig_corr = px.imshow(
            corr,
            text_auto=True,
            aspect="auto"
        )

        st.plotly_chart(
            fig_corr,
            use_container_width=True
        )

    # ======================
    # RANKING SKENARIO
    # ======================
    if "scenario" in df.columns:

        st.subheader("🏅 Ranking Skenario")

        ranking = df.sort_values(
            by=["avgwaitingtime", "carsrejected"],
            ascending=[True, True]
        )

        st.dataframe(
            ranking,
            use_container_width=True
        )

    # ======================
    # KESIMPULAN
    # ======================
    if (
        "scenario" in df.columns and
        len(df) > 0
    ):

        best = df.loc[
            df["avgwaitingtime"].idxmin()
        ]

        st.subheader("📌 Kesimpulan Otomatis")

        st.markdown(
            f"""
### Rekomendasi

Berdasarkan hasil simulasi, skenario **{best['scenario']}**
merupakan alternatif terbaik karena:

- Memiliki rata-rata waiting time terendah.
- Memiliki efisiensi pelayanan yang baik.
- Menekan jumlah kendaraan yang ditolak.
- Menjaga utilisasi sumber daya tetap efektif.

Skenario ini direkomendasikan untuk diterapkan pada operasional dealer servis mobil.
"""
        )

    # ======================
    # TABEL AKHIR
    # ======================
    st.subheader("📋 Tabel Data")

    st.dataframe(
        df,
        use_container_width=True
    )

else:
    st.info(
        "Silakan upload dataset terlebih dahulu."
    )
