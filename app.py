import cv2
import numpy as np
import gradio as gr

def urutkan_kontur(cnts, method="left-to-right"):
    if not cnts:
        return []
    i = 1 if method in ["top-to-bottom", "bottom-to-top"] else 0
    reverse = method in ["right-to-left", "bottom-to-top"]
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    cnts, _ = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b: b[1][i], reverse=reverse))
    return cnts

def proses_ljk_gradio(nama_siswa, kelas_siswa, nama_mapel, kelas_ujian, 
                       kunci_1, kunci_2, kunci_3, kunci_4, kunci_5, 
                       input_gambar):
    # 1. Validasi Input Nama Siswa
    if not nama_siswa.strip():
        return None, "⚠️ ERROR: Nama Siswa wajib diisi sebelum melakukan koreksi!"

    # 2. Validasi Input Gambar
    if input_gambar is None:
        return None, "⚠️ ERROR: Silakan unggah file gambar atau ambil foto LJK terlebih dahulu!"

    # 3. Konfigurasi Kunci Jawaban dari Form
    ans_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    kunci_jawaban = {
        0: ans_map[kunci_1],
        1: ans_map[kunci_2],
        2: ans_map[kunci_3],
        3: ans_map[kunci_4],
        4: ans_map[kunci_5]
    }
    
    total_soal = 5
    total_pilihan = 5
    tampilan_kelas = kelas_siswa.strip().upper() if kelas_siswa.strip() else "-"
    tampilan_mapel = nama_mapel.strip().upper() if nama_mapel.strip() else "-"
    tampilan_kelas_ujian = kelas_ujian.strip().upper() if kelas_ujian.strip() else "-"

    # 4. Membaca Gambar (Gradio mengirimkan gambar dalam format RGB NumPy Array)
    image = cv2.cvtColor(input_gambar, cv2.COLOR_RGB2BGR)
    output = image.copy()
    
    # 5. Pre-processing Gambar
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # 6. Cari Kontur Lingkaran LJK
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    kontur_lingkaran = []

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if w >= 20 and h >= 20 and 0.8 <= ar <= 1.2:
            kontur_lingkaran.append(c)

    # Jika bulatan tidak terdeteksi lengkap
    if len(kontur_lingkaran) < (total_soal * total_pilihan):
        pesan_error = (
            f"❌ Gagal memproses! Hanya mendeteksi {len(kontur_lingkaran)} bulatan jawaban.\n\n"
            f"Tips Penggunaan di iPhone:\n"
            f"1. Pastikan posisi LJK tegak lurus (tidak miring).\n"
            f"2. Cari ruangan dengan pencahayaan terang agar tidak ada bayangan HP.\n"
            f"3. Pastikan seluruh batas kertas LJK masuk ke dalam frame kamera."
        )
        return input_gambar, pesan_error

    # 7. Mengurutkan Soal (Atas ke Bawah)
    kontur_lingkaran = urutkan_kontur(kontur_lingkaran, method="top-to-bottom")
    benar = 0

    # 8. Analisis Jawaban Siswa
    for q, i in enumerate(range(0, len(kontur_lingkaran), total_pilihan)):
        cnts_pilihan = urutkan_kontur(kontur_lingkaran[i:i + total_pilihan], method="left-to-right")
        diarsir = None

        for j, c in enumerate(cnts_pilihan):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.bitwise_and(thresh, mask)
            total = cv2.countNonZero(mask)

            if diarsir is None or total > diarsir[0]:
                diarsir = (total, j)

        kunci = kunci_jawaban[q]
        warna = (0, 255, 0) if kunci == diarsir[1] else (0, 0, 255)
        
        if kunci == diarsir[1]:
            benar += 1

        cv2.drawContours(output, [cnts_pilihan[kunci]], -1, warna, 3)

    # 9. Kalkulasi Skor Akhir
    skor = (benar / total_soal) * 100
    
    # 10. Format Output Text Ringkasan
    hasil_teks = (
        f"📝 **IDENTITAS UJIAN & SISWA**\n"
        f"• Nama Siswa : {nama_siswa.upper()}\n"
        f"• Kelas Siswa : {tampilan_kelas}\n"
        f"• Mata Pelajaran : {tampilan_mapel}\n"
        f"• Kelas Ujian : {tampilan_kelas_ujian}\n\n"
        f"📊 **HASIL KOREKSI**\n"
        f"• Jumlah Benar : {benar} / {total_soal} Soal\n"
        f"• 💯 **NILAI AKHIR : {skor:.2f}**"
    )
    
    # Kembalikan gambar dalam format RGB untuk Gradio
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
    return output_rgb, hasil_teks

