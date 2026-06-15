import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi Maslakul Huda", layout="wide")

st.title("💯 Pemindai LJK Metode Grid Geometris (Anti-Meleset)")
st.write("Sistem ini mengunci koordinat bulatan berdasarkan layout matematika LJK, bukan tebakan otomatis.")

def luruskan_lembar(image):
    """Meluruskan kertas menggunakan 4 titik jangkar kotak pembatas"""
    h_orig, w_orig = image.shape[:2]
    scale = 1000 / h_orig  # Naikkan resolusi ke 1000px agar presisi
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
        rect[0] = centers[np.argmin(s)]  # Kiri Atas
        rect[2] = centers[np.argmax(s)]  # Kanan Bawah
        diff = np.diff(centers, axis=1)
        rect[1] = centers[np.argmin(diff)] # Kanan Atas
        rect[3] = centers[np.argmax(diff)] # Kiri Bawah
        
        # Dimensi standar lembar LJK yang telah diluruskan
        width, height = 600, 850
        pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        M_matrix = cv2.getPerspectiveTransform(rect, pts2)
        warped = cv2.warpPerspective(resized, M_matrix, (width, height))
        return warped
    return None

def buat_grid_ljk():
    """
    Memetakan koordinat matematika murni berdasarkan layout kertas Maslakul Huda.
    Mencakup Soal 1-50 dengan opsi A, B, C, D, E.
    """
    map_soal = {}
    
    # 1. KONFIGURASI JARAK ANTAR OPSI (A ke B, B ke C, dst = ~18 piksel)
    jarak_opsi = 18
    
    # ==================== BLOK ATAS (Soal 11-40) ====================
    # Kolom Tengah (Soal 11-20) -> Koordinat X awal opsi A dimulai dari X=240
    start_x_tengah_atas = 240
    start_y_tengah_atas = 115
    for i in range(10):
        q_num = 11 + i
        y_pos = start_y_tengah_atas + (i * 21) # Jarak antar baris soal = 21px
        map_soal[q_num] = [(start_x_tengah_atas + (j * jarak_opsi), y_pos) for j in range(5)]
        
    # Kolom Kanan (Soal 31-40) -> Koordinat X awal opsi A dimulai dari X=395
    start_x_kanan_atas = 395
    start_y_kanan_atas = 115
    for i in range(10):
        q_num = 31 + i
        y_pos = start_y_kanan_atas + (i * 21)
        map_soal[q_num] = [(start_x_kanan_atas + (j * jarak_opsi), y_pos) for j in range(5)]

    # ==================== BLOK BAWAH (Soal 1-10, 21-30, 41-50) ====================
    # Kolom Kiri (Soal 1-10) -> Koordinat X awal opsi A dimulai dari X=112
    start_x_kiri_bawah = 112
    start_y_bawah = 433
    for i in range(10):
        q_num = 1 + i
        y_pos = start_y_bawah + (i * 21)
        map_soal[q_num] = [(start_x_kiri_bawah + (j * jarak_opsi), y_pos) for j in range(5)]
        
    # Kolom Tengah (Soal 21-30) -> Koordinat X awal opsi A dimulai dari X=242
    start_x_tengah_bawah = 242
    for i in range(10):
        q_num = 21 + i
        y_pos = start_y_bawah + (i * 21)
        map_soal[q_num] = [(start_x_tengah_bawah + (j * jarak_opsi), y_pos) for j in range(5)]
        
    # Kolom Kanan (Soal 41-50) -> Koordinat X awal opsi A dimulai dari X=397
    start_x_kanan_bawah = 397
    for i in range(10):
        q_num = 41 + i
        y_pos = start_y_bawah + (i * 21)
        map_soal[q_num] = [(start_x_kanan_bawah + (j * jarak_opsi), y_pos) for j in range(5)]
        
    return map_soal

# --- ANTARMUKA STREAMLIT ---
file_image = st.file_uploader("Unggah Gambar LJK (Kunci atau Jawaban Siswa)...", type=["png", "jpg", "jpeg"])

if file_image:
    bytes_data = np.asarray(bytearray(file_image.read()), dtype=np.uint8)
    img = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
    
    warped = luruskan_lembar(img)
    if warped is not None:
        output_display = warped.copy()
        
        # Buat pemetaan grid koordinat matematis LJK
        grid_ljk = buat_grid_ljk()
        radius_bullet = 8  # Ukuran radius lingkaran seleksi
        
        # Gambar lingkaran penyeleksi murni berdasarkan koordinat rumus matematika layout
        for q_num, opsi_list in grid_ljk.items():
            # Beri label nomor soal di sebelah kiri opsi A
            x_label, y_label = opsi_list[0]
            cv2.putText(output_display, f"{q_num}", (x_label - 22, y_label + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            # Gambar bulatan pilihan ganda A, B, C, D, E
            for (cx, cy) in opsi_list:
                cv2.circle(output_display, (cx, cy), radius_bullet, (0, 255, 0), 1)
                cv2.circle(output_display, (cx, cy), 1, (0, 0, 255), -1) # Titik pusat tengah
                
        st.success("Berhasil Mengunci Grid Seluruh Bulatan Nomor 1-50!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB), caption="LJK Setelah Diluruskan")
        with col2:
            st.image(cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), caption="Hasil Pemetaan Grid Matematika (Pasti Pas)")
            
    else:
        st.error("Gagal mendeteksi kertas. Pastikan 4 kotak hijau di sudut LJK tidak terpotong kamera.")
