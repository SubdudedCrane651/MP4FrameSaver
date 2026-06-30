import cv2
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QFileDialog, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt


class FrameExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Frame Extractor")

        self.video = None
        self.current_frame = 0

        self.label = QLabel("Load a video to begin")
        self.label.setStyleSheet("background: #222; color: white; padding: 20px;")

        load_btn = QPushButton("Load MP4")
        prev_btn = QPushButton("Previous Frame")
        next_btn = QPushButton("Next Frame")
        save_btn = QPushButton("Save This Frame")

        load_btn.clicked.connect(self.load_video)
        prev_btn.clicked.connect(self.prev_frame)
        next_btn.clicked.connect(self.next_frame)
        save_btn.clicked.connect(self.save_frame)

        h = QHBoxLayout()
        h.addWidget(prev_btn)
        h.addWidget(next_btn)
        h.addWidget(save_btn)

        layout = QVBoxLayout()
        layout.addWidget(load_btn)
        layout.addWidget(self.label)
        layout.addLayout(h)

        self.setLayout(layout)

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open MP4", "", "Videos (*.mp4)")
        if path:
            self.video = cv2.VideoCapture(path)
            self.current_frame = 0
            self.show_frame()

    def show_frame(self):
        if not self.video:
            return

        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        success, frame = self.video.read()

        if not success:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.label.width(), self.label.height(),
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio

        ))

        self.last_frame = frame  # store raw frame for saving

    def prev_frame(self):
        if self.video and self.current_frame > 0:
            self.current_frame -= 1
            self.show_frame()

    def next_frame(self):
        if self.video:
            self.current_frame += 1
            self.show_frame()

    def save_frame(self):
        if hasattr(self, "last_frame"):
            path, _ = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG (*.png);;JPG (*.jpg)")
            if path:
                cv2.imwrite(path, self.last_frame)

app = QApplication(sys.argv)
window = FrameExtractor()
window.show()
sys.exit(app.exec())
