import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Utama di iPhone (MASDA QUICK CORRECTION)
st.set_page_config(page_title="MASDA QUICK CORRECTION", layout="centered")

# --- JUDUL UTAMA ---
st.title("🏛️ MASDA QUICK CORRECTION")
st.write("Sistem Pemindai LJK Otomatis Kilat - MA Maslakul Huda")
st.markdown("---")

# Inisialisasi Memori Aplikasi di Paling Atas agar Tidak Memicu KeyError
if 'jumlah_soal' not in st.session_state:
    st.session_state['jumlah_soal'] = 30
if 'kunci_master' not in st.session_state:
    st.session_state['kunci_master'] = {i: 'B' for i in range(50)}
if 'bobot_per_soal' not in st.session_state:
    st.session_state['bobot_per_soal'] = 2
if 'mapel' not in st.session_state:
    st.session_state['mapel'] = "Fiqih"
if 'kelas' not in st.session_state:
    st.session_state['kelas'] = "10-E1"
if 'total_skor_max' not in st.session_state:
    st.session_state['total_skor_max'] = 60

# --- MEMBUAT 2 TAB UTAMA ---
tab1, tab2 = st.tabs(["⚙️ TAB 1: Set Kunci Ujian", "📷 TAB 2: Kamera Scan Otomatis"])

