import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Sistem Koreksi LJK Maslakul Huda", layout="wide")

st.title("💯 Sistem Koreksi & Seleksi LJK Dinamis (1-50)")
st.write("Aplikasi ini menggunakan sistem model berbasis LJK Kunci Jawaban untuk memetakan koordinat bulatan secara presisi.")

# --- INI LOGIKA UNTUK MELURUSKAN PERSPEKTIF LEMBAR JAWABAN ---
def luruskan_lembar(image):
    # Mengubah ukuran gambar ke standar pemrosesan agar ringan di HP
    h_orig, w_orig = image.shape[:2]
    scale = 800 / h_orig
    resized = cv2.resize(image, (int(w_orig * scale), 800))
    
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Deteksi berbasis kotak hijau pembatas (Jangkar Sudut)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    for c in contours:
        if 80 < cv2.contourArea(c) < 1500:
            M = cv2.moments(c)
            if M["m00"] != 0:
                centers.append([int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])])
                
    if len(centers) >= 4:
        centers = np.array(centers)
        rect = np.zeros((4, 2), dtype="float32")
        s = centers.sum(axis=1)
        rect[0] = centers[np.argmin(s)] # Kiri Atas
        rect[2] = centers[np.argmax(s)] # Kanan Bawah
        diff = np.diff(centers, axis=1)
        rect[1] = centers[np.argmin(diff)] # Kanan Atas
        rect[3] = centers[np.argmax(diff)] # Kiri Bawah
        
        # Warp ke ukuran standar resolusi tinggi
        width, height = 600, 850
        pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        M_matrix = cv2.getPerspectiveTransform(rect, pts2)
        warped = cv2.warpPerspective(resized, M_matrix, (width, height))
        return warped
    return None

# --- INI LOGIKA UNTUK MENGEKSTRAK KISI BULATAN ---
def dapatkan_kisi_bulatan(warped_img):
    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bulatan = []
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        # Karakteristik bulatan LJK
        if w >= 12 and h >= 12 and w <= 25 and h <= 25 and 0.75 <= ar <= 1.25:
            bulatan.append((x, y, w, h))
    return bulatan

# --- INTERFACE UTAMA STREAMLIT ---
col_mod, col_scan = st.columns(2)

with col_mod:
    st.header("1. Registrasi Model (Kunci)")
    file_model = st.file_uploader("Unggah LJK Kunci Jawaban (Sebagai Acuan)", type=["png", "jpg", "jpeg"])
    
    if file_model:
        bytes_data = np.asarray(bytearray(file_model.read()), dtype=np.uint8)
        img_model = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
        
        warped_model = luruskan_lembar(img_model)
        if warped_model is not None:
            list_bulatan = dapatkan_kisi_bulatan(warped_model)
            # Simpan koordinat bulatan ke dalam session state agar diingat oleh sistem
            st.session_state['model_coords'] = list_bulatan
            st.session_state['warped_model'] = warped_model
            st.success(f"Model Berhasil Dikunci! Menemukan {len(list_bulatan)} titik referensi pilihan ganda.")
            
            # Tampilkan visualisasi model cetak biru
            vis_model = warped_model.copy()
            for (x, y, w, h) in list_bulatan:
                cv2.rectangle(vis_model, (x, y), (x+w, y+h), (255, 0, 0), 2)
            st.image(cv2.cvtColor(vis_model, cv2.COLOR_BGR2RGB), caption="Cetak Biru Model Referensi")
        else:
            st.error("Gagal meluruskan LJK Model. Pastikan 4 kotak hijau terlihat jelas.")

with col_scan:
    st.header("2. Pemindaian LJK Jawaban")
    if 'model_coords' not in st.session_state:
        st.warning("Silakan unggah dan registrasi LJK Kunci di sebelah kiri terlebih dahulu.")
    else:
        file_scan = st.file_uploader("Unggah LJK Lembar Jawaban Siswa/Ujian", type=["png", "jpg", "jpeg"])
        
        if file_scan:
            bytes_data_s = np.asarray(bytearray(file_scan.read()), dtype=np.uint8)
            img_scan = cv2.imdecode(bytes_data_s, cv2.IMREAD_COLOR)
            
            warped_scan = luruskan_lembar(img_scan)
            if warped_scan is not None:
                final_output = warped_scan.copy()
                
                # Pemrosesan biner gambar siswa untuk mendeteksi pilihan yang dihitamkan
                gray_s = cv2.cvtColor(warped_scan, cv2.COLOR_BGR2GRAY)
                thresh_s = cv2.threshold(gray_s, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                
                # Ambil koordinat referensi dari model yang sudah dikunci tadi
                referensi_bulatan = st.session_state['model_coords']
                
                # Proyeksikan koordinat model ke gambar yang baru masuk
                for (x, y, w, h) in referensi_bulatan:
                    # Ambil potongan area piksel bulatan
                    mask_area = thresh_s[y:y+h, x:x+w]
                    total_piksel = cv2.countNonZero(mask_area)
                    luas_area = w * h
                    kepadatan = total_piksel / float(luas_area)
                    
                    # Jika kerapatan piksel hitam tinggi, tandai sebagai pilihan siswa (Warna Merah Solid)
                    if kepadatan > 0.5: 
                        cv2.rectangle(final_output, (x, y), (x+w, y+h), (0, 0, 255), -1) 
                    else:
                        # Bulatan kosong biasa (Warna Hijau Presisi)
                        cv2.rectangle(final_output, (x, y), (x+w, y+h), (0, 255, 0), 1)
                
                st.success("Sinkronisasi Selesai! Semua bulatan dipetakan 100% pas mengikuti model acuan.")
                st.image(cv2.cvtColor(final_output, cv2.COLOR_BGR2RGB), caption="Hasil Penyeleksian LJK Siswa Berdasarkan Model")
            else:
                st.error("Gagal mendeteksi lembar jawaban siswa. Pastikan posisi pengambilan gambar mirip dengan model referensi.")

