import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi Maslakul Huda", layout="wide")

st.title("💯 Pemindai LJK dengan Fitur Pengepas Bulatan (Slider Kontrol)")
st.write("Gunakan menu slider di sebelah kiri untuk menggeser posisi bulatan hijau agar pas di tengah lingkaran LJK.")

def luruskan_lembar(image):
    """Meluruskan kertas menggunakan 4 titik jangkar kotak pembatas"""
    h_orig, w_orig = image.shape[:2]
    scale = 1000 / h_orig
    resized = cv2.resize(image, (int(w_orig * scale), 1000))
    
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    for c in contours:
        if 50 < cv2.contourArea(c) < 2000:
            M = cv2.moments(c)
            if M["m00"] != 0:
                centers.append([int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])])
                
    if len(centers) >= 4:
        centers = np.array(centers)
        rect = np.zeros((4, 2), dtype="float32")
        s = centers.sum(axis=1)
        rect[0] = centers[np.argmin(s)]  
        rect[2] = centers[np.argmax(s)]  
        diff = np.diff(centers, axis=1)
        rect[1] = centers[np.argmin(diff)] 
        rect[3] = centers[np.argmax(diff)] 
        
        width, height = 600, 850
        pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        M_matrix = cv2.getPerspectiveTransform(rect, pts2)
        warped = cv2.warpPerspective(resized, M_matrix, (width, height))
        return warped
    return None

# --- SIDEBAR KONTROL UNTUK PENGGESERAN DINAMIS ---
st.sidebar.header("🛠️ Pengaturan Posisi Bulatan (Paskan Di Sini)")

# Kontrol Ukuran Bulatan & Jarak Antar Opsi
radius_bullet = st.sidebar.slider("Ukuran Jari-jari Lingkaran", 5, 15, 8)
jarak_opsi = st.sidebar.slider("Jarak Horizontal Opsi (A ke E)", 15, 25, 18)
jarak_baris = st.sidebar.slider("Jarak Vertikal Baris Soal", 15, 25, 21)

st.sidebar.subheader("📍 Geser Posisi Blok Atas (Soal 11-40)")
shift_x_atas = st.sidebar.slider("Geser Kiri/Kanan (Atas)", -50, 50, 0)
shift_y_atas = st.sidebar.slider("Geser Atas/Bawah (Atas)", -50, 50, 0)

st.sidebar.subheader("📍 Geser Posisi Blok Bawah (Soal 1-10, 21-30, 41-50)")
shift_x_bawah = st.sidebar.slider("Geser Kiri/Kanan (Bawah)", -50, 50, 0)
shift_y_bawah = st.sidebar.slider("Geser Atas/Bawah (Bawah)", -50, 50, 0)


def buat_grid_ljk_dinamis(j_opsi, j_baris, sx_atas, sy_atas, sx_bawah, sy_bawah):
    map_soal = {}
    
    # ==================== BLOK ATAS ====================
    # Kolom Tengah (Soal 11-20)
    start_x_tengah_atas = 240 + sx_atas
    start_y_tengah_atas = 115 + sy_atas
    for i in range(10):
        q_num = 11 + i
        y_pos = start_y_tengah_atas + (i * j_baris)
        map_soal[q_num] = [(start_x_tengah_atas + (j * j_opsi), y_pos) for j in range(5)]
        
    # Kolom Kanan (Soal 31-40)
    start_x_kanan_atas = 395 + sx_atas
    start_y_kanan_atas = 115 + sy_atas
    for i in range(10):
        q_num = 31 + i
        y_pos = start_y_kanan_atas + (i * j_baris)
        map_soal[q_num] = [(start_x_kanan_atas + (j * j_opsi), y_pos) for j in range(5)]

    # ==================== BLOK BAWAH ====================
    # Kolom Kiri (Soal 1-10)
    start_x_kiri_bawah = 112 + sx_bawah
    start_y_bawah = 433 + sy_bawah
    for i in range(10):
        q_num = 1 + i
        y_pos = start_y_bawah + (i * j_baris)
        map_soal[q_num] = [(start_x_kiri_bawah + (j * j_opsi), y_pos) for j in range(5)]
        
    # Kolom Tengah (Soal 21-30)
    start_x_tengah_bawah = 242 + sx_bawah
    for i in range(10):
        q_num = 21 + i
        y_pos = start_y_bawah + (i * j_baris)
        map_soal[q_num] = [(start_x_tengah_bawah + (j * j_opsi), y_pos) for j in range(5)]
        
    # Kolom Kanan (Soal 41-50)
    start_x_kanan_bawah = 397 + sx_bawah
    for i in range(10):
        q_num = 41 + i
        y_pos = start_y_bawah + (i * j_baris)
        map_soal[q_num] = [(start_x_kanan_bawah + (j * j_opsi), y_pos) for j in range(5)]
        
    return map_soal

# --- MAIN UPLOADER ---
file_image = st.file_uploader("Unggah Gambar LJK...", type=["png", "jpg", "jpeg"])

if file_image:
    bytes_data = np.asarray(bytearray(file_image.read()), dtype=np.uint8)
    img = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
    
    warped = luruskan_lembar(img)
    if warped is not None:
        output_display = warped.copy()
        
        # Panggil pemetaan grid berdasarkan nilai slider
        grid_ljk = buat_grid_ljk_dinamis(jarak_opsi, jarak_baris, shift_x_atas, shift_y_atas, shift_x_bawah, shift_y_bawah)
        
        for q_num, opsi_list in grid_ljk.items():
            x_label, y_label = opsi_list[0]
            cv2.putText(output_display, f"{q_num}", (x_label - 22, y_label + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            for (cx, cy) in opsi_list:
                cv2.circle(output_display, (cx, cy), radius_bullet, (0, 255, 0), 1)
                cv2.circle(output_display, (cx, cy), 1, (0, 0, 255), -1)
                
        st.image(cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), caption="Hasil Kalibrasi Penyeleksian LJK (Gunakan slider untuk paskan lingkaran)")
    else:
        st.error("Gagal mendeteksi kertas. Pastikan 4 kotak hijau di sudut LJK tidak terpotong kamera.")
