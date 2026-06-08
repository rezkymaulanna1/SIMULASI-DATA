import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Simulasi Servis Mobil", layout="wide")

st.title("Dashboard Simulasi Antrian Servis Mobil")
st.write("Upload dataset hasil simulasi atau hasil model untuk dianalisis.")

uploaded_file = st.file_uploader("Upload file CSV atau Excel", type=["csv", "xlsx", "xls"])

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("Dataset berhasil diupload.")
    
    st.subheader("Preview Data")
    st.dataframe(df, use_container_width=True)
    
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if "scenario" in df.columns:
        scenario_list = df["scenario"].dropna().unique().tolist()
        selected_scenario = st.multiselect("Filter scenario", scenario_list, default=scenario_list)
        if selected_scenario:
            df = df[df["scenario"].isin(selected_scenario)]
    
    st.subheader("Ringkasan Statistik")
    col1, col2, col3, col4, col5 = st.columns(5)

    for c in ["avgwaitingtime", "avgtimeinsystem", "carsfinished", "carsrejected", "utilization"]:
        if c not in df.columns:
            df[c] = None

    with col1:
        st.metric("Rata-rata Waiting Time", f"{df['avgwaitingtime'].mean():.2f}")
    with col2:
        st.metric("Rata-rata Time in System", f"{df['avgtimeinsystem'].mean():.2f}")
    with col3:
        st.metric("Cars Finished", f"{df['carsfinished'].sum():.0f}")
    with col4:
        st.metric("Cars Rejected", f"{df['carsrejected'].sum():.0f}")
    with col5:
        st.metric("Utilization", f"{df['utilization'].mean():.3f}")

    st.subheader("Visualisasi")

    if "scenario" in df.columns and "avgwaitingtime" in df.columns:
        fig1 = px.bar(
            df, x="scenario", y="avgwaitingtime",
            title="Perbandingan Average Waiting Time",
            color="scenario"
        )
        st.plotly_chart(fig1, use_container_width=True)

    if "scenario" in df.columns and "utilization" in df.columns:
        fig2 = px.bar(
            df, x="scenario", y="utilization",
            title="Perbandingan Utilization",
            color="scenario"
        )
        st.plotly_chart(fig2, use_container_width=True)

    if len(numeric_cols) >= 2:
        x_axis = st.selectbox("Sumbu X", numeric_cols, index=0)
        y_axis = st.selectbox("Sumbu Y", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
        fig3 = px.scatter(df, x=x_axis, y=y_axis, color="scenario" if "scenario" in df.columns else None)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Tabel Data")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Silakan upload dataset terlebih dahulu.")