from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import sys
# need to add pyqt5 to prerequisites

# https://imagetracking.org.uk/2020/12/displaying-opencv-images-in-pyqt/

import time
from queue import Queue, Empty

from legolas_common.src.packet_types import BROADCAST_DEST, Packet, PacketType
from legolas_common.src.socket_client import SocketClient



class ReadIncomingMsgThread(QThread):
    change_incoming_message = pyqtSignal(Packet)

    def __init__(self, incoming_data: Queue):
        super().__init__()
        self.incoming_data = incoming_data


    def run(self):
        while True:
            time.sleep(1)
            try:
                new_packet = self.incoming_data.get_nowait() # need to make sure socket_client isn't eating these messages first
                print("RECEIVED MESSAGE FROM SERVER", GUI.packet_to_str(new_packet))
            except Empty:
                # print("no msg from server")
                continue
            self.change_incoming_message.emit(new_packet)




class GUI(QWidget):
    def __init__(self, outgoing_data: Queue, incoming_data: Queue ):
        super().__init__()
        self.setWindowTitle("LEGOLAS GUI")
        self.label_img = QLabel(parent=self)
        self.incoming_msg_label = QLabel(parent=self)
        self.incoming_msg_label.setText("MESSAGE LABEL")
        pixmap = QPixmap("yeah.jpg")
        self.button = QPushButton("send message", self)
        self.button.clicked.connect(self.on_click)
        self.change_img_button = QPushButton("change image", self)
        self.change_img_button.clicked.connect(self.change_img)
        self.original_img = True

        self.label_img.setPixmap(pixmap)

        layout = QHBoxLayout(self)
        layout.addWidget(self.incoming_msg_label)
        layout.addWidget(self.label_img)
        layout.addWidget(self.button)
        layout.addWidget(self.change_img_button)
    
        self.setLayout(layout)

        self.update_thread = ReadIncomingMsgThread(incoming_data)
        self.update_thread.change_incoming_message.connect(self.update_incoming_msg)
        self.incoming_data = incoming_data
        self.outgoing_data = outgoing_data
        self.update_thread.start()

    def on_click(self):
        print("send button pressed")
        self.outgoing_data.put(Packet(
                        PacketType.CONTROL,
                        BROADCAST_DEST,  # This doesn't actually matter
                        {"hello": "server", "time": time.time()},
                    ))

    def change_img(self):
        if self.original_img: 
            new_pixmap = QPixmap("yeah2.jpg")
            self.label_img.setPixmap(new_pixmap)
            self.original_img = False
        else:
            old_pixmap = QPixmap("yeah.jpg")
            self.label_img.setPixmap(old_pixmap)
            self.original_img = True

    @pyqtSlot(Packet)
    def update_incoming_msg(self, msg:Packet):
        text = GUI.packet_to_str(msg)
        self.incoming_msg_label.setText(text)

    @staticmethod # move this somewhere else where it makes more sense?
    def packet_to_str( msg : Packet) -> str:
        # print(f"From {msg.packet_address}: ", end="")
        print("WERE TRYING TO CHANGE THE LABEL")
        if msg.packet_type == PacketType.INTERNAL:
            return f"Received internal: {msg.payload}"
        elif msg.packet_type == PacketType.CONTROL:
            return f"Received control: {msg.payload}"
        elif msg.packet_type == PacketType.IMAGE:
            return "Received image"
        else:
            return f"Received ack: {msg.payload}"


if __name__ == "__main__":
    app = QApplication([])
    global_incoming_data: Queue[Packet] = Queue()
    global_outgoing_data: Queue[Packet] = Queue()
    client = SocketClient("127.0.0.1", 12348, global_outgoing_data, global_incoming_data)
    a = GUI(global_outgoing_data, global_incoming_data)
    a.show()
    client.run()
    app.exec()
    # what is Error receiving: [WinError 10038] An operation was attempted on something that is not a socket
    client.shutdown()
