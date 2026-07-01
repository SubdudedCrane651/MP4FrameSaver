import sys
from moviepy import VideoFileClip
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QScrollArea, QGridLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import numpy as np
import cv2


class FramePicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Frame Picker – All Frames Visible")

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
        # Convert frame to QImage
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio)

        label = QLabel()
        label.setPixmap(pix)
        label.setStyleSheet("border:1px solid #444;")
        label.mousePressEvent = lambda e, idx=index: self.select_frame(idx)

        row = index // 5
        col = index % 5
        self.grid.addWidget(label, row, col)

    def select_frame(self, index):
        self.selected_frame = self.frames[index]

        rgb = cv2.cvtColor(self.selected_frame, cv2.COLOR_BGR2RGB)
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
        if self.selected_frame is None:
            QMessageBox.warning(self, "No frame selected", "Click a frame first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG (*.png);;JPG (*.jpg)")
        if path:
            cv2.imwrite(path, self.selected_frame)


app = QApplication(sys.argv)
window = FramePicker()
window.show()
sys.exit(app.exec())
