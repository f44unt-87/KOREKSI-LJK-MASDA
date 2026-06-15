import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Presisi Masda", layout="centered")

st.title("📸 Pemindai LJK - Paskan Kertas")
st.write("Silakan unggah foto LJK. Tekan tombol panah untuk menggeser kertas fotonya sampai pas masuk ke dalam lingkaran target hijau.")

# --- INISIALISASI SESSION STATE UNTUK MENYIMPAN POSISI GESER ---
if 'shift_x' not in st.session_state:
    st.session_state['shift_x'] = 0
if 'shift_y' not in st.session_state:
    st.session_state['shift_y'] = 0
if 'zoom' not in st.session_state:
    st.session_state['zoom'] = 100

# 1. FORM UPLOAD FOTO LJK
uploaded_file = st.file_uploader("Unggah atau Ambil Foto LJK...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Standarkan resolusi gambar ke 600 x 850 piksel agar pas di layar iPhone
    width, height = 600, 850
    img_resized = cv2.resize(img_raw, (width, height))
    
    # --- TOMBOL NAVIGASI INTERAKTIF ---
    st.write("### 🎮 Tombol Penggeser Kertas:")
    
    # Baris Tombol Atas
    col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
    with col_t2:
        if st.button("🔼 GESER ATAS", use_container_width=True):
            st.session_state['shift_y'] -= 8  # Naikkan kertas ke atas

    # Baris Tombol Kiri, Reset, Kanan
    col_l, col_space, col_r = st.columns([1, 1, 1])
    with col_l:
        if st.button("◀️ GESER KIRI", use_container_width=True):
            st.session_state['shift_x'] -= 8  # Geser kertas ke kiri
    with col_space:
        if st.button("🔄 RESET", use_container_width=True):
            st.session_state['shift_x'] = 0
            st.session_state['shift_y'] = 0
            st.session_state['zoom'] = 100
    with col_r:
        if st.button("▶️ GESER KANAN", use_container_width=True):
            st.session_state['shift_x'] += 8  # Geser kertas ke kanan

    # Baris Tombol Bawah
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b2:
        if st.button("🔽 GESER BAWAH", use_container_width=True):
            st.session_state['shift_y'] += 8  # Turunkan kertas ke bawah
            
    # Slider Zoom untuk mencocokkan skala kertas LJK
    st.session_state['zoom'] = st.slider("🔍 Ukuran Kertas / Zoom (%)", 50, 150, st.session_state['zoom'])

    # 2. PROSES PERGESERAN GAMBAR BERDASARKAN TOMBOL DAN SLIDER
    tx = st.session_state['shift_x']
    ty = st.session_state['shift_y']
    scale = st.session_state['zoom'] / 100.0
    
    # Eksekusi Pembesaran (Zoom) terpusat di tengah layar
    M_scale = cv2.getRotationMatrix2D((width/2, height/2), 0, scale)
    img_transformed = cv2.warpAffine(img_resized, M_scale, (width, height))
    
    # Eksekusi Pergeseran Posisi Gambar
    M_translate = np.float32([[1, 0, tx], [0, 1, ty]])
    img_transformed = cv2.warpAffine(img_transformed, M_translate, (width, height))
    
    output_display = img_transformed.copy()

    # 3. KISI TARGET MATEMATIS TETAP (MAPPING SOAL 1-50)
    # Koordinat ini telah dikalibrasi ulang agar langsung membidik area LJK Masda Anda
    def buat_grid_kalibrasi():
        map_soal = {}
        j_opsi = 17   # Jarak horizontal antar bulatan A-E
        j_baris = 19  # Jarak vertikal antar baris soal
        
        # --- BLOK ATAS ---
        # Kolom Tengah (Soal 11-20)
        for i in range(10):
            map_soal[11 + i] = [(225 + (j * j_opsi), 220 + (i * j_baris)) for j in range(5)]
        # Kolom Kanan (Soal 31-40)
        for i in range(10):
            map_soal[31 + i] = [(380 + (j * j_opsi), 220 + (i * j_baris)) for j in range(5)]
            
        # --- BLOK BAWAH ---
        # Kolom Kiri (Soal 1-10)
        for i in range(10):
            map_soal[1 + i] = [(80 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
        # Kolom Tengah (Soal 21-30)
        for i in range(10):
            map_soal[21 + i] = [(225 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
        # Kolom Kanan (Soal 41-50)
        for i in range(10):
            map_soal[41 + i] = [(380 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
            
        return map_soal

    grid_ljk = buat_grid_kalibrasi()
    
    # Gambar target lingkaran hijau 1-50 tepat di atas foto yang digeser
    for q_num, opsi_list in grid_ljk.items():
        x_lbl, y_lbl = opsi_list[0]
        # Beri teks penanda nomor soal warna merah kecil di layar
        cv2.putText(output_display, f"{q_num}", (x_lbl - 20, y_lbl + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1)
        for (cx, cy) in opsi_list:
            # Menggambar bulatan hijau cetakan target
            cv2.circle(output_display, (cx, cy), 7, (0, 255, 0), 1)

    # 4. TAMPILKAN HASILNYA KE LAYAR HP IPHONE
    st.image(
        cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), 
        caption="Paskan posisi bulatan hitam kertas ke dalam lingkaran hijau target di atas", 
        use_container_width=True
    )
