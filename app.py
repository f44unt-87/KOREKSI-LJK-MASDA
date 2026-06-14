import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Halaman Utama di iPhone
st.set_page_config(page_title="KOREKSI CEPAT MASLAKUL HUDA", layout="centered")

# --- JUDUL UTAMA ---
st.title("🏛️ KOREKSI CEPAT MASLAKUL HUDA")
st.write("Aplikasi Bantu Koreksi LJK Multi-Soal & Kirim Nilai via WhatsApp")
st.markdown("---")

# --- MEMBUAT 2 TAB ---
tab1, tab2 = st.tabs(["⚙️ TAB 1: Set Ujian & Kunci", "📝 TAB 2: Input Jawaban & Kirim WA"])

# ==========================================
# TAB 1: PENGATURAN MAPEL, JUMLAH SOAL & KUNCI
# ==========================================
with tab1:
    st.subheader("📋 Informasi Ujian")
    nama_mapel = st.text_input("Nama Mata Pelajaran", value="Fiqih")
    kelas_ujian = st.text_input("Kelas / Ruang", value="10-E1")
    
    st.subheader("🔢 Konfigurasi Penilaian")
    col_jsoal, col_jbobot = st.columns(2)
    with col_jsoal:
        jumlah_soal = st.number_input("Masukkan Jumlah Soal Ujian", min_value=1, max_value=50, value=30, step=1)
    with col_jbobot:
        bobot_sama_rata = st.number_input("Ketentuan Nilai Tiap 1 Soal", min_value=1, max_value=100, value=2, step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban Resmi ({jumlah_soal} Soal)")
    st.write("Semua nomor otomatis diatur awal ke posisi B untuk mempermudah pengisian:")
    
    kunci_master = {}
    for base_idx in range(0, jumlah_soal, 5):
        cols = st.columns(5)
        for sub_idx in range(5):
            idx = base_idx + sub_idx
            if idx < jumlah_soal:
                with cols[sub_idx]:
                    pilihan = st.selectbox(
                        f"Soal {idx+1}", 
                        ['A', 'B', 'C', 'D', 'E'], 
                        index=1, # Default ke B
                        key=f"master_kunci_{idx}"
                    )
                    kunci_master[idx] = pilihan
            
    total_skor_max = jumlah_soal * bobot_sama_rata
    st.info(f"📊 **Ringkasan:** {jumlah_soal} soal aktif dengan bobot per nomor {bobot_sama_rata}. Total Skor Maksimal = {total_skor_max}.")

    # Simpan ke session state
    st.session_state['kunci_master'] = kunci_master
    st.session_state['total_soal'] = jumlah_soal
    st.session_state['bobot_per_soal'] = bobot_sama_rata
    st.session_state['total_skor_max'] = total_skor_max
    st.session_state['mapel'] = nama_mapel
    st.session_state['kelas_ujian'] = kelas_ujian
    
    st.success("✅ Kunci Jawaban dan aturan bobot berhasil disimpan! Silakan pindah ke TAB 2 di atas.")

# ==========================================
# TAB 2: INPUT JAWABAN SISWA & WHATSAPP (SISTEM INPUT KILAT)
# ==========================================
with tab2:
    total_soal_aktif = st.session_state.get('total_soal', 30)
    kunci_master_aktif = st.session_state.get('kunci_master', {})
    bobot_aktif = st.session_state.get('bobot_per_soal', 2)
    max_skor_aktif = st.session_state.get('total_skor_max', 60)
    mapel_aktif = st.session_state.get('mapel', "Fiqih")
    kelas_ujian_aktif = st.session_state.get('kelas_ujian', "10-E1")

    st.subheader("📋 Data Kelas")
    kelas_siswa = st.text_input("Kelas / Ruang Siswa", value=kelas_ujian_aktif)

    st.markdown("---")
    st.subheader("📷 Bukti Arsip LJK (Opsional)")
    input_gambar = st.camera_input("Ambil Foto Kertas LJK (Sebagai dokumentasi arsip)")
    if input_gambar is None:
        input_gambar = st.file_uploader("Atau upload file dari Galeri iPhone", type=["jpg", "jpeg", "png"])

    st.markdown("---")
    st.subheader("✍️ Input Pilihan Jawaban Siswa")
    st.info("💡 Semua nomor di bawah ini sudah otomatis memilih **B**. Anda hanya perlu mengubah nomor yang jawabannya selain B!")

    jawaban_siswa = {}
    # Menampilkan pilihan input yang berurutan rapi sesuai nomor 1 sampai terakhir
    for base_idx in range(0, total_soal_aktif, 5):
        cols = st.columns(5)
        for sub_idx in range(5):
            idx = base_idx + sub_idx
            if idx < total_soal_aktif:
                with cols[sub_idx]:
                    pilihan_siswa = st.radio(
                        f"No. {idx+1}",
                        ['A', 'B', 'C', 'D', 'E'],
                        index=1, # Otomatis langsung mengarah ke B sejak awal
                        key=f"siswa_ans_{idx}"
                    )
                    jawaban_siswa[idx] = pilihan_siswa

    st.markdown("---")
    
    # --- PROSES HITUNG INSTAN ---
    if st.button("🚀 HITUNG JAWABAN & NILAI AKHIR", type="primary"):
        soal_benar = 0
        soal_salah = 0
        skor_didapat = 0
        detail_koreksi = []

        for idx in range(total_soal_aktif):
            kunci_benar = kunci_master_aktif.get(idx, 'B')
            ans_siswa = jawaban_siswa.get(idx, 'B')
            
            if ans_siswa == kunci_benar:
                soal_benar += 1
                skor_didapat += bobot_aktif
                detail_koreksi.append(f"No. {idx+1}: ✅ (Siswa: {ans_siswa} | Kunci: {kunci_benar})")
            else:
                soal_salah += 1
                detail_koreksi.append(f"No. {idx+1}: ❌ (Siswa: {ans_siswa} | Kunci: {kunci_benar})")

        # Kalkulasi Nilai Akhir
        nilai_final = (skor_didapat / max_skor_aktif) * 100

        st.success("🎉 Hasil Penilaian Berhasil Dihitung dengan Akurasi 100%!")
        
        # Tampilan Box Laporan Hasil Penilaian
        st.markdown(f"""
        ### 📋 LAPORAN HASIL PENILAIAN LJK
        * **Mata Pelajaran** : {mapel_aktif.upper()}
        * **Kelas / Ruang** : {kelas_siswa.upper()}
        
        **📊 HASIL EVALUASI REALSTIS:**
        * ✅ Jumlah Jawaban **BENAR** : **{soal_benar} Soal**
        * ❌ Jumlah Jawaban **SALAH** : **{soal_salah} Soal**
        * 🎯 Total Skor Poin : **{skor_didapat} / {max_skor_aktif} Poin**
        
        ## 💯 NILAI AKHIR: {nilai_final:.2f}
        """)
        
        with st.expander("🔍 Lihat Analisis Jawaban Per Nomor"):
            for line in detail_koreksi:
                st.write(line)

        # --- INTEGRASI OUTBOUND WHATSAPP ---
        st.subheader("📲 Kirim Hasil Nilai ke WhatsApp")
        no_wa_raw = st.text_input("Masukkan Nomor WA Penerima", value="081353539600")
        
        no_wa_clean = no_wa_raw.strip()
        if no_wa_clean.startswith("0"):
            no_wa_clean = "62" + no_wa_clean[1:]
            
        pesan_wa = (
            f"🚨 *LAPORAN HASIL UJIAN SISWA*\n"
            f"=========================\n"
            f"🏛️ *Madrasah Aliyah Maslakul Huda*\n\n"
            f"• *Kelas* : {kelas_siswa.upper()}\n"
            f"• *Mata Pelajaran* : {mapel_aktif.upper()}\n"
            f"-----------------------------------------\n"
            f"📊 *HASIL KOREKSI PENILAIAN LJK*:\n"
            f"• Jawaban Benar : {soal_benar} Soal\n"
            f"• Jawaban Salah : {soal_salah} Soal\n"
            f"• Total Skor Poin : {skor_didapat} / {max_skor_aktif}\n"
            f"• *💯 NILAI AKHIR : {nilai_final:.2f}*\n"
            f"=========================\n"
            f"_Pesan dikirim resmi melalui Aplikasi Koreksi Cepat Maslakul Huda._"
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
