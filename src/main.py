from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
# need to add pyqt5 to prerequisites

def on_click():
    print("button pressed")

def main() -> None:
    """Program entrypoint"""

    app = QApplication([])
    window = QWidget()
    label = QLabel("YEAHHHHHHH")
    pixmap = QPixmap("yeah.jpg")
    button = QPushButton("send message", window)
    button.clicked.connect(on_click)
    label.setPixmap(pixmap)

    layout = QHBoxLayout(window)
    layout.addWidget(label)
    layout.addWidget(button)

    window.show()
    app.exec()
    


if __name__ == "__main__":
    main()
