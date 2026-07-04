import sys
from moviepy import VideoFileClip
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QScrollArea, QGridLayout, QMessageBox,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import cv2

import numpy as np
import cv2

def apply_color_correction(img_bgr, gamma=1.1, vibrance=1.15, warmth=1.10):
        # --- 1. Gamma correction ---
        # gamma > 1 brightens midtones
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
        img = cv2.LUT(img_bgr, table)

        # --- 2. Vibrance (smart saturation) ---
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= vibrance
        hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
        img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # --- 3. Warmth (boost red/yellow, reduce blue) ---
        b, g, r = cv2.split(img)
        r = np.clip(r * warmth, 0, 255)
        b = np.clip(b / warmth, 0, 255)
        img = cv2.merge([b.astype(np.uint8), g.astype(np.uint8), r.astype(np.uint8)])

        return img
    
def auto_white_balance(img):
    result = img.copy().astype(np.float32)

    avg_b = np.mean(result[..., 0])
    avg_g = np.mean(result[..., 1])
    avg_r = np.mean(result[..., 2])

    avg_gray = (avg_b + avg_g + avg_r) / 3

    result[..., 0] *= (avg_gray / avg_b)
    result[..., 1] *= (avg_gray / avg_g)
    result[..., 2] *= (avg_gray / avg_r)

    return np.clip(result, 0, 255).astype(np.uint8)

def sharpen(img):
    blur = cv2.GaussianBlur(img, (0, 0), 2)
    sharp = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
    return sharp

def kodak_film_look(img):
    # Convert to float
    img = img.astype(np.float32) / 255.0

    # --- Teal shadows / warm highlights ---
    r, g, b = img[..., 2], img[..., 1], img[..., 0]

    # Warm highlights (boost red/yellow)
    r = r * 1.08
    g = g * 1.02

    # Teal shadows (reduce red, boost blue)
    b = b * 1.10
    r = r * 0.95

    # --- Film contrast S-curve ---
    img = np.stack([b, g, r], axis=-1)
    img = np.clip(img, 0, 1)

    # S-curve
    img = img ** 0.9  # gentle contrast

    return (img * 255).astype(np.uint8)

def denoise(img):
    return cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)
 
def apply_full_color_pipeline(img_bgr):
    # Step 1: Auto white balance
    img = auto_white_balance(img_bgr)

    # Step 2: Noise reduction
    img = denoise(img)

    # Step 3: Kodak film look
    img = kodak_film_look(img)

    # Step 4: Sharpening
    img = sharpen(img)

    return img

 
class FramePicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Frame Picker – High Quality Thumbnails")

        self.clip = None
        self.frames = []
        self.selected_frame = None

        self.load_btn = QPushButton("Load MP4")
        self.load_btn.clicked.connect(self.load_video)

        self.preview_label = QLabel("Click a frame to preview it")
        self.preview_label.setFixedHeight(300)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background:#222;color:white;")

        self.save_btn = QPushButton("Save Selected Frame")
        self.save_btn.clicked.connect(self.save_frame)

        # Scrollable area for thumbnails
        self.scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.grid = QGridLayout(self.scroll_widget)
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(self.load_btn)
        layout.addWidget(self.scroll)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open MP4", "", "Videos (*.mp4)")
        if not path:
            return

        self.clip = VideoFileClip(path)
        duration = self.clip.duration
        fps = self.clip.fps
        total_frames = int(duration * fps)

        self.frames = []
        self.clear_grid()

        # Extract frames
        for i in range(total_frames):
            t = i / fps
            frame = self.clip.get_frame(t)
            self.frames.append(frame)
            self.add_thumbnail(frame, i)

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_thumbnail(self, frame, index):
        # MoviePy gives RGB → convert to BGR first
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Resize frame for thumbnail using high-quality downsampling
        thumb = cv2.resize(
            frame_bgr,
            (320, 180),
            interpolation=cv2.INTER_AREA
        )

        # Add frame number overlay
        cv2.putText(
            thumb,
            f"{index}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Convert to RGB for Qt
        rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        # Create label
        label = QLabel()
        label.setPixmap(pix)
        label.setStyleSheet("""
            border: 2px solid #555;
            border-radius: 8px;
            margin: 6px;
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(3, 3)
        label.setGraphicsEffect(shadow)

        # Click handler
        label.mousePressEvent = lambda e, idx=index: self.select_frame(idx)

        # Add to grid
        row = index // 4
        col = index % 4
        self.grid.addWidget(label, row, col)


    def select_frame(self, index):
        # MoviePy gives RGB → convert to BGR
        frame_bgr = cv2.cvtColor(self.frames[index], cv2.COLOR_RGB2BGR)

        # Store ORIGINAL frame for saving
        self.selected_frame_original = frame_bgr

        # Create enhanced preview (Kodak look, sharpening, etc.)
        corrected = apply_full_color_pipeline(frame_bgr)

        # Store corrected frame for preview only
        self.selected_frame_corrected = corrected

        # Convert corrected frame to RGB for Qt preview
        rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        pix = QPixmap.fromImage(qimg).scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

        self.preview_label.setPixmap(pix)



    def save_frame(self):
        if self.selected_frame_original is None:
            QMessageBox.warning(self, "No frame selected", "Click a frame first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG (*.png);;JPG (*.jpg)")
        if path:
            # Save the ORIGINAL frame (no color correction)
            cv2.imwrite(path, self.selected_frame_original)


app = QApplication(sys.argv)
window = FramePicker()
window.show()
sys.exit(app.exec())
