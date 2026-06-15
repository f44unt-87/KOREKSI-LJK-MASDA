import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi Masda", layout="centered")

st.title("📸 Pemindai LJK - Geser Gambar")
st.write("Tekan tombol panah di bawah untuk menggeser posisi foto LJK Anda sampai masuk pas ke dalam lingkaran target hijau.")

# --- INISIALISASI PENYIMPANAN POSISI (SESSION STATE) ---
if 'shift_x' not in st.session_state:
    st.session_state['shift_x'] = 0
if 'shift_y' not in st.session_state:
    st.session_state['shift_y'] = 0
if 'zoom' not in st.session_state:
    st.session_state['zoom'] = 100

# 1. FITUR UPLOAD FOTO
uploaded_file = st.file_uploader("Unggah atau Ambil Foto LJK...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Menyamakan ukuran dasar gambar agar pas dengan cetakan matematika LJK Anda
    width, height = 600, 850
    img_resized = cv2.resize(img_raw, (width, height))
    
    # --- TOMBOL NAVIGASI UNTUK MENGGESER FOTO ---
    st.write("### 🎮 Tombol Penggeser Foto:")
    
    # Baris tombol atas
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔼 GESER ATAS", use_container_width=True):
            st.session_state['shift_y'] -= 4  # Menggeser foto ke atas sebanyak 4 piksel

    # Baris tombol kiri dan kanan
    col_l, col_space, col_r = st.columns([1, 1, 1])
    with col_l:
        if st.button("◀️ GESER KIRI", use_container_width=True):
            st.session_state['shift_x'] -= 4  # Menggeser foto ke kiri
    with col_space:
        if st.button("🔄 RESET", use_container_width=True):
            st.session_state['shift_x'] = 0
            st.session_state['shift_y'] = 0
            st.session_state['zoom'] = 100
    with col_r:
        if st.button("▶️ GESER KANAN", use_container_width=True):
            st.session_state['shift_x'] += 4  # Menggeser foto ke kanan

    # Baris tombol bawah
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b2:
        if st.button("🔽 GESER BAWAH", use_container_width=True):
            st.session_state['shift_y'] += 4  # Menggeser foto ke bawah
            
    # Slider Zoom untuk membesarkan/mengecilkan ukuran foto agar pas dengan grid
    st.session_state['zoom'] = st.slider("🔍 Ukuran Kertas / Zoom (%)", 70, 130, st.session_state['zoom'])

    # 2. EKSEKUSI PERGESERAN FOTO (TRANSLASI & ZOOM)
    tx = st.session_state['shift_x']
    ty = st.session_state['shift_y']
    scale = st.session_state['zoom'] / 100.0
    
    # Proses pembesaran (zoom) terpusat di tengah kertas
    M_scale = cv2.getRotationMatrix2D((width/2, height/2), 0, scale)
    img_transformed = cv2.warpAffine(img_resized, M_scale, (width, height))
    
    # Proses pergeseran foto ke atas/bawah/kanan/kiri
    M_translate = np.float32([[1, 0, tx], [0, 1, ty]])
    img_transformed = cv2.warpAffine(img_transformed, M_translate, (width, height))
    
    output_display = img_transformed.copy()

    # 3. CETAKAN TARGET TETAP (GRID UTAMA NOMOR 1-50)
    # Lingkaran ini posisinya diam terkunci di layar, menanti foto digeser tepat di bawahnya
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
    for q_num, opsi_list in grid_ljk.items():
        x_lbl, y_lbl = opsi_list[0]
        # Tampilkan nomor soal penanda berwarna merah di layar
        cv2.putText(output_display, f"{q_num}", (x_lbl - 22, y_lbl + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        for (cx, cy) in opsi_list:
            # Tampilkan bulatan hijau target pas
            cv2.circle(output_display, (cx, cy), 8, (0, 255, 0), 1)

    # 4. TAMPILKAN GAMBAR HASIL PERGESERAN
    st.image(
        cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), 
        caption="Hasil Penyelarasan Posisi Gambar LJK", 
        use_container_width=True
    )
