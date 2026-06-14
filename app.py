import cv2
import numpy as np
import streamlit as st
import urllib.parse

# Konfigurasi Tampilan Halaman Utama di iPhone
st.set_page_config(page_title="KOREKSI CEPAT MASLAKUL HUDA", layout="centered")

def dapatkan_perspektif(image, pts):
    """Memperbaiki kemiringan foto berdasarkan 4 titik sudut agar kertas menjadi lurus sempurna"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

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
# TAB 2: AUTOMATIC SCANNING & WA (PRESISI TINGGI)
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
    input_gambar = st.camera_input("Posisikan LJK Maslakul Huda secara lurus")
    if input_gambar is None:
        input_gambar = st.file_uploader("Atau pilih file gambar dari Galeri iPhone", type=["jpg", "jpeg", "png"])

    if input_gambar is not None:
        with st.spinner("Menghitung akurasi bulatan LJK..."):
            file_bytes = np.asarray(bytearray(input_gambar.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            
            # --- 1. PRE-PROCESSING UTAMA ---
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

            # --- 2. DETEKSI LINGKARAN & FILTER UKURAN YANG LEBIH KETAT ---
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            kontur_lingkaran = []
            
            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                # Filter ketat: Diameter bulatan LJK Anda biasanya berkisar di ukuran piksel ini
                if 18 <= w <= 45 and 18 <= h <= 45 and 0.82 <= ar <= 1.18:
                    kontur_lingkaran.append(c)

            soal_benar = 0
            soal_salah = 0
            skor_didapat = 0
            ans_letters = ['A', 'B', 'C', 'D', 'E']
            detail_jawaban = []
            output = image.copy()

            # Melakukan penyortiran koordinat absolut agar tidak melompati baris nomor LJK Maslakul Huda
            if len(kontur_lingkaran) >= (total_soal_aktif * 5):
                # Urutkan berdasarkan koordinat Y (atas ke bawah) global terlebih dahulu
                boundingBoxes = [cv2.boundingRect(c) for c in kontur_lingkaran]
                kontur_lingkaran = [c for _, c in sorted(zip(boundingBoxes, kontur_lingkaran), key=lambda b: b[0][1])]
                
                # Memilah per sub-baris isi 5 bulatan (A-E) untuk mengunci akurasi per nomor soal
                koreksi_sukses = True
                jawaban_terdeteksi_all = {}
                
                # Kelompokkan bulatan ke dalam grup horizontal (soal per soal)
                list_soal_kontur = []
                for i in range(0, len(kontur_lingkaran), 5):
                    sub_grup = kontur_lingkaran[i:i+5]
                    if len(sub_grup) == 5:
                        # Urutkan sub grup dari kiri ke kanan (A, B, C, D, E)
                        sub_grup_boxes = [cv2.boundingRect(cg) for cg in sub_grup]
                        sub_grup = [cg for _, cg in sorted(zip(sub_grup_boxes, sub_grup), key=lambda b: b[0][0])]
                        list_soal_kontur.append(sub_grup)
                
                # Urutkan ulang baris soal berdasarkan struktur penomoran unik LJK Maslakul Huda Anda
                # (Kiri Atas, Kiri Bawah, Tengah Atas, Tengah Bawah, Kanan Atas, Kanan Bawah)
                def dapatkan_posisi_blok(grup):
                    (x, y, w, h) = cv2.boundingRect(grup[0])
                    return (x, y)
                
                list_soal_kontur = sorted(list_soal_kontur, key=dapatkan_posisi_blok)

                # Batasi pemrosesan hanya sampai jumlah soal yang diaktifkan user
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
                        warna = (0, 255, 0) # Hijau
                        detail_jawaban.append(f"No. {q+1}: ✅ (Siswa: {huruf_terdeteksi} | Kunci: {huruf_kunci})")
                    else:
                        soal_salah += 1
                        warna = (0, 0, 255) # Merah
                        detail_jawaban.append(f"No. {q+1}: ❌ (Siswa: {huruf_terdeteksi} | Kunci: {huruf_kunci})")
                        
                    cv2.drawContours(output, [cnts_pilihan[ans_letters.index(huruf_kunci)]], -1, warna, 3)

                nilai_akhir = (skor_didapat / max_skor_aktif) * 100
                status_koreksi = "BERHASIL OTOMATIS (PRESISI)"
            else:
                soal_benar = 0
                soal_salah = total_soal_aktif
                nilai_akhir = 0.0
                status_koreksi = f"MOHON PASIKAN KAMERA TEGAK LURUS (Hanya mendeteksi {len(kontur_lingkaran)} bulatan)"

            st.success("✨ Selesai! Hasil analisis presisi tinggi keluar di bawah:")

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

            st.image(output, channels="BGR", caption="Visualisasi Analisis Presisi LJK")

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
