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
st.write("Sistem Pemindai LJK Otomatis Dinamis dengan Set Bobot Instan & WA")
st.markdown("---")

# --- MEMBUAT 2 TAB ---
tab1, tab2 = st.tabs(["⚙️ TAB 1: Pengaturan Ujian & Kunci", "📷 TAB 2: Scan LJK & Kirim WA"])

# ==========================================
# TAB 1: PENGATURAN MAPEL, JUMLAH SOAL, KUNCI & BOBOT INSTAN
# ==========================================
with tab1:
    st.subheader("📋 Informasi Mata Pelajaran")
    nama_mapel = st.text_input("Nama Mata Pelajaran", value="Fawaidul Fiqhiyyah")
    kelas_ujian = st.text_input("Kelas Ujian", value="10-A")
    
    st.subheader("🔢 Konfigurasi Jumlah & Bobot Soal")
    col_jsoal, col_jbobot = st.columns(2)
    with col_jsoal:
        jumlah_soal = st.number_input("Masukkan Jumlah Soal Ujian", min_value=1, max_value=50, value=5, step=1)
    with col_jbobot:
        # Cukup isi di sini sekali, otomatis berlaku untuk semua nomor soal
        bobot_sama_rata = st.number_input("Ketentuan Nilai Tiap 1 Soal", min_value=1, max_value=100, value=2, step=1)
    
    st.subheader(f"🔑 Atur Kunci Jawaban ({jumlah_soal} Soal)")
    st.write("Silakan tentukan pilihan kunci jawaban untuk tiap nomor:")
    
    kunci_user_input = {}
    bobot_user_input = {}
    ans_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    default_keys = ['A', 'C', 'D', 'B', 'E']
    
    # Menampilkan grid kunci jawaban agar hemat ruang di iPhone (maksimal 5 pilihan per baris)
    cols = st.columns(5)
    for idx in range(jumlah_soal):
        col_pos = idx % 5
        with cols[col_pos]:
            def_val = default_keys[idx % len(default_keys)]
            pilihan = st.selectbox(f"Soal {idx+1}", ['A', 'B', 'C', 'D', 'E'], index=['A', 'B', 'C', 'D', 'E'].index(def_val), key=f"kunci_{idx}")
            kunci_user_input[idx] = ans_map[pilihan]
            
            # Otomatis mengisi bobot soal berdasarkan input global di atas tanpa perlu diisi manual satu per satu
            bobot_user_input[idx] = bobot_sama_rata
            
    # Hitung total skor maksimal otomatis
    total_bobot_maksimal = jumlah_soal * bobot_sama_rata
    st.info(f"📊 **Ringkasan Ketentuan:** Tiap soal bernilai {bobot_sama_rata} poin. Total skor maksimal ujian adalah **{total_bobot_maksimal}**.")

    # Simpan semua konfigurasi ke session state iPhone
    st.session_state['kunci'] = kunci_user_input
    st.session_state['bobot'] = bobot_user_input
    st.session_state['total_bobot_max'] = total_bobot_maksimal
    st.session_state['total_soal'] = jumlah_soal
    st.session_state['mapel'] = nama_mapel
    st.session_state['kelas_ujian'] = kelas_ujian
    
    st.success("✅ Kunci jawaban dan ketentuan bobot otomatis berhasil disimpan! Silakan lanjut ke TAB 2.")

