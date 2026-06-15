import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi", layout="wide")

st.title("📸 Pemindai LJK dengan Garis Pembatas Pas")
st.write("Sesuaikan 4 titik koordinat pojok agar garis merah pas membungkus 4 kotak hijau di LJK Anda.")

# --- INISIALISASI ATAU AMBIL FILE ---
uploaded_file = st.file_uploader("Unggah Foto LJK Anda...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Standarkan resolusi awal gambar input agar pas di layar HP
    h_orig, w_orig = img_raw.shape[:2]
    scale_view = 800 / h_orig
    img = cv2.resize(img_raw, (int(w_orig * scale_view), 800))
    h, w, _ = img.shape

    # --- MENU KONTROL PENGGESER TITIK POJOK ---
    st.sidebar.header("📍 Geser Posisi 4 Titik Pojok")
    st.sidebar.write("Ubah angka di bawah ini untuk mengepaskan lingkaran merah ke kotak hijau LJK Anda:")
    
    # Estimasi posisi awal di sudut-sudut gambar
    x_tl = st.sidebar.number_input("Kiri Atas (X)", min_value=0, max_value=w, value=int(w * 0.1))
    y_tl = st.sidebar.number_input("Kiri Atas (Y)", min_value=0, max_value=h, value=int(h * 0.1))
    
    x_tr = st.sidebar.number_input("Kanan Atas (X)", min_value=0, max_value=w, value=int(w * 0.9))
    y_tr = st.sidebar.number_input("Kanan Atas (Y)", min_value=0, max_value=h, value=int(h * 0.1))
    
    x_br = st.sidebar.number_input("Kanan Bawah (X)", min_value=0, max_value=w, value=int(w * 0.9))
    y_br = st.sidebar.number_input("Kanan Bawah (Y)", min_value=0, max_value=h, value=int(h * 0.9))
    
    x_bl = st.sidebar.number_input("Kiri Bawah (X)", min_value=0, max_value=w, value=int(w * 0.1))
    y_bl = st.sidebar.number_input("Kiri Bawah (Y)", min_value=0, max_value=h, value=int(h * 0.9))

    # Tampilkan garis pembatas pembungkus pada gambar asli
    img_pembantas = img.copy()
    pts_pembatas = np.array([[x_tl, y_tl], [x_tr, y_tr], [x_br, y_br], [x_bl, y_bl]], np.int32)
    # Gambar garis merah tebal penghubung antar titik
    cv2.polylines(img_pembantas, [pts_pembatas], True, (0, 0, 255), 3)
    # Gambar lingkaran penanda di setiap sudut
    for pt in pts_pembatas:
        cv2.circle(img_pembantas, tuple(pt), 8, (255, 0, 0), -1)

    # --- PROSES PELURUSAN PERSPEKTIF ---
    pts1 = np.float32([[x_tl, y_tl], [x_tr, y_tr], [x_br, y_br], [x_bl, y_bl]])
    width_w, height_w = 600, 850
    pts2 = np.float32([[0, 0], [width_w, 0], [width_w, height_w], [0, height_w]])
    
    M_matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img, M_matrix, (width_w, height_w))
    output_display = warped.copy()

    # --- GRID MATEMATIS LAYOUT LJK (Nomor 1-50) ---
    # Fungsi ini menggambar bulatan tepat di atas kertas yang sudah diluruskan garis pembatas tadi
    def buat_grid_tetap():
        map_soal
