import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# KONFIGURASI HALAMAN
# =====================================================

st.set_page_config(
    page_title="Dashboard Analisis Simulasi Servis Mobil",
    layout="wide"
)

# =====================================================
# HEADER
# =====================================================

st.title("🚗 Dashboard Analisis Simulasi Antrian Pelayanan Servis Mobil")

st.markdown("""
Dashboard ini digunakan untuk mengevaluasi performa sistem pelayanan servis kendaraan
berdasarkan hasil simulasi berbagai skenario operasional.

### Indikator yang Dianalisis
- Average Waiting Time
- Average Time in System
- Resource Utilization
- Jumlah Kendaraan Selesai Dilayani
- Jumlah Kendaraan Ditolak
""")

# =====================================================
# UPLOAD DATA
# =====================================================

uploaded_file = st.file_uploader(
    "Upload Dataset (CSV / Excel)",
    type=["csv", "xlsx", "xls"]
)

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# =====================================================
# PROSES DATA
# =====================================================

if uploaded_file is not None:

    df = load_data(uploaded_file)

    st.success("Dataset berhasil diunggah.")

    # =================================================
    # FILTER SCENARIO
    # =================================================

    if "scenario" in df.columns:

        scenario_list = sorted(
            df["scenario"].dropna().unique().tolist()
        )

        selected_scenario = st.multiselect(
            "Filter Scenario",
            scenario_list,
            default=scenario_list
        )

        if selected_scenario:
            df = df[df["scenario"].isin(selected_scenario)]

    # =================================================
    # VALIDASI KOLOM
    # =================================================

    required_cols = [
        "avgwaitingtime",
        "avgtimeinsystem",
        "carsfinished",
        "carsrejected",
        "utilization"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    # =================================================
    # EXECUTIVE SUMMARY
    # =================================================

    st.header("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Avg Waiting Time",
            f"{df['avgwaitingtime'].mean():.2f} menit"
        )

    with col2:
        st.metric(
            "Avg Time in System",
            f"{df['avgtimeinsystem'].mean():.2f} menit"
        )

    with col3:
        st.metric(
            "Service Completion",
            f"{df['carsfinished'].sum():.0f}"
        )

    with col4:
        st.metric(
            "Resource Utilization",
            f"{df['utilization'].mean()*100:.1f}%"
        )

    # =================================================
    # KPI TAMBAHAN
    # =================================================

    total_cars = (
        df["carsfinished"].sum()
        + df["carsrejected"].sum()
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

    # =================================================
    # EVALUASI SISTEM
    # =================================================

    st.header("Evaluasi Kinerja Sistem")

    avg_util = df["utilization"].mean()

    if avg_util < 0.50:
        level = "Under Utilized"
    elif avg_util < 0.80:
        level = "Efficient"
    else:
        level = "Highly Loaded"

    st.info(
        f"""
        Tingkat utilisasi rata-rata sistem adalah
        **{avg_util:.2%}** sehingga sistem dikategorikan
        sebagai **{level}**.
        """
    )

    # =================================================
    # ANALISIS SKENARIO
    # =================================================

    if (
        "scenario" in df.columns
        and len(df) > 0
    ):

        st.header("Analisis Perbandingan Skenario")

        best = df.loc[
            df["avgwaitingtime"].idxmin()
        ]

        worst = df.loc[
            df["avgwaitingtime"].idxmax()
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
### Skenario Paling Efisien

**{best['scenario']}**

- Waiting Time : {best['avgwaitingtime']:.2f}
- Time in System : {best['avgtimeinsystem']:.2f}
- Utilization : {best['utilization']:.2f}
""")

        with col2:
            st.warning(f"""
### Skenario Perlu Evaluasi

**{worst['scenario']}**

- Waiting Time : {worst['avgwaitingtime']:.2f}
- Time in System : {worst['avgtimeinsystem']:.2f}
- Utilization : {worst['utilization']:.2f}
""")

    # =================================================
    # ANALISIS VISUAL
    # =================================================

    st.header("Analisis Visual")

    # -----------------------------
    # Kinerja Operasional
    # -----------------------------

    st.subheader("Kinerja Operasional")

    if "scenario" in df.columns:

        fig_wait = px.bar(
            df,
            x="scenario",
            y="avgwaitingtime",
            color="scenario",
            title="Perbandingan Average Waiting Time"
        )

        st.plotly_chart(
            fig_wait,
            use_container_width=True
        )

        fig_time = px.bar(
            df,
            x="scenario",
            y="avgtimeinsystem",
            color="scenario",
            title="Perbandingan Average Time in System"
        )

        st.plotly_chart(
            fig_time,
            use_container_width=True
        )

    # -----------------------------
    # Efisiensi Sumber Daya
    # -----------------------------

    st.subheader("Efisiensi Sumber Daya")

    if "scenario" in df.columns:

        fig_util = px.bar(
            df,
            x="scenario",
            y="utilization",
            color="scenario",
            title="Perbandingan Resource Utilization"
        )

        st.plotly_chart(
            fig_util,
            use_container_width=True
        )

    # -----------------------------
    # Outcome Pelayanan
    # -----------------------------

    st.subheader("Outcome Pelayanan")

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
        values="Jumlah",
        title="Proporsi Kendaraan Selesai dan Ditolak"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

    # =================================================
    # ANALISIS HUBUNGAN VARIABEL
    # =================================================

    numeric_cols = df.select_dtypes(
        include="number"
    ).columns.tolist()

    if len(numeric_cols) >= 2:

        st.header("Analisis Hubungan Variabel")

        col1, col2 = st.columns(2)

        with col1:
            x_axis = st.selectbox(
                "Pilih Sumbu X",
                numeric_cols
            )

        with col2:
            y_axis = st.selectbox(
                "Pilih Sumbu Y",
                numeric_cols,
                index=1
            )

        fig_scatter = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color="scenario"
            if "scenario" in df.columns
            else None,
            title=f"Hubungan {x_axis} dan {y_axis}"
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True
        )

    # =================================================
    # KORELASI
    # =================================================

    if len(numeric_cols) >= 2:

        st.header("Analisis Korelasi")

        corr = df[numeric_cols].corr()

        fig_corr = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            title="Heatmap Korelasi Variabel"
        )

        st.plotly_chart(
            fig_corr,
            use_container_width=True
        )

        st.caption("""
Nilai korelasi mendekati +1 menunjukkan hubungan positif yang kuat,
sedangkan nilai mendekati -1 menunjukkan hubungan negatif yang kuat.
Nilai mendekati 0 menunjukkan hubungan yang lemah.
""")

    # =================================================
    # RANKING SKENARIO
    # =================================================

    if "scenario" in df.columns:

        st.header("Ranking Skenario")

        ranking = df.sort_values(
            by=[
                "avgwaitingtime",
                "carsrejected"
            ],
            ascending=[True, True]
        )

        ranking = ranking.reset_index(drop=True)
        ranking.index += 1
        ranking.index.name = "Rank"

        st.dataframe(
            ranking,
            use_container_width=True
        )

    # =================================================
    # DATASET
    # =================================================

    st.header("Dataset")

    st.dataframe(
        df,
        use_container_width=True
    )

    # =================================================
    # KESIMPULAN
    # =================================================

    if (
        "scenario" in df.columns
        and len(df) > 0
    ):

        st.header("Kesimpulan dan Rekomendasi")

        st.markdown(f"""
Berdasarkan hasil simulasi yang dilakukan, skenario
**{best['scenario']}** menunjukkan performa terbaik
dibandingkan skenario lainnya.

Skenario tersebut menghasilkan rata-rata waktu tunggu
sebesar **{best['avgwaitingtime']:.2f} menit**
dengan tingkat utilisasi sumber daya sebesar
**{best['utilization']:.2%}**.

Hasil ini menunjukkan bahwa konfigurasi tersebut
mampu memberikan keseimbangan antara efisiensi pelayanan
dan pemanfaatan sumber daya, sehingga direkomendasikan
untuk diterapkan pada sistem pelayanan servis kendaraan.
""")

else:

    st.info(
        "Silakan upload dataset terlebih dahulu untuk memulai analisis."
    )
