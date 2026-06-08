import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Simulasi Servis Mobil Pro",
    layout="wide"
)

st.title("🚗 Dashboard Simulasi Antrian Servis Mobil (Versi Optimasi)")
st.write("Upload dataset hasil simulasi untuk analisis performa antrian dan profitabilitas bisnis.")

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
    # VALIDASI & PENYESUAIAN KOLOM (FAIL-SAFE)
    # ======================
    # Kolom dasar dari versi sebelumnya
    base_cols = ["scenario", "avgwaitingtime", "avgtimeinsystem", "carsfinished", "carsrejected", "utilization"]
    for c in base_cols:
        if c not in df.columns:
            df[c] = 0 if c != "scenario" else "Skenario Default"

    # Kolom BARU untuk mengakomodasi informasi yang kurang (Teori Antrian & Bisnis)
    new_cols_defaults = {
        "num_servers": 2,            # Jumlah mekanik/bengkel operasional
        "avg_queue_length": 0.0,     # Rata-rata panjang antrian mobil
        "max_queue_length": 0,       # Panjang antrian maksimal (kapasitas fisik)
        "operational_cost": 500000,  # Biaya operasional per skenario (gaji, alat, dll)
        "opportunity_loss": 150000   # Kerugian per 1 mobil yang ditolak (rejected)
    }
    
    for col, default_val in new_cols_defaults.items():
        if col not in df.columns:
            df[col] = default_val

    # Perhitungan Otomatis: Service Time & Finansial
    # Waktu Pelayanan = Waktu di Sistem - Waktu Tunggu
    df["avg_service_time"] = (df["avgtimeinsystem"] - df["avgwaitingtime"]).clip(lower=0)
    
    # Asumsi Pendapatan Kotor per mobil yang berhasil diservis (Misal: Rp 350,000)
    revenue_per_car = 350000 
    df["estimated_revenue"] = df["carsfinished"] * revenue_per_car
    df["total_opportunity_loss"] = df["carsrejected"] * df["opportunity_loss"]
    df["net_profit"] = df["estimated_revenue"] - df["operational_cost"] - df["total_opportunity_loss"]

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
    st.dataframe(df, use_container_width=True)

    # ======================
    # 📊 RINGKASAN STATISTIK UTAMA (OPERASIONAL)
    # ======================
    st.subheader("📊 Ringkasan Performa Antrian")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Avg Waiting Time", f"{df['avgwaitingtime'].mean():.2f} mnt")
    with col2:
        st.metric("Avg Service Time", f"{df['avg_service_time'].mean():.2f} mnt")
    with col3:
        st.metric("Avg Queue Length", f"{df['avg_queue_length'].mean():.2f} mobil")
    with col4:
        st.metric("Total Cars Finished", f"{df['carsfinished'].sum():.0f}")
    with col5:
        st.metric("Total Cars Rejected", f"{df['carsrejected'].sum():.0f}")

    # ======================
    # 💰 ANALISIS FINANSIAL (NEW SECTION)
    # ======================
    st.subheader("💰 Dampak Finansial & Bisnis")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        st.metric("Est. Total Revenue", f"Rp {df['estimated_revenue'].sum():,.0f}")
    with f_col2:
        st.metric("Total Operasional Cost", f"Rp {df['operational_cost'].sum():,.0f}")
    with f_col3:
        st.metric("Total Opportunity Loss", f"Rp {df['total_opportunity_loss'].sum():,.0f}", delta=f"-Rp {df['total_opportunity_loss'].sum():,.0f}", delta_color="inverse")
    with f_col4:
        total_profit = df['net_profit'].sum()
        st.metric("Total Net Profit", f"Rp {total_profit:,.0f}", delta="Keuntungan Bersih")

    # ======================
    # 📈 INDIKATOR KINERJA & STATUS SISTEM
    # ======================
    st.subheader("⚙️ Kapasitas & Status Sistem")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    total_cars = df["carsfinished"].sum() + df["carsrejected"].sum()
    service_rate = ((df["carsfinished"].sum() / total_cars) * 100) if total_cars > 0 else 0
    avg_util = df["utilization"].mean()

    with col_kpi1:
        st.metric("Service Success Rate", f"{service_rate:.2f}%")
    with col_kpi2:
        st.metric("Rata-rata Utilisasi Mekanik", f"{avg_util * 100:.1f}%")
    with col_kpi3:
        # Status Sistem Berdasarkan Utilisasi
        if avg_util < 0.50:
            st.info("Kapasitas berlebih (Banyak mekanik menganggur).")
        elif avg_util < 0.85:
            st.success("Kondisi Optimal (Keseimbangan performa & biaya).")
        else:
            st.warning("Sistem Overload (Risiko antrian meludak tinggi!).")

    # ======================
    # 🏆 EVALUASI SKENARIO GANDA (OPERASIONAL VS BISNIS)
    # ======================
    if len(df) > 0 and "scenario" in df.columns:
        st.subheader("🏆 Evaluasi Skenario Terbaik")
        
        best_ops = df.loc[df["avgwaitingtime"].idxmin()]
        best_biz = df.loc[df["net_profit"].idxmax()]
        
        col_eval1, col_eval2 = st.columns(2)
        
        with col_eval1:
            st.success(f"""
            **Skenario Terbaik (Operasional - Waktu Tunggu Terpendek)**
            * **Nama Skenario:** {best_ops['scenario']}
            * **Jumlah Mekanik:** {best_ops['num_servers']} orang
            * **Waktu Tunggu:** {best_ops['avgwaitingtime']:.2f} menit
            * **Net Profit:** Rp {best_ops['net_profit']:,.0f}
            """)
            
        with col_eval2:
            st.info(f"""
            **Skenario Terbaik (Bisnis - Profit Tertinggi)**
            * **Nama Skenario:** {best_biz['scenario']}
            * **Jumlah Mekanik:** {best_biz['num_servers']} orang
            * **Waktu Tunggu:** {best_biz['avgwaitingtime']:.2f} menit
            * **Net Profit:** Rp {best_biz['net_profit']:,.0f}
            """)

    # ======================
    # VISUALISASI BARU
    # ======================
    st.subheader("📉 Analisis Grafis Perbandingan Skenario")
    vis_tab1, vis_tab2, vis_tab3 = st.tabs(["Performa Antrian", "Analisis Finansial", "Korelasi Variabel"])
    
    with vis_tab1:
        # Grafik Waktu Tunggu vs Panjang Antrian
        fig_ops = go.Figure()
        fig_ops.add_trace(go.Bar(x=df["scenario"], y=df["avgwaitingtime"], name="Avg Waiting Time (Min)"))
        fig_ops.add_trace(go.Line(x=df["scenario"], y=df["avg_queue_length"], name="Avg Queue Length (Cars)", yaxis="y2"))
        
        fig_ops.update_layout(
            title="Waktu Tunggu vs Panjang Antrian Fisik",
            yaxis=dict(title="Waktu Tunggu (Menit)"),
            yaxis2=dict(title="Jumlah Mobil di Antrian", overlaying="y", side="right")
        )
        st.plotly_chart(fig_ops, use_container_width=True)
        
    with vis_tab2:
        # Grafik Profitabilitas Skenario
        fig_fin = px.bar(
            df, x="scenario", y="net_profit", 
            color="net_profit", 
            title="Analisis Keuntungan Bersih per Skenario",
            labels={"net_profit": "Net Profit (Rp)"}
        )
        st.plotly_chart(fig_fin, use_container_width=True)
        
    with vis_tab3:
        # Scatter Plot Hubungan Kustom
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        x_axis = st.selectbox("Sumbu X", numeric_cols, index=numeric_cols.index("utilization") if "utilization" in numeric_cols else 0)
        y_axis = st.selectbox("Sumbu Y", numeric_cols, index=numeric_cols.index("net_profit") if "net_profit" in numeric_cols else 1)
        
        fig_scatter = px.scatter(df, x=x_axis, y=y_axis, color="scenario", size="carsfinished", title=f"Hubungan antara {x_axis} dan {y_axis}")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ======================
    # KESIMPULAN OTOMATIS BERBASIS MULTI-VARIABEL
    # ======================
    if len(df) > 0 and "scenario" in df.columns:
        st.subheader("📌 Kesimpulan & Rekomendasi Bisnis")
        
        # Logika rekomendasi gabungan
        if best_ops['scenario'] == best_biz['scenario']:
            rekomendasi_teks = f"Skenario **{best_biz['scenario']}** adalah pilihan mutlak karena berhasil meminimalkan waktu tunggu pelanggan sekaligus memberikan profit tertinggi bagi bengkel."
        else:
            rekomendasi_teks = f"Terdapat *trade-off* (pilihan sulit). Jika fokus Anda adalah **kepuasan pelanggan**, pilih **{best_ops['scenario']}**. Namun, jika fokus Anda adalah **efisiensi biaya operasional**, skenario **{best_biz['scenario']}** jauh lebih menguntungkan secara finansial meskipun pelanggan harus menunggu sedikit lebih lama."

        st.markdown(f"""
        ### Rekomendasi Eksekutif:
        {rekomendasi_teks}
        
        * **Catatan Bottleneck:** Perhatikan nilai *Utilisasi Mekanik*. Jika ada skenario dengan nilai di atas 85%, pertimbangkan untuk membatasi kapasitas antrian (`max_queue_length`) atau menambah mekanik part-time pada jam sibuk guna menekan angka *Opportunity Loss* akibat mobil yang ditolak.
        """)

    # ======================
    # TABEL AKHIR
    # ======================
    st.subheader("📋 Tabel Data Lengkap")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Silakan upload dataset simulasi Anda terlebih dahulu untuk memulai analisis.")