# --- MEMBANGUN ANTARMUKA GRADIO WEB ---
with gr.Blocks(title="KOREKSI CEPAT MASLAKUL HUDA", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown(
        """
        # 🏛️ KOREKSI CEPAT MASLAKUL HUDA
        Aplikasi pemindai dan korektor Lembar Jawab Komputer (LJK) instan berbasis web.
        """
    )
    
    with gr.Row():
        # Kolom Kiri: Input Informasi & Kunci Jawaban
        with gr.Column():
            gr.Markdown("### 👤 Data Siswa & Ujian")
            nama_siswa = gr.Textbox(label="Nama Siswa (Wajib)", placeholder="Masukkan nama siswa...")
            kelas_siswa = gr.Textbox(label="Kelas Siswa (Opsional)", placeholder="Contoh: 10-A, 11-B...")
            nama_mapel = gr.Textbox(label="Nama Mata Pelajaran", placeholder="Contoh: Matematika, Fiqih...")
            kelas_ujian = gr.Textbox(label="Kelas Ujian", placeholder="Contoh: Kelas 9, Kelas 12...")
            
            gr.Markdown("### 🔑 Pengaturan Kunci Jawaban (5 Soal)")
            with gr.Row():
                kunci_1 = gr.Dropdown(['A', 'B', 'C', 'D', 'E'], value='A', label="Soal 1")
                kunci_2 = gr.Dropdown(['A', 'B', 'C', 'D', 'E'], value='C', label="Soal 2")
                kunci_3 = gr.Dropdown(['A', 'B', 'C', 'D', 'E'], value='D', label="Soal 3")
                kunci_4 = gr.Dropdown(['A', 'B', 'C', 'D', 'E'], value='A', label="Soal 4")
                kunci_5 = gr.Dropdown(['A', 'B', 'C', 'D', 'E'], value='E', label="Soal 5")

        # Kolom Kanan: Kamera & Hasil Scanning
        with gr.Column():
            gr.Markdown("### 📷 Ambil / Unggah Gambar LJK")
            # Komponen gambar Gradio otomatis menyediakan tombol kamera dan upload file di iPhone
            input_gambar = gr.Image(label="Kamera / File Gambar LJK", sources=["webcam", "upload"], type="numpy")
            
            btn_proses = gr.Button("🚀 MULAI KOREKSI LEMBAR JAWABAN", variant="primary")
            
            gr.Markdown("### 📋 Hasil Penilaian")
            output_text = gr.Markdown(value="Hasil nilai akan muncul di sini setelah menekan tombol koreksi.")
            output_gambar = gr.Image(label="Visualisasi Hasil Koreksi Bulatan")

    # Logika Trigger Tombol Klik
    btn_proses.click(
        fn=proses_ljk_gradio,
        inputs=[nama_siswa, kelas_siswa, nama_mapel, kelas_ujian, 
                kunci_1, kunci_2, kunci_3, kunci_4, kunci_5, input_gambar],
        outputs=[output_gambar, output_text]
    )

# Menjalankan aplikasi secara lokal dan membuat tautan publik shareable
if __name__ == "__main__":
    demo.launch(share=True)