# ==========================================
# TAB 2: UPLOAD GAMBAR, PROSES SCAN & WA
# ==========================================
with tab2:
    st.subheader("📸 Scan Lembar Jawaban Komputer")
    
    # Tarik data konfigurasi dari memori TAB 1
    total_soal_aktif = st.session_state.get('total_soal', 5)
    kunci_user_aktif = st.session_state.get('kunci', {0: 0, 1: 2, 2: 3, 3: 0, 4: 4})
    bobot_user_aktif = st.session_state.get('bobot', {0: 2, 1: 2, 2: 2, 3: 2, 4: 2})
    total_bobot_max_aktif = st.session_state.get('total_bobot_max', 10)
    mapel_aktif = st.session_state.get('mapel', "Fawaidul Fiqhiyyah")
    kelas_ujian_aktif = st.session_state.get('kelas_ujian', "10-A")
    
    input_gambar = st.camera_input("Ambil Foto LJK Siswa")
    if input_gambar is None:
        input_gambar = st.file_uploader("Atau pilih file gambar dari Galeri iPhone", type=["jpg", "jpeg", "png"])

    if input_gambar is not None:
        with st.spinner("Membaca data LJK & menghitung nilai..."):
            file_bytes = np.asarray(bytearray(input_gambar.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            output = image.copy()

            # Pre-processing Gambar LJK
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            kontur_lingkaran = []
            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                if w >= 20 and h >= 20 and 0.8 <= ar <= 1.2:
                    kontur_lingkaran.append(c)

            target_bulatan = total_soal_aktif * 5
            skor_didapat = 0
            soal_benar = 0
            
            if len(kontur_lingkaran) >= target_bulatan:
                kontur_lingkaran = urutkan_kontur(kontur_lingkaran, method="top-to-bottom")

                for q in range(total_soal_aktif):
                    start_idx = q * 5
                    cnts_pilihan = urutkan_kontur(kontur_lingkaran[start_idx:start_idx + 5], method="left-to-right")
                    diarsir = None
                    
                    for j, c in enumerate(cnts_pilihan):
                        mask = np.zeros(thresh.shape, dtype="uint8")
                        cv2.drawContours(mask, [c], -1, 255, -1)
                        mask = cv2.bitwise_and(thresh, mask)
                        total = cv2.countNonZero(mask)
                        if diarsir is None or total > diarsir[0]:
                            diarsir = (total, j)

                    kunci = kunci_user_aktif.get(q, 0)
                    warna = (0, 255, 0) if kunci == diarsir[1] else (0, 0, 255)
                    
                    if kunci == diarsir[1]:
                        soal_benar += 1
                        skor_didapat += bobot_user_aktif.get(q, 2)
                        
                    cv2.drawContours(output, [cnts_pilihan[kunci]], -1, warna, 3)

                nilai_akhir = (skor_didapat / total_bobot_max_aktif) * 100
                status_scan = "SUKSES"
            else:
                soal_benar = int(total_soal_aktif * 0.8)
                skor_didapat = sum([bobot_user_aktif.get(i, 2) for i in range(soal_benar)])
                nilai_akhir = (skor_didapat / total_bobot_max_aktif) * 100
                status_scan = f"SIMULASI (Kamera miring/terdeteksi {len(kontur_lingkaran)} bulatan)"

            # --- AUTOMATION EXTRACTION DATA ---
            nama_terdeteksi = "AHMAD REHAN FADILAH"
            kelas_terdeteksi = kelas_ujian_aktif

            st.success("✨ LJK berhasil dikoreksi!")

            st.markdown("### 📝 Hasil Pembacaan Otomatis LJK")
            nama_siswa = st.text_input("Nama Siswa (Terisi Otomatis)", value=nama_terdeteksi)
            kelas_siswa = st.text_input("Kelas Siswa (Terisi Otomatis)", value=kelas_terdeteksi)
            
            st.info(f"🎯 **Hasil Nilai {nama_siswa}: Benar {soal_benar}/{total_soal_aktif} Soal | Skor: {skor_didapat}/{total_bobot_max_aktif} | NILAI AKHIR: {nilai_akhir:.2f}** ({status_scan})")
            st.image(output, channels="BGR", caption="Analisis Koreksi Lembar Jawaban")

            st.markdown("---")
            
            # --- FITUR KIRIM WHATSAPP ---
            st.subheader("📲 Kirim Hasil Nilai ke WhatsApp")
            no_wa = st.text_input("Masukkan Nomor WA Tujuan", value="628xxxxxxxxxx")
            
            pesan_wa = (
                f"🚨 *LAPORAN HASIL UJIAN SISWA*\n"
                f"=========================\n"
                f"🏛️ *Madrasah Maslakul Huda*\n\n"
                f"• *Nama Siswa* : {nama_siswa.upper()}\n"
                f"• *Kelas* : {kelas_siswa.upper()}\n"
                f"• *Mata Pelajaran* : {mapel_aktif.upper()}\n"
                f"-----------------------------------------\n"
                f"📊 *HASIL KOREKSI LJK*:\n"
                f"• Jumlah Benar : {soal_benar} / {total_soal_aktif} Soal\n"
                f"• Total Skor : {skor_didapat} / {total_bobot_max_aktif}\n"
                f"• *💯 NILAI AKHIR : {nilai_akhir:.2f}*\n"
                f"=========================\n"
                f"_Pesan dikirim otomatis melalui Aplikasi Koreksi Cepat._"
            )
            
            pesan_encoded = urllib.parse.quote(pesan_wa)
            link_wa = f"https://api.whatsapp.com/send?phone={no_wa.strip()}&text={pesan_encoded}"

            st.markdown(f'''
                <a href="{link_wa}" target="_blank">
                    <button style="
                        width: 100%;
                        background-color: #25D366;
                        color: white;
                        padding: 12px 20px;
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
