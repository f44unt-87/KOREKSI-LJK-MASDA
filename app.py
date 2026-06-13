import cv2
import numpy as np
import streamlit as st

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
st.write("Aplikasi pemindai LJK instan langsung lewat kamera iPhone Anda.")
st.markdown("---")

# --- FORM INPUT DATA ---
st.subheader("👤 Data Siswa & Ujian")
nama_siswa = st.text_input("Nama Siswa (Wajib)")
kelas_siswa = st.text_input("Kelas Siswa (Opsional)")
nama_mapel = st.text_input("Nama Mata Pelajaran (Opsional)")
kelas_ujian = st.text_input("Kelas Ujian (Opsional)")

# --- PENGATURAN KUNCI JAWABAN ---
st.subheader("🔑 Pengaturan Kunci Jawaban")
col1, col2, col3, col4, col5 = st.columns(5)
with col1: kunci_1 = st.selectbox("Soal 1", ['A', 'B', 'C', 'D', 'E'], index=0)
with col2: kunci_2 = st.selectbox("Soal 2", ['A', 'B', 'C', 'D', 'E'], index=2)
with col3: kunci_3 = st.selectbox("Soal 3", ['A', 'B', 'C', 'D', 'E'], index=3)
with col4: kunci_4 = st.selectbox("Soal 4", ['A', 'B', 'C', 'D', 'E'], index=0)
with col5: kunci_5 = st.selectbox("Soal 5", ['A', 'B', 'C', 'D', 'E'], index=4)

st.markdown("---")

# --- AMBIL GAMBAR DARI KAMERA IPHONE ---
st.subheader("📷 Ambil / Unggah Gambar LJK")
# st.camera_input otomatis mengaktifkan kamera depan/belakang iPhone Anda dengan izin iOS
input_gambar = st.camera_input("Posisikan LJK tepat di depan kamera")

# Jika user belum mengambil foto, coba tawarkan opsi upload file alternatif
if input_gambar is None:
    input_gambar = st.file_uploader("Atau pilih file gambar dari galeri iPhone", type=["jpg", "jpeg", "png"])

# --- TOMBOL PROSES KOREKSI ---
if st.button("🚀 MULAI KOREKSI", type="primary"):
    if not nama_siswa.strip():
        st.error("⚠️ Nama Siswa wajib diisi terlebih dahulu!")
    elif input_gambar is None:
        st.error("⚠️ Silakan ambil foto LJK atau unggah file terlebih dahulu!")
    else:
        with st.spinner("Sedang memproses dan mencocokkan bulatan LJK..."):
            # Membaca gambar dari Streamlit input ke OpenCV format
            file_bytes = np.asarray(bytearray(input_gambar.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            output = image.copy()

            # Map Kunci Jawaban
            ans_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
            kunci_jawaban = {0: ans_map[kunci_1], 1: ans_map[kunci_2], 2: ans_map[kunci_3], 3: ans_map[kunci_4], 4: ans_map[kunci_5]}

            # Pre-processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

            # Cari Kontur
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            kontur_lingkaran = []

            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                if w >= 20 and h >= 20 and 0.8 <= ar <= 1.2:
                    kontur_lingkaran.append(c)

            # Validasi jika jumlah bulatan kurang
            if len(kontur_lingkaran) < (5 * 5):
                st.error(f"❌ Gagal memproses! Hanya mendeteksi {len(kontur_lingkaran)} bulatan jawaban.")
                st.warning("Tips: Pastikan kertas LJK mendapat cahaya terang merata dan posisinya lurus masuk ke frame kamera.")
                st.image(image, channels="BGR", caption="Gambar Asli")
            else:
                kontur_lingkaran = urutkan_kontur(kontur_lingkaran, method="top-to-bottom")
                benar = 0

                for q, i in enumerate(range(0, len(kontur_lingkaran), 5)):
                    cnts_pilihan = urutkan_kontur(kontur_lingkaran[i:i + 5], method="left-to-right")
                    diarsir = None

                    for j, c in enumerate(cnts_pilihan):
                        mask = np.zeros(thresh.shape, dtype="uint8")
                        cv2.drawContours(mask, [c], -1, 255, -1)
                        mask = cv2.bitwise_and(thresh, mask)
                        total = cv2.countNonZero(mask)

                        if diarsir is None or total > diarsir[0]:
                            diarsir = (total, j)

                    kunci = kunci_jawaban[q]
                    warna = (0, 255, 0) if kunci == diarsir[1] else (0, 0, 255)
                    if kunci == diarsir[1]:
                        benar += 1

                    cv2.drawContours(output, [cnts_pilihan[kunci]], -1, warna, 3)

                # Menampilkan Hasil Akhir
                skor = (benar / 5) * 100
                tampilan_kelas = kelas_siswa.strip().upper() if kelas_siswa.strip() else "-"
                tampilan_mapel = nama_mapel.strip().upper() if nama_mapel.strip() else "-"
                tampilan_kelas_ujian = kelas_ujian.strip().upper() if kelas_ujian.strip() else "-"

                st.success("🎉 Koreksi Selesai!")
                
                # Kotak Hasil Nilai
                st.markdown(f"""
                ### 📋 LAPORAN HASIL PENILAIAN
                * **Nama Siswa** : {nama_siswa.upper()}
                * **Kelas Siswa** : {tampilan_kelas}
                * **Mata Pelajaran** : {tampilan_mapel}
                * **Kelas Ujian** : {tampilan_kelas_ujian}
                
                **🎯 SKOR UTAMA:**
                * Jumlah Benar : **{benar} / 5 Soal**
                * ## 💯 NILAI AKHIR: {skor:.2f}
                """)
                
                # Tampilkan visualisasi gambar
                st.image(output, channels="BGR", caption="Visualisasi Hasil Koreksi Lembar Jawaban")
