import cv2
import numpy as np
import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Halaman Utama di iPhone
st.set_page_config(page_title="KOREKSI CEPAT MASLAKUL HUDA", layout="centered")

def proses_satu_kolom_aman(kontur_kolom, thresh, ans_letters):
    """Memproses baris 5 pilihan (A-E) di dalam satu kolom secara aman tanpa memicu crash"""
    if len(kontur_kolom) < 5:
        return []
        
    # Ambil bounding box untuk pengurutan
    boxes = [cv2.boundingRect(c) for c in kontur_kolom]
    
    # Urutkan dari atas ke bawah berdasarkan koordinat Y
    kontur_kolom = [c for _, c in sorted(zip(boxes, kontur_kolom), key=lambda b: b[1][1])]
    
    grup_soal_kolom = []
    while len(kontur_kolom) >= 5:
        anchor_y = cv2.boundingRect(kontur_kolom[0])[1]
        sebaris = []
        sisa = []
        
        # Kelompokkan yang memiliki jarak vertikal dekat (toleransi bergelombang)
        for c in kontur_kolom:
            y_curr = cv2.boundingRect(c)[1]
            if abs(y_curr - anchor_y) < 30:
                sebaris.append(c)
            else:
                sisa.append(c)
                
        if len(sebaris) >= 5:
            # Urutkan dari kiri ke kanan (A, B, C, D, E) secara ketat
            sebaris_boxes = [cv2.boundingRect(cg) for cg in sebaris]
            sebaris = [cg for _, cg in sorted(zip(sebaris_boxes, sebaris), key=lambda b: b[0][0])]
            grup_soal_kolom.append(sebaris[:5])
            
        kontur_kolom = sisa
        if len(sebaris) < 5 and kontur_kolom:
            kontur_kolom.pop(0)
            
    return grup_soal_kolom

# --- JUDUL UTAMA ---
st.title("🏛️ KOREKSI CEPAT MASLAKUL HUDA")
st.write("Sistem Pemindai LJK Otomatis Dinamis Bebas Crash - MA Maslakul Huda")
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
        jumlah_soal = st.number_input("Masukkan Jumlah Soal Ujian", min_value=1, max_value=50, value=30, step=1)
    with col_jbobot:
        bobot_sama_rata = st.number_input("Ketentuan Nilai Tiap 1 Soal", min_value=1, max_value=100, value=2, step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban Resmi ({jumlah_soal} Soal)")
    st.write("Kunci default otomatis di posisi B:")
    
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
                        index=1, 
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
# TAB 2: AUTOMATIC SCANNING & WA (ANTI-CRASH)
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
        with st.spinner("Menganalisis lembar jawaban secara dinamis..."):
            file_bytes = np.asarray(bytearray(input_gambar.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            output = image.copy()
            
            # Pre-processing Gambar
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            
            # Penutupan rongga lingkaran tengah (anti efek donat bolong)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            cnts, _ = cv2.findContours(thresh_closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            mask_solid = np.zeros(thresh.shape, dtype="uint8")
            for c in cnts:
                cv2.drawContours(mask_solid, [c], -1, 255, -1)

            cnts_final, _ = cv2.findContours(mask_solid.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter geometri bulatan LJK yang valid
            kontur_valid = []
            koordinat_x = []
            for c in cnts_final:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                if 12 <= w <= 60 and 12 <= h <= 60 and 0.70 <= ar <= 1.30:
                    kontur_valid.append(c)
                    koordinat_x.append(x)

            soal_benar = 0
            soal_salah = 0
            skor_didapat = 0
            ans_letters = ['A', 'B', 'C', 'D', 'E']
            detail_jawaban = []

            # PROTEKSI UTAMA: Jalankan pencarian otomatis hanya jika terdeteksi bulatan LJK minimal yang masuk akal
            if len(kontur_valid) >= 25:
                # SOLUSI: Menggunakan pembagian 3 wilayah kolom adaptif berdasarkan nilai X minimum & maksimum yang riil terfoto
                min_x, max_x = min(koordinat_x), max(koordinat_x)
                rentang_x = max_x - min_x
                
                batas_kiri_tengah = min_x + (rentang_x * 0.38)
                batas_tengah_kanan = min_x + (rentang_x * 0.68)
                
                raw_kiri = []
                raw_tengah = []
                raw_kanan = []
                
                for c in kontur_valid:
                    x = cv2.boundingRect(c)[0]
                    if x < batas_kiri_tengah:
                        raw_kiri.append(c)
                    elif x < batas_tengah_kanan:
                        raw_tengah.append(c)
                    else:
                        raw_kanan.append(c)

                # Jalankan fungsi sortir aman (kebal dari ValueError kosong)
                grup_kiri = proses_satu_kolom_aman(raw_kiri, thresh, ans_letters)
                grup_tengah = proses_satu_kolom_aman(raw_tengah, thresh, ans_letters)
                grup_kanan = proses_satu_kolom_aman(raw_kanan, thresh, ans_letters)
                
                # Susun ulang sesuai layout lembar kertas Maslakul Huda Anda
                list_soal_kontur_final = grup_kiri + grup_tengah + grup_kanan

                if len(list_soal_kontur_final) > 0:
                    for q in range(min(total_soal_aktif, len(list_soal_kontur_final))):
                        cnts_pilihan = list_soal_kontur_final[q]
                        
                        diarsir = None
                        for j, c in enumerate(cnts_pilihan):
                            mask = np.zeros(thresh.shape, dtype="uint8")
                            cv2.drawContours(mask, [c], -1, 255, -1)
                            mask = cv2.bitwise_and(thresh, mask)
                            total = cv2.countNonZero(mask)
                            
                            if diarsir is None or total > diarsir[0]:
                                diarsir = (total, j)

                        huruf_terdeteksi = ans_letters[diarsir[1]]
                        huruf_kunci = kunci_master_aktif.get(q, 'B')

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
                    status_koreksi = "BERHASIL OTOMATIS (ADAPTIF)"
                else:
                    status_koreksi = "GAGAL STRUKTUR (Kertas terlalu miring/bergelombang ekstrem)"
                    nilai_akhir = 0.0
            else:
                # Jika foto blur parah atau bukan LJK, kunci ke 0 tanpa crash
                soal_salah = total_soal_aktif
                nilai_akhir = 0.0
                status_koreksi = f"MOHON DEKATKAN KAMERA (Hanya mendeteksi {len(kontur_valid)} bulatan valid)"

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

            st.image(output, channels="BGR", caption="Hasil Analisis Kamera")

            st.markdown("---")
            
            # --- INTEGRASI WHATSAPP ---
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
                f"📊 *HASIL KOREKSI OTOMATIS LJK*:\n"
                f"• Jawaban Benar : {soal_benar} Soal\n"
                f"• Jawaban Salah : {soal_salah} Soal\n"
                f"• Total Skor Poin : {skor_didapat} / {max_skor_aktif}\n"
                f"• *💯 NILAI AKHIR : {nilai_akhir:.2f}*\n"
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
