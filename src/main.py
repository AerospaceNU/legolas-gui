from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
import sys
# need to add pyqt5 to prerequisites

# potential gui feature: view received frames in an album 

class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("YEAHHHHHHH")
        pixmap = QPixmap("yeah.jpg")
        self.button = QPushButton("send message", self)
        self.button.clicked.connect(self.on_click)
        self.change_img_button = QPushButton("change image", self)
        self.change_img_button.clicked.connect(self.change_img)
        self.original_img = True

        self.label.setPixmap(pixmap)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.change_img_button)
        self.setLayout(layout)

    def on_click(self):
        print("button pressed")

    def change_img(self):
        if self.original_img: 
            new_pixmap = QPixmap("yeah2.jpg")
            self.label.setPixmap(new_pixmap)
            self.original_img = False
        else:
            old_pixmap = QPixmap("yeah.jpg")
            self.label.setPixmap(old_pixmap)
            self.original_img = True

    


if __name__ == "__main__":
    app = QApplication([])
    a = GUI()
    a.show()
    sys.exit(app.exec_())
