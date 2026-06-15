import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_image_cropper import st_cropper

st.set_page_config(page_title="Koreksi LJK Interaktif", layout="centered")

st.title("📸 Pemindai LJK - Geser Pembatas Kertas")
st.write("Geser dan tarik kotak pembatas di bawah menggunakan jari Anda hingga pas membungkus area lembar jawaban LJK.")

# 1. UPLOAD GAMBAR
uploaded_file = st.file_uploader("Unggah atau Ambil Foto LJK...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Buka gambar menggunakan PIL untuk dialirkan ke komponen Cropper
    img_pil = Image.open(uploaded_file)
    
    st.subheader("📐 Langkah 1: Geser & Sesuaikan Kotak Pembatas")
    st.info("Tarik ujung-ujung kotak di bawah ini agar pas mengurung kertas LJK Anda, lalu lihat hasilnya di bawah.")
    
    # Menampilkan fungsi CROPPER INTERAKTIF (Bisa digeser/tarik langsung di HP)
    # Box_color adalah warna garis pembatas (kita pakai merah agar jelas)
    cropped_img_pil = st_cropper(
        img_pil, 
        realtime_update=True, 
        box_color='#FF0000', 
        aspect_ratio=None
    )
    
    # 2. PROSES PERSPECTIVE & GRID MATEMATIS OTOMATIS
    # Mengubah hasil potongan gambar interaktif tadi ke format OpenCV
    img_cropped = cv2.cvtColor(np.array(cropped_img_pil), cv2.COLOR_RGB2BGR)
    
    # Paksa hasil potongan menjadi resolusi standar presisi tinggi (600 x 850 piksel)
    width, height = 600, 850
    warped = cv2.resize(img_cropped, (width, height))
    output_display = warped.copy()
    
    # 3. KISI MATEMATIS UTALISASI BULATAN (Pasti Pas jika pemotongan kertas rapi)
    def buat_grid_tetap():
        map_soal = {}
        j_opsi, j_baris = 18, 21
        
        # Blok Atas (Soal 11-20 dan 31-40)
        for i in range(10):
            map_soal[11 + i] = [(240 + (j * j_opsi), 115 + (i * j_baris)) for j in range(5)]
            map_soal[31 + i] = [(395 + (j * j_opsi), 115 + (i * j_baris)) for j in range(5)]
        # Blok Bawah (Soal 1-10, 21-30, 41-50)
        for i in range(10):
            map_soal[1 + i] = [(112 + (j * j_opsi), 433 + (i * j_baris)) for j in range(5)]
            map_soal[21 + i] = [(242 + (j * j_opsi), 433 + (i * j_baris)) for j in range(5)]
            map_soal[41 + i] = [(397 + (j * j_opsi), 433 + (i * j_baris)) for j in range(5)]
        return map_soal

    grid_ljk = buat_grid_tetap()
    
    # Gambar seleksi bulatan hijau nomor 1-50
    for q_num, opsi_list in grid_ljk.items():
        x_lbl, y_lbl = opsi_list[0]
        # Gambar nomor soal warna merah kecil
        cv2.putText(output_display, f"{q_num}", (x_lbl - 22, y_lbl + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        for (cx, cy) in opsi_list:
            # Menggambar bulatan hijau seleksi pilihan ganda
            cv2.circle(output_display, (cx, cy), 8, (0, 255, 0), 1)
            cv2.circle(output_display, (cx, cy), 1, (0, 0, 255), -1)

    # 4. TAMPILKAN HASILNYA DI BAWAHNYA SECARA REAL-TIME
    st.markdown("---")
    st.subheader("🎯 Langkah 2: Hasil Seleksi Otomatis Nomor 1-50")
    st.write("Jika bulatan hijau belum pas, silakan sesuaikan kembali kotak pembatas merah di atas.")
    
    st.image(
        cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), 
        caption="Hasil Seleksi Bulatan Pasca Pemotongan", 
        use_container_width=True
    )
