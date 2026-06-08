import streamlit as pd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Konfigurasi halaman dengan pendekatan formal
st.set_page_config(
    page_title="Analisis Sistem Antrian & Optimasi Operasional",
    layout="wide"
)

# Header Akademis / Laporan Eksekutif
st.title("Dashboard Analisis Komparatif dan Optimasi Sistem Antrian Servis Kendaraan")
st.markdown("""
---
*Aplikasi ini berfungsi sebagai instrumen pengambilan keputusan berbasis data simulasi untuk mengevaluasi kinerja operasional sistem antrian stochastic dan implikasinya terhadap kelayakan finansial perusahaan.*
""")

# Modul Unggah Data
st.sidebar.header("Parameter & Input Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah Dataset Simulasi (Format CSV / Excel)",
    type=["csv", "xlsx", "xls"]
)

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("Dataset berhasil dimuat dan divalidasi.")

    # =========================================================================
    # STANDARISASI & VALIDASI DATA (FAIL-SAFE DENGAN METODE IMPUTASI DEFAULT)
    # =========================================================================
    base_cols = ["scenario", "avgwaitingtime", "avgtimeinsystem", "carsfinished", "carsrejected", "utilization"]
    for c in base_cols:
        if c not in df.columns:
            df[c] = 0 if c != "scenario" else "Skenario Dasar"

    # Penambahan variabel laten berdasarkan Teori Antrian & Manajemen Keuangan
    extended_metrics = {
        "num_servers": 2,            # Jumlah Pelayan / Mekanik aktif (M)
        "avg_queue_length": 0.0,     # Rata-rata panjang antrian dalam sistem (Lq)
        "max_queue_length": 0,       # Kapasitas fisik ruang tunggu maksimum
        "operational_cost": 500000,  # Biaya tetap operasional per skenario
        "opportunity_loss": 150000   # Biaya peluang hilang per kendaraan yang ditolak (Balking Cost)
    }
    
    for col, default_val in extended_metrics.items():
        if col not in df.columns:
            df[col] = default_val

    # Perhitungan Variabel Turunan Operasional & Finansial
    # Waktu Pelayanan aktual (Wt) = Waktu Total (Ws) - Waktu Tunggu (Wq)
    df["avg_service_time"] = (df["avgtimeinsystem"] - df["avgwaitingtime"]).clip(lower=0)
    
    # Pendapatan kotor diestimasikan Rp 350.000 per unit kendaraan yang selesai diproses
    revenue_per_unit = 350000 
    df["estimated_revenue"] = df["carsfinished"] * revenue_per_unit
    df["total_opportunity_loss"] = df["carsrejected"] * df["opportunity_loss"]
    df["net_profit"] = df["estimated_revenue"] - df["operational_cost"] - df["total_opportunity_loss"]

    # =========================================================================
    # KONTROL FILTER SKENARIO
    # =========================================================================
    if "scenario" in df.columns:
        scenario_list = df["scenario"].dropna().unique().tolist()
        selected_scenario = st.sidebar.multiselect(
            "Filter Skenario Analisis",
            scenario_list,
            default=scenario_list
        )
        if selected_scenario:
            df = df[df["scenario"].isin(selected_scenario)]

    # =========================================================================
    # 1. MATRIKS KINERJA OPERASIONAL (TEORI ANTRIAN)
    # =========================================================================
    st.subheader("1. Indikator Kinerja Operasional Utama (Key Operational Indicators)")
    
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.metric("Rata-rata Waktu Tunggu ($W_q$)", f"{df['avgwaitingtime'].mean():.2f} Menit")
    with m_col2:
        st.metric("Rata-rata Waktu Pelayanan ($W_t$)", f"{df['avg_service_time'].mean():.2f} Menit")
    with m_col3:
        st.metric("Rata-rata Panjang Antrian ($L_q$)", f"{df['avg_queue_length'].mean():.2f} Unit")
    with m_col4:
        st.metric("Total Volume Output (Selesai)", f"{df['carsfinished'].sum():,.0f} Unit")
    with m_col5:
        st.metric("Total Volume Penolakan (Balking)", f"{df['carsrejected'].sum():,.0f} Unit")

    # =========================================================================
    # 2. EVALUASI EKONOMI & KELAYAKAN FINANSIAL
    # =========================================================================
    st.subheader("2. Analisis Dampak Ekonomi & Kelayakan Finansial")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        st.metric("Estimasi Pendapatan Kotor", f"Rp {df['estimated_revenue'].sum():,.0f}")
    with f_col2:
        st.metric("Total Biaya Operasional Fixed", f"Rp {df['operational_cost'].sum():,.0f}")
    with f_col3:
        st.metric("Total Biaya Peluang Hilang", f"Rp {df['total_opportunity_loss'].sum():,.0f}")
    with f_col4:
        total_profit = df['net_profit'].sum()
        st.metric("Margin Keuntungan Bersih (Net Profit)", f"Rp {total_profit:,.0f}")

    # =========================================================================
    # 3. ANALISIS KAPASITAS & SATURASI SISTEM
    # =========================================================================
    st.subheader("3. Analisis Kapasitas & Tingkat Saturasi Fasilitas")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns([1, 1, 2])
    total_cars = df["carsfinished"].sum() + df["carsrejected"].sum()
    service_rate = ((df["carsfinished"].sum() / total_cars) * 100) if total_cars > 0 else 0
    avg_util = df["utilization"].mean()

    with col_kpi1:
        st.metric("Rasio Keberhasilan Sistem (Service Rate)", f"{service_rate:.2f}%")
    with col_kpi2:
        st.metric("Rata-rata Efisiensi Utilisasi ($\\rho$)", f"{avg_util * 100:.2f}%")
    with col_kpi3:
        # Penilaian Status Berdasarkan Batas Akademis Manajemen Operasional
        if avg_util < 0.50:
            st.info("Keterangan: Fasilitas mengalami *Underutilization* (Kapasitas menganggur tinggi, inefisiensi biaya).")
        elif avg_util < 0.85:
            st.success("Keterangan: Fasilitas berada pada Kondisi Optimal (Keseimbangan antara keandalan sistem dan efisiensi biaya).")
        else:
            st.warning("Keterangan: Fasilitas mendekati Titik Jenuh / *Saturasi* (Risiko ketidakstabilan antrian stochastic tinggi).")

    # =========================================================================
    # 4. ANALISIS KEPUTUSAN MULTI-KRITERIA (MULTIPLE-CRITERIA DECISION ANALYSIS)
    # =========================================================================
    if len(df) > 0 and "scenario" in df.columns:
        st.subheader("4. Evaluasi Skenario Berdasarkan Pendekatan Multi-Kriteria")
        
        best_ops = df.loc[df["avgwaitingtime"].idxmin()]
        best_biz = df.loc[df["net_profit"].idxmax()]
        
        col_eval1, col_eval2 = st.columns(2)
        with col_eval1:
            st.markdown(f"""
            <div style="border: 1px solid #d4edda; padding: 15px; border-radius: 5px; background-color: #f8f9fa;">
                <h4 style="color: #28a745; margin-top:0;">Skenario Optimum (Dimensi Kinerja Operasional)</h4>
                <ul>
                    <li><b>Identitas Skenario:</b> {best_ops['scenario']}</li>
                    <li><b>Alokasi Server:</b> {best_ops['num_servers']} Mekanik</li>
                    <li><b>Minimalisasi Waktu Tunggu ($W_q$):</b> {best_ops['avgwaitingtime']:.2f} Menit</li>
                    <li><b>Proyeksi Keuntungan Bersih:</b> Rp {best_ops['net_profit']:,.0f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col_eval2:
            st.markdown(f"""
            <div style="border: 1px solid #cce5ff; padding: 15px; border-radius: 5px; background-color: #f8f9fa;">
                <h4 style="color: #004085; margin-top:0;">Skenario Optimum (Dimensi Profitabilitas Bisnis)</h4>
                <ul>
                    <li><b>Identitas Skenario:</b> {best_biz['scenario']}</li>
                    <li><b>Alokasi Server:</b> {best_biz['num_servers']} Mekanik</li>
                    <li><b>Waktu Tunggu Efektif ($W_q$):</b> {best_biz['avgwaitingtime']:.2f} Menit</li>
                    <li><b>Maksimalisasi Keuntungan Bersih:</b> Rp {best_biz['net_profit']:,.0f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # 5. VISUALISASI DATA & DISTRIBUSI MATRIKS
    # =========================================================================
    st.subheader("5. Visualisasi Grafis dan Distribusi Korelatif Skenario")
    vis_tab1, vis_tab2, vis_tab3 = st.tabs(["Korelasi Operasional", "Komparasi Finansial", "Analisis Distribusi Variabel"])
    
    with vis_tab1:
        fig_ops = go.Figure()
        fig_ops.add_trace(go.Bar(x=df["scenario"], y=df["avgwaitingtime"], name="Waktu Tunggu Wq (Menit)", marker_color='#1f77b4'))
        fig_ops.add_trace(go.Scatter(x=df["scenario"], y=df["avg_queue_length"], name="Panjang Antrian Lq (Unit)", yaxis="y2", line=dict(color='#ff7f0e', width=3)))
        
        fig_ops.update_layout(
            title="Analisis Dual-Axis: Hubungan Waktu Tunggu terhadap Panjang Antrian Fisik",
            xaxis=dict(title="Skenario Pengujian"),
            yaxis=dict(title="Skala Waktu Tunggu (Menit)"),
            yaxis2=dict(title="Skala Jumlah Unit Kendaraan", overlaying="y", side="right"),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ops, use_container_width=True)
        
    with vis_tab2:
        fig_fin = px.bar(
            df, x="scenario", y="net_profit", 
            color="net_profit",
            color_continuous_scale="Blues",
            title="Komparasi Efisiensi Profitabilitas Bersih Antar Skenario",
            labels={"net_profit": "Net Profit (Rupiah)", "scenario": "Skenario"}
        )
        fig_fin.update_layout(template="plotly_white")
        st.plotly_chart(fig_fin, use_container_width=True)
        
    with vis_tab3:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            x_axis = st.selectbox("Variabel Independen (Sumbu X)", numeric_cols, index=numeric_cols.index("utilization") if "utilization" in numeric_cols else 0)
        with col_sel2:
            y_axis = st.selectbox("Variabel Dependen (Sumbu Y)", numeric_cols, index=numeric_cols.index("net_profit") if "net_profit" in numeric_cols else 1)
        
        fig_scatter = px.scatter(
            df, x=x_axis, y=y_axis, color="scenario", size="carsfinished",
            title=f"Analisis Sebaran Spasial: Korelasi antara {x_axis} dan {y_axis}",
            labels={x_axis: x_axis.replace('_', ' ').title(), y_axis: y_axis.replace('_', ' ').title()}
        )
        fig_scatter.update_layout(template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # =========================================================================
    # 6. SINTESIS AKADEMIK & IMPLIKASI MANAJERIAL
    # =========================================================================
    if len(df) > 0 and "scenario" in df.columns:
        st.subheader("6. Sintesis Analisis & Implikasi Manajerial")
        
        if best_ops['scenario'] == best_biz['scenario']:
            kesimpulan_teks = f"Berdasarkan data empiris hasil pengujian, skenario **{best_biz['scenario']}** didapati sebagai solusi dominan (*dominant solution*). Skenario ini secara simultan mereduksi kemacetan operasional pada titik minimum sekaligus menghasilkan utilitas ekonomi paling optimal."
        else:
            kesimpulan_teks = f"Hasil analisis menunjukkan adanya fenomena *Trade-Off* struktural antara efisiensi pelayanan operasional dan maksimasi profitabilitas. Skenario **{best_ops['scenario']}** unggul dalam menjaga kepuasan pelanggan melalui minimasi *lead time* ($W_q$). Sebaliknya, jika prioritas manajemen bertumpu pada efisiensi anggaran korporasi, skenario **{best_biz['scenario']}** direkomendasikan karena menghasilkan yield finansial tertinggi, meskipun mengorbankan parameter kepuasan waktu tunggu searah dengan peningkatan probabilitas penolakan kendaraan (*balking rate*)."

        st.markdown(f"""
        ### Ringkasan Eksekutif (Executive Summary):
        {kesimpulan_teks}
        
        ### Rekomendasi Kebijakan Strategis:
        1. **Pencegahan Kongesti Sistem:** Skenario dengan tingkat utilitas ($\rho$) melebihi batas kritis 85% memerlukan intervensi berupa fleksibilitas kapasitas (contoh: mekanik cadangan paruh waktu) guna menekan lonjakan *Opportunity Loss* akibat tingginya tingkat *balking* pelanggan.
        2. **Standardisasi Alokasi Sumber Daya:** Rekomendasi pemilihan skenario terbaik wajib diintegrasikan dengan ketersediaan ruang fisik area tunggu aktual bengkel demi mencegah luapan antrian kendaraan ke area publik.
        """)

    # =========================================================================
    # 7. TABEL DATASET UTAMA
    # =========================================================================
    st.subheader("7. Lampiran Data Matriks Komprehensif")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Sistem siap menerima input. Harap mengunggah dataset empiris simulasi antrian melalui panel konfigurasi di sebelah kiri.")
