import streamlit as st
import cv2
import numpy as np

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Koreksi LJK Otomatis", layout="centered")

st.title("📸 Pemindai & Seleksi LJK Otomatis")
st.write("Unggah foto lembar LJK Anda, sistem akan otomatis meluruskan perspektif dan menyeleksi nomor 1-50.")

# Komponen Uploader Gambar
uploaded_file = st.file_uploader("Pilih atau Ambil Foto LJK...", type=["png", "jpg", "jpeg", "heic"])

if uploaded_file is not None:
    # Mengubah file upload menjadi format OpenCV image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Buat salinan untuk proses visualisasi
    output_img = img.copy()
    h, w, _ = img.shape
    
    st.info("Sedang memproses gambar dan mendeteksi 4 titik pojok...")

    # 1. DETEKSI OTOMATIS 4 KOTAK JANGKAR (Warna Hijau)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_corners = []
    for c in contours:
        area = cv2.contourArea(c)
        if 100 < area < 1000:
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                detected_corners.append([cX, cY])

    # Validasi jika ditemukan minimal 4 titik kotak hijau
    if len(detected_corners) >= 4:
        pts = np.array(detected_corners)
        
        # Mengurutkan titik secara otomatis (Kiri Atas, Kanan Atas, Kanan Bawah, Kiri Bawah)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        tl = pts[np.argmin(s)]       # Top-Left
        br = pts[np.argmax(s)]       # Bottom-Right
        tr = pts[np.argmin(diff)]    # Top-Right
        bl = pts[np.argmax(diff)]    # Bottom-Left
        
        pts1 = np.float32([tl, tr, br, bl])
        
        # 2. PERSPECTIVE TRANSFORM (Meluruskan Lembar LJK)
        width, height = 500, 700
        pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(img, matrix, (width, height))
        final_output = warped.copy()
        
        # 3. PREPROCESSING & DETEKSI BULATAN JAWABAN
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        circles = cv2.HoughCircles(
            blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1, 
            minDist=12, 
            param1=50, 
            param2=14, 
            minRadius=6, 
            maxRadius=14
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            questions = {i: [] for i in range(1, 51)}
            
            # Pengelompokan nomor soal 1-50 berdasarkan letak sub-blok koordinat
            for circle in circles:
                cx, cy, r = circle
                
                # BLOK ATAS (Y < 350)
                if cy < 350:
                    if 200 <= cx < 320:  # Kolom Tengah (Soal 11-20)
                        row_idx = int((cy - 100) / 21)
                        q_num = 11 + row_idx
                        if 11 <= q_num <= 20: questions[q_num].append((cx, cy, r))
                    elif cx >= 320:     # Kolom Kanan (Soal 31-40)
                        row_idx = int((cy - 100) / 21)
                        q_num = 31 + row_idx
                        if 31 <= q_num <= 40: questions[q_num].append((cx, cy, r))
                
                # BLOK BAWAH (Y >= 350)
                else:
                    if cx < 200:        # Kolom Kiri (Soal 1-10)
                        row_idx = int((cy - 440) / 21)
                        q_num = 1 + row_idx
                        if 1 <= q_num <= 10: questions[q_num].append((cx, cy, r))
                    elif 200 <= cx < 320: # Kolom Tengah (Soal 21-30)
                        row_idx = int((cy - 440) / 21)
                        q_num = 21 + row_idx
                        if 21 <= q_num <= 30: questions[q_num].append((cx, cy, r))
                    elif cx >= 320:     # Kolom Kanan (Soal 41-50)
                        row_idx = int((cy - 440) / 21)
                        q_num = 41 + row_idx
                        if 41 <= q_num <= 50: questions[q_num].append((cx, cy, r))

            # Mengurutkan opsi jawaban A-E dari kiri ke kanan dan menandainya
            for q_num in sorted(questions.keys()):
                questions[q_num] = sorted(questions[q_num], key=lambda x: x[0])
                if len(questions[q_num]) > 0:
                    first_circle = questions[q_num][0]
                    # Beri teks nomor soal berwarna merah
                    cv2.putText(final_output, str(q_num), (first_circle[0] - 25, first_circle[1] + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    for circle in questions[q_num]:
                        cx, cy, r = circle
                        # Gambar lingkaran luar warna cyan/biru muda
                        cv2.circle(final_output, (cx, cy), r, (255, 255, 0), 2)
            
            # 4. MENAMPILKAN HASIL DI WEB STREAMLIT
            st.success("Pemrosesan Selesai!")
            
            # Konversi BGR ke RGB untuk Streamlit
            img_original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
            img_final_rgb = cv2.cvtColor(final_output, cv2.COLOR_BGR2RGB)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(img_original_rgb, caption="1. Foto Asli Terunggah", use_container_width=True)
            with col2:
                st.image(img_warped_rgb, caption="2. Hasil Perspektif Lurus", use_container_width=True)
                
            st.image(img_final_rgb, caption="3. Hasil Seleksi Deteksi Nomor 1-50", use_container_width=True)
            
        else:
            st.error("Gagal mendeteksi bulatan jawaban ganda. Coba perbaiki pencahayaan foto.")
    else:
        st.error(f"Gagal mendeteksi 4 kotak pojok hijau secara otomatis (Hanya mendeteksi {len(detected_corners)} titik). Pastikan 4 kotak pembatas di foto terlihat jelas dan tidak terpotong.")
