import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi", layout="centered")

st.title("📸 Pemindai LJK Presisi (Anti-Menceng)")
st.write("Versi optimasi: Menggunakan pelurusan titik presisi tinggi dan grid mapping dinamis.")

uploaded_file = st.file_uploader("Unggah Foto LJK Anda...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    
    # 1. DETEKSI 4 TITIK POJOK UTAMA (Mencari Kontur Terluar / Kotak Pembatas)
    gray_init = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred_init = cv2.GaussianBlur(gray_init, (5, 5), 0)
    edged = cv2.Canny(blurred_init, 50, 150)
    
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    pts1 = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            pts1 = approx
            break
            
    # Jika kontur luar gagal, gunakan fallback deteksi berbasis warna hijau kotak pembatas
    if pts1 is None:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        contours_g, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        centers = []
        for cg in contours_g:
            if 100 < cv2.contourArea(cg) < 2000:
                M = cv2.moments(cg)
                if M["m00"] != 0:
                    centers.append([int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])])
                    
        if len(centers) >= 4:
            # Ambil 4 sudut paling ekstrem
            centers = np.array(centers)
            s = centers.sum(axis=1)
            diff = np.diff(centers, axis=1)
            pts1 = np.float32([centers[np.argmin(s)], centers[np.argmin(diff)], centers[np.argmax(s)], centers[np.argmax(diff)]])

    if pts1 is not None:
        # Menata urutan titik (Kiri Atas, Kanan Atas, Kanan Bawah, Kiri Bawah)
        pts1 = pts1.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts1.sum(axis=1)
        rect[0] = pts1[np.argmin(s)]
        rect[2] = pts1[np.argmax(s)]
        diff = np.diff(pts1, axis=1)
        rect[1] = pts1[np.argmin(diff)]
        rect[3] = pts1[np.argmax(diff)]
        
        # 2. PERSPECTIVE TRANSFORM DENGAN RESOLUSI LEBIH BESAR AGAR TIDAK PECAH
        width, height = 600, 800
        pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        M_matrix = cv2.getPerspectiveTransform(rect, pts2)
        warped = cv2.warpPerspective(img, M_matrix, (width, height))
        final_output = warped.copy()
        
        # 3. DETEKSI BULATAN SECARA ADAPTIF (Mengikuti kontur bulat, bukan koordinat kaku)
        gray_w = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray_w, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Cari semua objek bulat di kertas yang sudah lurus
        cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bubble_contours = []
        
        for c in cnts:
            (x, y, w_b, h_b) = cv2.boundingRect(c)
            ar = w_b / float(h_b)
            # Filter objek yang benar-benar bulat berbentuk lingkaran LJK
            if w_b >= 10 and h_b >= 10 and 0.8 <= ar <= 1.2:
                bubble_contours.append(c)
                
        st.success(f"Berhasil mendeteksi {len(bubble_contours)} bulatan LJK!")
        
        # Gambar semua bulatan yang berhasil dikunci langsung pada posisinya
        for c in bubble_contours:
            (x, y, w_b, h_b) = cv2.boundingRect(c)
            # Menggambar kotak presisi langsung di sekeliling bulatan asli gambar
            cv2.rectangle(final_output, (x, y), (x + w_b, y + h_b), (0, 255, 0), 2)
            
        # Tampilkan Hasil Perbaikan
        img_original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_final_rgb = cv2.cvtColor(final_output, cv2.COLOR_BGR2RGB)
        
        st.image(img_original_rgb, caption="Foto Asli", use_container_width=True)
        st.image(img_final_rgb, caption="Hasil Koreksi Presisi (Kotak Hijau Mengunci Bulatan Asli)", use_container_width=True)
    else:
        st.error("Gagal meluruskan gambar. Pastikan batas tepi kertas LJK atau 4 kotak hijau terlihat jelas tanpa terpotong jari/bayangan.")
