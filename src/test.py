import sys

import cv2
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def convert_cv_qt(self, cv_img):
    """Convert from an opencv image to QPixmap"""
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
    # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
    return QPixmap.fromImage(convert_to_Qt_format)


class ImageLabel(QLabel):
    image_click_event = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Still good for fallback
        self.original_pixmap = QPixmap("yeah.jpg")  # Replace with your image path
        self.setMinimumSize(10, 10)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.scaled_pixmap = None

    def update_image(self, image):
        qt_img = convert_cv_qt(image)
        self.original_pixmap = qt_img
        self.update()

    def resizeEvent(self, _):

        self.update()  # Trigger repaint

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.original_pixmap.isNull():
            self.scaled_pixmap = self.original_pixmap.scaled(
                self.size().width(),  # Full label width
                self.size().height(),  # Full label height (will be trimmed by aspect)
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        if self.scaled_pixmap:
            painter = QPainter(self)
            # Compute left margin to center horizontally
            x_offset = (self.width() - self.scaled_pixmap.width()) // 2
            painter.drawPixmap(x_offset, 0, self.scaled_pixmap)

    def mousePressEvent(self, event):
        if self.scaled_pixmap is None:
            return

        # Compute horizontal margin from centering
        margin_x = (self.width() - self.scaled_pixmap.width()) // 2
        margin_y = 0  # Top-aligned

        click_x = event.pos().x() - margin_x
        click_y = event.pos().y() - margin_y

        if 0 <= click_x < self.scaled_pixmap.width() and 0 <= click_y < self.scaled_pixmap.height():
            scale_x = self.original_pixmap.width() / self.scaled_pixmap.width()
            scale_y = self.original_pixmap.height() / self.scaled_pixmap.height()
            orig_x = int(click_x * scale_x)
            orig_y = int(click_y * scale_y)
            self.image_click_event.emit((orig_x, orig_y))
        # else:
        #     print("Clicked outside the image area.")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        font = QFont()
        font.setPointSize(20)  # Set text size to 20 points

        self.setWindowTitle("Custom Layout")

        # === Top Bar (10% height) ===
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)

        def add_top_layout_label(text):
            label = QLabel(text)
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)
            top_layout.addWidget(label, alignment=Qt.AlignCenter)
            return label

        add_top_layout_label("Tracking Status:")
        track_status = add_top_layout_label("Not Tracking")
        add_top_layout_label("Recording Status:")
        track_status = add_top_layout_label("Not Recording")

        # === Main Content ===
        main_content = QWidget()
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Left (70%): Image
        image_label = ImageLabel()
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Right (30%): Vertical labels
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        for i in range(6):
            right_layout.addWidget(QLabel(f"Right Label {i+1}"))
        right_layout.addStretch()

        main_layout.addWidget(image_label, 7)
        main_layout.addWidget(right_panel, 3)

        # === Full Layout ===
        full_layout = QVBoxLayout(self)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.addWidget(top_bar, 1)
        full_layout.addWidget(main_content, 9)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
