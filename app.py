import cv2
import numpy as np

def order_points(pts):
    # Mengurutkan titik sudut: kiri-atas, kanan-atas, kanan-bawah, kiri-bawah
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def get_warped(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Mencari kontur terbesar (asumsi LJK)
    doc_cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
    peri = cv2.arcLength(doc_cnt, True)
    approx = cv2.approxPolyDP(doc_cnt, 0.02 * peri, True)
    
    if len(approx) == 4:
        pts = order_points(approx.reshape(4, 2))
        (tl, tr, br, bl) = pts
        
        # Hitung lebar dan tinggi baru
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts, dst)
        return cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    return None

def scan_ljk(image_path):
    img = cv2.imread(image_path)
    warped = get_warped(img)
    
    if warped is None:
        print("LJK tidak terdeteksi. Harap sejajarkan 4 sudut!")
        return

    # Proses deteksi lingkaran pada gambar yang sudah diluruskan
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Di sini Anda bisa memotong (crop) area jawaban per nomor
    # dan menghitung jumlah piksel hitam (seperti koding sebelumnya)
    cv2.imshow("Hasil Lurus", warped)
    cv2.waitKey(0)

# Jalankan
# scan_ljk("foto_ljk.jpg")
