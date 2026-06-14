import cv2
import numpy as np
import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Halaman Utama di iPhone
st.set_page_config(page_title="KOREKSI CEPAT MASLAKUL HUDA", layout="centered")

# --- JUDUL UTAMA ---
st.title("🏛️ KOREKSI CEPAT MASLAKUL HUDA")
st.write("Aplikasi Bantu Koreksi LJK Terintegrasi WhatsApp - MA Maslakul Huda")
st.markdown("---")

# --- MEMBUAT 2 TAB ---
tab1, tab2 = st.tabs(["⚙️ TAB 1: Set Ujian & Kunci", "📝 TAB 2: Input Jawaban Siswa & Kirim WA"])

# ==========================================
# TAB 1: PENGATURAN MAPEL, JUMLAH SOAL & KUNCI
# ==========================================
with tab1:
    st.subheader("📋 Informasi Mata Pelajaran")
    nama_mapel = st.text_input("Nama Mata Pelajaran", value="Fiqih")
    kelas_ujian = st.text_input("Kelas Ujian / Ruang", value="11-A")
    
    st.subheader("🔢 Konfigurasi Ujian")
    col_jsoal, col_jbobot = st.columns(2)
    with col_jsoal:
        jumlah_soal = st.number_input("Jumlah Soal Ujian (Pilihan Ganda)", min_value=1, max_value=50, value=10, step=1)
    with col_jbobot:
        bobot_sama_rata = st.number_input("Ketentuan Nilai Tiap 1 Soal", min_value=1, max_value=100, value=10, step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban Resmi ({jumlah_soal} Soal)")
    st.write("Tentukan kunci jawaban yang benar untuk acuan penilaian:")
    
    kunci_master = {}
    default_keys = ['A', 'B', 'C', 'D', 'E']
    
    # Menampilkan grid kunci jawaban yang urut dari nomor 1 sampai terakhir
    for base_idx in range(0, jumlah_soal, 5):
        cols = st.columns(5)
        for sub_idx in range(5):
            idx = base_idx + sub_idx
            if idx < jumlah_soal:
                with cols[sub_idx]:
                    def_val = default_keys[idx % len(default_keys)]
                    pilihan = st.selectbox(
                        f"Soal {idx+1}", 
                        ['A', 'B', 'C', 'D', 'E'], 
                        index=['A', 'B', 'C', 'D', 'E'].index(def_val), 
                        key=f"master_kunci_{idx}"
                    )
                    kunci_master[idx] = pilihan
            
    total_skor_max = jumlah_soal * bobot_sama_rata
    st.info(f"📊 **Ringkasan:** Total {jumlah_soal} soal dengan nilai kelipatan {bobot_sama_rata}. Total Skor Maksimal = {total_skor_max}.")

    # Simpan ke session state
    st.session_state['kunci_master'] = kunci_master
    st.session_state['total_soal'] = jumlah_soal
    st.session_state['bobot_per_soal'] = bobot_sama_rata
    st.session_state['total_skor_max'] = total_skor_max
    st.session_state['mapel'] = nama_mapel
    st.session_state['kelas_ujian'] = kelas_ujian
    
    st.success("✅ Kunci Jawaban Ujian berhasil disimpan! Silakan pindah ke TAB 2 di atas.")

# ==========================================
# TAB 2: INPUT JAWABAN SISWA & WHATSAPP
# ==========================================
with tab2:
    st.subheader("👤 Identitas Siswa")
    st.write("Silakan masukkan identitas siswa yang sedang dikoreksi:")
    
    col_nama, col_kelas = st.columns([2, 1])
    with col_nama:
        nama_siswa = st.text_input("Nama Lengkap Siswa", placeholder="Contoh: Ahmad Rehan Fadilah")
    with col_kelas:
        kelas_siswa = st.text_input("Kelas", value=st.session_state.get('kelas_ujian', ""))

    st.markdown("---")
    st.subheader("📷 Bukti Arsip LJK (Opsional)")
    input_gambar = st.camera_input("Ambil Foto Kertas LJK (Sebagai dokumentasi arsip)")
    if input_gambar is None:
        input_gambar = st.file_uploader("Atau upload file dari Galeri iPhone", type=["jpg", "jpeg", "png"])

    st.markdown("---")
    
    # Ambil data dari TAB 1
    total_soal_aktif = st.session_state.get('total_soal', 10)
    kunci_master_aktif = st.session_state.get('kunci_master', {})
    bobot_aktif = st.session_state.get('bobot_per_soal', 10)
    max_skor_aktif = st.session_state.get('total_skor_max', 100)
    mapel_aktif = st.session_state.get('mapel', "Fiqih")

    st.subheader(f"✍️ Input Pilihan Jawaban {nama_siswa if nama_siswa else 'Siswa'}")
    st.write("Ketuk pilihan huruf sesuai dengan lembar jawaban asli siswa di kertas:")

    jawaban_siswa = {}
    # Menampilkan tombol pilihan jawaban siswa secara berurutan nomor 1 sampai terakhir
    for base_idx in range(0, total_soal_aktif, 5):
        cols = st.columns(5)
        for sub_idx in range(5):
            idx = base_idx + sub_idx
            if idx < total_soal_aktif:
                with cols[sub_idx]:
                    pilihan_siswa = st.radio(
                        f"No. {idx+1}",
                        ['A', 'B', 'C', 'D', 'E'],
                        index=0,
                        key=f"siswa_ans_{idx}"
                    )
                    jawaban_siswa[idx] = pilihan_siswa

    st.markdown("---")
    
    # --- PROSES HITUNG OTOMATIS ---
    if st.button("🚀 HITUNG NILAI AKHIR", type="primary"):
        if not nama_siswa.strip():
            st.error("⚠️ Mohon isi Nama Lengkap Siswa terlebih dahulu!")
        else:
            soal_benar = 0
            skor_didapat = 0
            detail_koreksi = []

            for idx in range(total_soal_aktif):
                kunci_benar = kunci_master_aktif.get(idx, 'A')
                ans_siswa = jawaban_siswa.get(idx, 'A')
                
                if ans_siswa == kunci_benar:
                    soal_benar += 1
                    skor_didapat += bobot_aktif
                    detail_koreksi.append(f"No. {idx+1}:  (Siswa: {ans_siswa} | Kunci: {kunci_benar})")
                else:
                    detail_koreksi.append(f"No. {idx+1}: ❌ (Siswa: {ans_siswa} | Kunci: {kunci_benar})")

            nilai_final = (skor_didapat / max_skor_aktif) * 100

            st.success(f"🎉 Penilaian untuk {nama_siswa.upper()} Berhasil Dihitung!")
            
            # Tampilan Box Hasil Laporan
            st.markdown(f"""
            ### 📋 LAPORAN HASIL PENILAIAN
            * **Nama Siswa** : {nama_siswa.upper()}
            * **Kelas** : {kelas_siswa.upper()}
            * **Mata Pelajaran** : {mapel_aktif.upper()}
            
            **🎯 SKOR PEROLEHAN:**
            * Jumlah Benar : **{soal_benar} / {total_soal_aktif} Soal**
            * Total Skor : **{skor_didapat} / {max_skor_aktif} Poin**
            * ## 💯 NILAI AKHIR: {nilai_final:.2f}
            """)
            
            with st.expander("🔍 Lihat Detail Jawaban Benar/Salah"):
                for line in detail_koreksi:
                    st.write(line)

            # --- INTEGRASI WHATSAPP WA ---
            st.subheader("📲 Kirim Hasil Nilai ke WhatsApp")
            no_wa = st.text_input("Masukkan Nomor WA (Wali Murid / Guru)", placeholder="Contoh: 628123456789")
            
            pesan_wa = (
                f"🚨 *LAPORAN HASIL UJIAN SISWA*\n"
                f"=========================\n"
                f"🏛️ *Madrasah Aliyah Maslakul Huda*\n\n"
                f"• *Nama Siswa* : {nama_siswa.upper()}\n"
                f"• *Kelas* : {kelas_siswa.upper()}\n"
                f"• *Mata Pelajaran* : {mapel_aktif.upper()}\n"
                f"-----------------------------------------\n"
                f"📊 *HASIL KOREKSI PENILAIAN*:\n"
                f"• Jumlah Benar : {soal_benar} / {total_soal_aktif} Soal\n"
                f"• Total Skor Poin : {skor_didapat} / {max_skor_aktif}\n"
                f"• *💯 NILAI AKHIR : {nilai_final:.2f}*\n"
                f"=========================\n"
                f"_Pesan dikirim resmi melalui Aplikasi Koreksi Cepat Maslakul Huda._"
            )
            
            pesan_encoded = urllib.parse.quote(pesan_wa)
            link_wa = f"https://api.whatsapp.com/send?phone={no_wa.strip()}&text={pesan_encoded}"

            if no_wa:
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
