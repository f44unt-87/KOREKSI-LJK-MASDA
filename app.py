import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Koreksi LJK Akurat", layout="centered")

st.title("📸 Pemindai LJK - Penyelaras Sudut Kertas")
st.write("Sesuaikan 4 sudut di bawah ini agar garis kotak merah membungkus pas 4 kotak hijau pada kertas LJK Anda.")

# 1. FITUR UPLOAD FOTO
uploaded_file = st.file_uploader("Unggah atau Ambil Foto LJK...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Perkecil resolusi tampilan awal agar pas di layar HP iPhone (Tinggi 800px)
    h_orig, w_orig = img_raw.shape[:2]
    scale_view = 800 / h_orig
    img_view = cv2.resize(img_raw, (int(w_orig * scale_view), 800))
    h_v, w_v = img_view.shape[:2]
    
    # --- SLIDER UNTUK MENYESUAIKAN 4 SUDUT KERTAS ---
    st.write("### 🛠️ Tarik Slider Sudut Kertas:")
    
    col_tl, col_tr = st.columns(2)
    with col_tl:
        st.write("**Pojok Kiri Atas**")
        tl_x = st.slider("Kiri Atas - Kanan/Kiri (X)", 0, w_v, int(w_v * 0.05), key="tlx")
        tl_y = st.slider("Kiri Atas - Atas/Bawah (Y)", 0, h_v, int(h_v * 0.1), key="tly")
    with col_tr:
        st.write("**Pojok Kanan Atas**")
        tr_x = st.slider("Kanan Atas - Kanan/Kiri (X)", 0, w_v, int(w_v * 0.95), key="trx")
        tr_y = st.slider("Kanan Atas - Atas/Bawah (Y)", 0, h_v, int(h_v * 0.1), key="try")
        
    col_bl, col_br = st.columns(2)
    with col_bl:
        st.write("**Pojok Kiri Bawah**")
        bl_x = st.slider("Kiri Bawah - Kanan/Kiri (X)", 0, w_v, int(w_v * 0.05), key="blx")
        bl_y = st.slider("Kiri Bawah - Atas/Bawah (Y)", 0, h_v, int(h_v * 0.9), key="bly")
    with col_br:
        st.write("**Pojok Kanan Bawah**")
        br_x = st.slider("Kanan Bawah - Kanan/Kiri (X)", 0, w_v, int(w_v * 0.95), key="brx")
        br_y = st.slider("Kanan Bawah - Atas/Bawah (Y)", 0, h_v, int(h_v * 0.9), key="bry")

    # Gambar garis panduan merah di atas foto asli
    img_guide = img_view.copy()
    pts_guide = np.array([[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]], np.int32)
    cv2.polylines(img_guide, [pts_guide], True, (0, 0, 255), 3) # Garis kotak merah pembungkus
    for pt in pts_guide:
        cv2.circle(img_guide, tuple(pt), 10, (255, 0, 0), -1) # Titik biru di tiap sudut

    st.image(cv2.cvtColor(img_guide, cv2.COLOR_BGR2RGB), caption="1. Panduan: Pas-kan titik sudut ini ke kotak hijau LJK Anda", use_container_width=True)

    # 2. PROSES WARP PERSPECTIVE (MELURUSKAN & MENYESUAIKAN UKURAN OTOMATIS)
    pts1 = np.float32([[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]])
    width_w, height_w = 600, 850
    pts2 = np.float32([[0, 0], [width_w, 0], [width_w, height_w], [0, height_w]])
    
    M_matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img_view, M_matrix, (width_w, height_w))
    output_display = warped.copy()

    # 3. KISI TARGET MATEMATIS TETAP (MAPPING SOAL 1-50)
    def buat_grid_kalibrasi():
        map_soal = {}
        j_opsi = 17   # Jarak horizontal antar bulatan A-E
        j_baris = 19  # Jarak vertikal antar baris soal
        
        # --- BLOK ATAS ---
        for i in range(10):
            map_soal[11 + i] = [(225 + (j * j_opsi), 220 + (i * j_baris)) for j in range(5)]
            map_soal[31 + i] = [(380 + (j * j_opsi), 220 + (i * j_baris)) for j in range(5)]
            
        # --- BLOK BAWAH ---
        for i in range(10):
            map_soal[1 + i] = [(80 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
            map_soal[21 + i] = [(225 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
            map_soal[41 + i] = [(380 + (j * j_opsi), 525 + (i * j_baris)) for j in range(5)]
            
        return map_soal

    grid_ljk = buat_grid_kalibrasi()
    
    # Menggambar lingkaran hijau seleksi di atas kertas hasil pelurusan
    for q_num, opsi_list in grid_ljk.items():
        x_lbl, y_lbl = opsi_list[0]
        cv2.putText(output_display, f"{q_num}", (x_lbl - 20, y_lbl + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1)
        for (cx, cy) in opsi_list:
            cv2.circle(output_display, (cx, cy), 7, (0, 255, 0), 1)

    # 4. TAMPILKAN HASILNYA
    st.markdown("---")
    st.subheader("🎯 Hasil Seleksi Otomatis Nomor 1-50")
    st.image(cv2.cvtColor(output_display, cv2.COLOR_BGR2RGB), caption="Hasil Akhir: Bulatan Otomatis Mengunci Pas Pasca Penyelarasan", use_container_width=True)
