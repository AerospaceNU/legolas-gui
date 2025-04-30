import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Still good for fallback
        self.original_pixmap = QPixmap("yeah.jpg")  # Replace with your image path
        self.setMinimumSize(10, 10)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.scaled_pixmap = None

    def resizeEvent(self, event):
        if not self.original_pixmap.isNull():
            self.scaled_pixmap = self.original_pixmap.scaled(
                self.size().width(),  # Full label width
                self.size().height(),  # Full label height (will be trimmed by aspect)
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        super().paintEvent(event)
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
            print(f"Clicked on image at: ({orig_x}, {orig_y})")
        else:
            print("Clicked outside the image area.")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Layout")

        # === Top Bar (10% height) ===
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)
        for i in range(5):
            top_layout.addWidget(QLabel(f"Top Label {i+1}"))

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