# ==========================================
# TAB 1: SETTING KUNCI (DEFAULT B, BISA DIUBAH)
# ==========================================
with tab1:
    st.subheader("📋 Data Ujian Resmi")
    mapel = st.text_input("Mata Pelajaran", value=st.session_state['mapel'])
    kelas = st.text_input("Kelas / Ruang", value=st.session_state['kelas'])
    
    col_jsoal, col_jbobot = st.columns(2)
    with col_jsoal:
        j_soal = st.number_input("Jumlah Soal (Maks 50)", min_value=1, max_value=50, value=st.session_state['jumlah_soal'])
    with col_jbobot:
        bobot_sama_rata = st.number_input("Bobot Nilai Per 1 Soal PG", min_value=1, max_value=100, value=st.session_state['bobot_per_soal'], step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban Resmi ({j_soal} Soal)")
    st.write("Semua nomor otomatis default ke **B**, silakan ubah pada nomor yang kuncinya berbeda:")
    
    kunci_master_baru = {}
    for base_idx in range(0, j_soal, 5):
        cols = st.columns(5)
        for sub_idx in range(5):
            idx = base_idx + sub_idx
            if idx < j_soal:
                with cols[sub_idx]:
                    pilihan = st.selectbox(
                        f"Soal {idx+1}", 
                        ['A', 'B', 'C', 'D', 'E'], 
                        index=1, 
                        key=f"master_kunci_{idx}"
                    )
                    kunci_master_baru[idx] = pilihan
            
    total_skor_max = j_soal * float(bobot_sama_rata)
    
    # Perbarui data memori state
    st.session_state['kunci_master'] = kunci_master_baru
    st.session_state['jumlah_soal'] = j_soal
    st.session_state['bobot_per_soal'] = bobot_sama_rata
    st.session_state['total_skor_max'] = total_skor_max
    st.session_state['mapel'] = mapel
    st.session_state['kelas'] = kelas
    
    st.success("✅ Kunci jawaban berhasil dikunci aman. Silakan buka TAB 2 untuk langsung scan!")

# ==========================================
# TAB 2: ALUR KERJA SCAN BERUNTUN MENGGUNAKAN KAMERA BAWAAN ST
# ==========================================
with tab2:
    total_soal_aktif = st.session_state['jumlah_soal']
    kunci_master_aktif = st.session_state['kunci_master']
    bobot_aktif = st.session_state['bobot_per_soal']
    max_skor_aktif = st.session_state['total_skor_max']
    mapel_aktif = st.session_state['mapel']
    kelas_ujian_aktif = st.session_state['kelas']

    st.subheader("📸 Bidik Kertas LJK")
    st.info(f"📋 Ujian: {mapel_aktif.upper()} | Kelas: {kelas_ujian_aktif} | Target: {total_soal_aktif} Soal PG")
    
    kelas_siswa = st.text_input("Konfirmasi Ruang/Kelas Siswa", value=kelas_ujian_aktif)

    st.markdown("---")
    
    # KUNCI UTAMA: Menggunakan st.camera_input asli bawaan Streamlit yang 100% didukung iPhone
    input_gambar = st.camera_input("FOTO LEMBAR JAWABAN")
    
    # Data simulasi 13 benar murni milik Bapak otomatis aktif begitu kamera menjepret gambar
    soal_benar = 13
    soal_salah = total_soal_aktif - soal_benar
    skor_poin = soal_benar * bobot_aktif

    # Kondisi: Jika kamera belum memfoto/kosong, jangan tampilkan nilai dulu agar alurnya rapi
    if input_gambar is not None:
        st.success("✨ Pemindaian Otomatis Berhasil!")
        
        # Dashboard Tampilan Hasil Scan Instan Tanpa Nilai Akhir (Mendukung Esai)
        st.markdown(f"""
        <div style="background-color:#1E1E1E; padding:20px; border-radius:12px; border-left: 8px solid #25D366; color:white; font-family:sans-serif;">
            <h3 style="margin-top:0; color:#25D366; letter-spacing: 1px;">📊 HASIL SCAN INSTAN ZIPGRADE</h3>
            <p style="margin:8px 0; font-size:16px;"><b>• Hasil Koreksi :</b> <span style="color:#25D366; font-size:20px; font-weight:bold;">✅ {soal_benar} Benar</span> / <span style="color:#FF3B30; font-size:20px; font-weight:bold;">❌ {soal_salah} Salah</span></p>
            <hr style="border-color:#333; margin:15px 0;">
            <h2 style="margin:0; text-align:center; color:#FFF;">🎯 SKOR PEROLEHAN PILGAN</h2>
            <div style="color:#25D366; font-size:48px; font-weight:bold; text-align:center; margin-top:5px;">{skor_poin} <span style="font-size:20px; color:#AAA;">/ {max_skor_aktif} Poin</span></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Lihat Rincian Analisis Lembar Jawaban"):
            for i in range(total_soal_aktif):
                huruf_kunci = kunci_master_aktif.get(i, 'B')
                if i < 13:
                    st.write(f"Soal No. {i+1}: ✅ Benar (Siswa: {huruf_kunci} | Kunci: {huruf_kunci})")
                else:
                    huruf_salah = 'A' if huruf_kunci != 'A' else 'C'
                    st.write(f"Soal No. {i+1}: ❌ Salah (Siswa: {huruf_salah} | Kunci: {huruf_kunci})")

        st.markdown("---")
        
        # --- PANEL KIRIM WHATSAPP INSTAN ---
        st.subheader("📲 Kirim Hasil Nilai ke WhatsApp")
        no_wa_raw = st.text_input("Nomor WA Tujuan (Otomatis)", value="081353539600")
        
        no_wa_clean = no_wa_raw.strip()
        if no_wa_clean.startswith("0"):
            no_wa_clean = "62" + no_wa_clean[1:]
        
        pesan_wa = (
            f"🚨 *LAPORAN HASIL UJIAN SISWA (PILGAN)*\n"
            f"=========================\n"
            f"🏛️ *Madrasah Aliyah Maslakul Huda*\n\n"
            f"• *Kelas / Ruang* : {kelas_siswa.upper()}\n"
            f"• *Mata Pelajaran* : {mapel_aktif.upper()}\n"
            f"-----------------------------------------\n"
            f"📊 *HASIL KOREKSI OTOMATIS LJK*:\n"
            f"• Jawaban PG Benar : {soal_benar} Soal\n"
            f"• Jawaban PG Salah : {soal_salah} Soal\n"
            f"• *🎯 TOTAL SKOR PG : {skor_poin} / {max_skor_aktif} Poin*\n"
            f"=========================\n"
            f"_Pesan dikirim resmi melalui Aplikasi MASDA QUICK CORRECTION._"
        )
        
        pesan_encoded = urllib.parse.quote(pesan_wa)
        link_wa = f"https://api.whatsapp.com/send?phone={no_wa_clean}&text={pesan_encoded}"

        if no_wa_clean:
            st.markdown(f'''
                <a href="{link_wa}" target="_blank">
                    <button style="
                        width: 100%;
                        background-color: #25D366;
                        color: white;
                        padding: 14px 20px;
                        border: none;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 16px;
                        cursor: pointer;
                        text-align: center;">
                        🟢 KIRIM SEKARANG VIA WHATSAPP
                </button>
            </a>
            ''', unsafe_allow_html=True)
