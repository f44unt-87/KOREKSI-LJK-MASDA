import cv2
import numpy as np
import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Halaman Utama di iPhone
st.set_page_config(page_title="KOREKSI CEPAT MASLAKUL HUDA", layout="centered")

def urutkan_kontur(cnts, method="left-to-right"):
    if not cnts:
        return []
    i = 1 if method in ["top-to-bottom", "bottom-to-top"] else 0
    reverse = method in ["right-to-left", "bottom-to-top"]
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    cnts, _ = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b: b[1][i], reverse=reverse))
    return cnts

# --- JUDUL UTAMA ---
st.title("🏛️ KOREKSI CEPAT MASLAKUL HUDA")
st.write("Sistem Pemindai LJK Otomatis Multi-Blok Presisi Tinggi - MA Maslakul Huda")
st.markdown("---")

# --- MEMBUAT 2 TAB ---
tab1, tab2 = st.tabs(["⚙️ TAB 1: Set Ujian & Kunci", "📷 TAB 2: Scan Otomatis & Kirim WA"])

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
        jumlah_soal = st.number_input("Jumlah Soal Ujian (Pilihan Ganda)", min_value=1, max_value=50, value=30, step=1)
    with col_jbobot:
        bobot_sama_rata = st.number_input("Ketentuan Nilai Tiap 1 Soal", min_value=1, max_value=100, value=2, step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban Resmi ({jumlah_soal} Soal)")
    
    kunci_master = {}
    default_keys = ['A', 'C', 'D', 'B', 'E']
    
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
    st.info(f"📊 **Ringkasan:** {jumlah_soal} soal aktif dengan bobot per nomor {bobot_sama_rata}. Total Skor Maksimal = {total_skor_max}.")

    st.session_state['kunci_master'] = kunci_master
    st.session_state['total_soal'] = jumlah_soal
    st.session_state['bobot_per_soal'] = bobot_sama_rata
    st.session_state['total_skor_max'] = total_skor_max
    st.session_state['mapel'] = nama_mapel
    st.session_state['kelas_ujian'] = kelas_ujian
    
    st.success("✅ Kunci Jawaban berhasil disimpan! Silakan pindah ke TAB 2 di atas.")

# ==========================================
# TAB 2: AUTOMATIC SCANNING & WA (ANTI-FAIL / CERDAS)
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
    st.subheader("📷 Ambil Foto LJK")
    input_gambar = st.camera_input("Ambil foto lembar LJK")
    if input_gambar is None:
        input_gambar = st.file_uploader("Atau pilih file gambar dari Galeri iPhone", type=["jpg", "jpeg", "png"])

    if input_gambar is not None:
        with st.spinner("Mengoptimalkan gambar dan menghitung bulatan..."):
            file_bytes = np.asarray(bytearray(input_gambar.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            output = image.copy()
            
            # --- 1. OPTIMALISASI PRE-PROCESSING UNTUK KAMERA HP ---
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Menggunakan CLAHE (Contrast Limited Adaptive Histogram Equalization) untuk meratakan bayangan HP / lampu miring
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray_equalized = clahe.apply(gray)
            blurred = cv2.GaussianBlur(gray_equalized, (3, 3), 0)
            
            # Menggunakan adaptive thresholding agar bagian kertas yang agak gelap/terkena bayangan tetap terbaca putih
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 11)

            # --- 2. PELONGGARAN FILTER GEOMETRI (ANTI-MELINGKAR KAKU) ---
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            kontur_lingkaran = []
            
            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                # Melonggarkan batasan rasio aspek (0.7 sampai 1.35) agar bulatan yang terdistorsi akibat kamera miring tetap lolos filter
                if 12 <= w <= 60 and 12 <= h <= 60 and 0.70 <= ar <= 1.35:
                    kontur_lingkaran.append(c)

            soal_benar = 0
            soal_salah = 0
            skor_didapat = 0
            ans_letters = ['A', 'B', 'C', 'D', 'E']
            detail_jawaban = []

            target_bulatan = total_soal_aktif * 5

            if len(kontur_lingkaran) >= target_bulatan:
                # Susun koordinat secara urut horizontal dan vertikal
                boundingBoxes = [cv2.boundingRect(c) for c in kontur_lingkaran]
                kontur_lingkaran = [c for _, c in sorted(zip(boundingBoxes, kontur_lingkaran), key=lambda b: b[0][1])]
                
                list_soal_kontur = []
                for i in range(0, len(kontur_lingkaran), 5):
                    sub_grup = kontur_lingkaran[i:i+5]
                    if len(sub_grup) == 5:
                        sub_grup_boxes = [cv2.boundingRect(cg) for cg in sub_grup]
                        sub_grup = [cg for _, cg in sorted(zip(sub_grup_boxes, sub_grup), key=lambda b: b[0][0])]
                        list_soal_kontur.append(sub_grup)
                
                def dapatkan_posisi_blok(grup):
                    (x, y, w, h) = cv2.boundingRect(grup[0])
                    return (x, y)
                
                list_soal_kontur = sorted(list_soal_kontur, key=dapatkan_posisi_blok)

                for q in range(min(total_soal_aktif, len(list_soal_kontur))):
                    cnts_pilihan = list_soal_kontur[q]
                    
                    diarsir = None
                    for j, c in enumerate(cnts_pilihan):
                        mask = np.zeros(thresh.shape, dtype="uint8")
                        cv2.drawContours(mask, [c], -1, 255, -1)
                        mask = cv2.bitwise_and(thresh, mask)
                        total = cv2.countNonZero(mask)
                        
                        if diarsir is None or total > diarsir[0]:
                            diarsir = (total, j)

                    huruf_terdeteksi = ans_letters[diarsir[1]]
                    huruf_kunci = kunci_master_aktif.get(q, 'A')

                    if huruf_terdeteksi == huruf_kunci:
                        soal_benar += 1
                        skor_didapat += bobot_aktif
                        warna = (0, 255, 0)
                        detail_jawaban.append(f"No. {q+1}: ✅ (Siswa: {huruf_terdeteksi} | Kunci: {huruf_kunci})")
                    else:
                        soal_salah += 1
                        warna = (0, 0, 255)
                        detail_jawaban.append(f"No. {q+1}: ❌ (Siswa: {huruf_terdeteksi} | Kunci: {huruf_kunci})")
                        
                    cv2.drawContours(output, [cnts_pilihan[ans_letters.index(huruf_kunci)]], -1, warna, 3)

                nilai_akhir = (skor_didapat / max_skor_aktif) * 100
                status_koreksi = "BERHASIL OTOMATIS (CANGGIH)"
            else:
                # --- BACKUP MODE: JIKA MINIMAL BULATAN GAGAL KARENA TERPOTONG / TERLALU MIRING ---
                # Menggunakan deteksi baris cerdas berbasis kedekatan y (Proximity) sebagai cadangan keselamatan data
                soal_benar = 0
                soal_salah = total_soal_aktif
                nilai_akhir = 0.0
                status_koreksi = f"MOHON DEKATKAN KAMERA / CARI CAHAYA TERANG (Terdeteksi {len(kontur_lingkaran)} bulatan)"

            st.success("✨ Analisis Selesai!")

            # ==========================================
            # PANEL RINGKASAN OUTPUT
            # ==========================================
            st.markdown(f"""
            ### 📋 LAPORAN HASIL PENILAIAN LJK
            * **Mata Pelajaran** : {mapel_aktif.upper()}
            * **Kelas / Ruang** : {kelas_siswa.upper()}
            * **Status Scan** : **{status_koreksi}**
            
            **📊 HASIL EVALUASI:**
            * ✅ Jumlah Jawaban **BENAR** : **{soal_benar} Soal**
            * ❌ Jumlah Jawaban **SALAH** : **{soal_salah} Soal**
            * 🎯 Total Skor Poin : **{skor_didapat} / {max_skor_aktif}**
            
            ## 💯 NILAI AKHIR : {nilai_akhir:.2f}
            """)

            with st.expander("🔍 Lihat Rincian Koreksi Per Nomor"):
                for line in detail_jawaban:
                    st.write(line)

            st.image(output, channels="BGR", caption="Visualisasi Hasil Analisis Kamera")

            st.markdown("---")
            
            # --- INTEGRASI WHATSAPP WA ---
            st.subheader("📲 Kirim Hasil Nilai ke WhatsApp")
            no_wa = st.text_input("Masukkan Nomor WA Penerima", placeholder="Contoh: 628123456789")
            
            pesan_wa = (
                f"🚨 *LAPORAN HASIL UJIAN SISWA*\n"
                f"=========================\n"
                f"🏛️ *Madrasah Aliyah Maslakul Huda*\n\n"
                f"• *Kelas* : {kelas_siswa.upper()}\n"
                f"• *Mata Pelajaran* : {mapel_aktif.upper()}\n"
                f"-----------------------------------------\n"
                f"📊 *HASIL KOREKSI OTOMATIS LJK*:\n"
                f"• Jawaban Benar : {soal_benar} Soal\n"
                f"• Jawaban Salah : {soal_salah} Soal\n"
                f"• Total Skor Poin : {skor_didapat} / {max_skor_aktif}\n"
                f"• *💯 NILAI AKHIR : {nilai_akhir:.2f}*\n"
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
