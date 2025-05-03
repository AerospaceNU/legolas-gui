import sys
import time
from queue import Empty, Queue

import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QVBoxLayout,
    QWidget,
    # QSpinBox, 
    QDoubleSpinBox,
    QSlider
)

from legolas_common.src.frame_annotator import draw_tracked_object
from legolas_common.src.packet_types import BROADCAST_DEST, Packet, PacketType
from legolas_common.src.socket_client import SocketClient

# TODO: update requirements.txt

# https://imagetracking.org.uk/2020/12/displaying-opencv-images-in-pyqt/

def convert_cv_qt(cv_img):
    """Convert from an opencv image to QPixmap"""
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
    # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
    return QPixmap.fromImage(convert_to_Qt_format)

class ReadIncomingMsgThread(QThread):
    recieve_packet = pyqtSignal(Packet)  # change when internal/control, and image

    def __init__(self, incoming_data: Queue):
        super().__init__()
        self.incoming_data = incoming_data

    def run(self):
        while True:
            time.sleep(0.00001)
            try:
                new_packet = (
                    self.incoming_data.get_nowait()
                )

                self.recieve_packet.emit(new_packet)
            except Empty:
                continue

class ImageLabel(QLabel):
    image_click_event = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Still good for fallback
        self.original_pixmap = QPixmap("yeah.jpg")  # Replace with your image path
        self.setMinimumSize(10, 10)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.scaled_pixmap = None

    def update_image(self, image, annotations):
        for annotation in annotations:
            if annotation.primary_track:
                draw_tracked_object(image, annotation)
            else:
                draw_tracked_object(image, annotation, (0, 0, 255))
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


class GUI(QWidget):
    def __init__(self, outgoing_data: Queue, incoming_data: Queue):
        
        super().__init__()
        self.setWindowTitle("LEGOLAS GUI")

        # Data components
        self.update_thread = ReadIncomingMsgThread(incoming_data)
        self.update_thread.recieve_packet.connect(self.update_incoming_msg)
        self.incoming_data = incoming_data
        self.outgoing_data = outgoing_data
        self.update_thread.start()
        self.annotations_list = []

        self.font = QFont()
        self.font.setPointSize(20)  # Set text size to 20 points

         # === Top Bar (10% height) ===
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)

        def add_top_layout_label(text):
            label = QLabel(text)
            label.setFont(self.font)
            label.setAlignment(Qt.AlignCenter)
            top_layout.addWidget(label, alignment=Qt.AlignCenter)
            return label

        add_top_layout_label("Tracking Status:")
        self.track_status = add_top_layout_label("Not Tracking")
        add_top_layout_label("Recording Status:")
        self.recording_status = add_top_layout_label("OFF")

        # === Main Content ===
        main_content = QWidget()
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Left (70%): Image
        self.image_label = ImageLabel()
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.image_click_event.connect(self.update_internal_id)

        # Right (30%): Vertical labels
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)

        self.incoming_msg_label = QLabel("INCOMING MESSAGE LABEL")
        # self.incoming_msg_label.setText()

        self.general_msg_label = QLabel("general messages")
        # self.general_msg_label.setText("")

        # for i in range(4):
        #     right_layout.addWidget(QLabel(f"Right Label {i+1}")
        right_layout.addWidget(self.incoming_msg_label)
        right_layout.addWidget(self.general_msg_label)

        start_record_button = QPushButton("start record")
        start_record_button.clicked.connect(self.send_start_recording)
        stop_record_button = QPushButton("stop record")
        stop_record_button.clicked.connect(self.send_stop_recording)
        
        
        start_tracking_button = QPushButton("start tracking")
        start_tracking_button.clicked.connect(self.send_track_obj_msg)
        self.potential_current_id = -1
        stop_track_button = QPushButton("stop tracking", self)
        stop_track_button.clicked.connect(self.send_stop_track_msg)



        # self.button.clicked.connect(self.on_click)
        right_layout.addWidget(start_tracking_button)
        right_layout.addWidget(stop_track_button)

        def make_param_box(label: str, default_value: float):
            retlabel = QLabel(label)
            retbox = QDoubleSpinBox()
            retbox.setDecimals(4)
            retbox.setSingleStep(0.0001)
            retbox.setValue(default_value)
            right_layout.addWidget(retlabel)
            right_layout.addWidget(retbox)
            return retbox

        self.yaw_kp = make_param_box("Yaw k_p: ", 0.025)
        self.yaw_ki = make_param_box("Yaw k_i: ", 0.0002)
        self.pitch_kp = make_param_box("Pitch k_p: ", 0.025)
        self.pitch_ki = make_param_box("Pitch k_i: ", 0.0002)

        update_params_button = QPushButton("send params")
        update_params_button.clicked.connect(self.send_param_update)
        right_layout.addWidget(update_params_button)

        right_layout.addWidget(start_record_button)
        right_layout.addWidget(stop_record_button)



        right_layout.addStretch()

        main_layout.addWidget(self.image_label, 7)
        main_layout.addWidget(right_panel, 3)





        # layout = QHBoxLayout(self)
        # layout.addWidget(self.incoming_msg_label)
        # layout.addWidget(self.label_img)
        # layout.addWidget(self.button)

        # self.setLayout(layout)

        
        # === Full Layout ===
        full_layout = QVBoxLayout(self)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.addWidget(top_bar, 1)
        full_layout.addWidget(main_content, 9)

    # def on_click(self):
    #     print("send button pressed")
    #     self.outgoing_data.put(
    #         Packet(
    #             PacketType.CONTROL,
    #             BROADCAST_DEST,  # This doesn't actually matter
    #             {"hello": "server", "time": time.time()},
    #         )
    #     )
    def send_track_obj_msg(self):
        if self.potential_current_id < 0:
            self.general_msg_label.setText("nothing to update")
            return
        print("tracking obj id number", self.potential_current_id)
        self.track_status.setText(f"tracking obj {self.potential_current_id}")
        self.outgoing_data.put(Packet(PacketType.CONTROL, BROADCAST_DEST, {"trackID": self.potential_current_id}))
        self.potential_current_id = -1
    
    def send_stop_track_msg(self):
        self.track_status.setText("Not Tracking")
        self.outgoing_data.put(Packet(PacketType.CONTROL, BROADCAST_DEST, {"trackID": None}))

    def send_start_recording(self):
        self.recording_status.setText("ON")
        self.outgoing_data.put(Packet(PacketType.CONTROL, BROADCAST_DEST, {"record": True}))
    
    def send_stop_recording(self):
        self.recording_status.setText("OFF")
        self.outgoing_data.put(Packet(PacketType.CONTROL, BROADCAST_DEST, {"record": False}))


        
    @pyqtSlot(tuple)
    def update_internal_id(self, coords: tuple):
        for annotation in self.annotations_list:
            bb = annotation.bbox
            tl = bb.top_left
            br = bb.bottom_right
            if tl.x <= coords[0] and br.x >= coords[0]:
                if tl.y <= coords[1] and br.y >= coords[1]:
                    self.potential_current_id = annotation.persistent_id
                    self.general_msg_label.setText("updating internal id to " + str(self.potential_current_id))
                    return
                
                

    def send_param_update(self):
        self.outgoing_data.put(Packet(PacketType.CONTROL, BROADCAST_DEST, {"gimbalParams": 
                                                                           {"yaw": {"kp": self.yaw_kp.value(), "ki": self.yaw_ki.value()}, 
                                                                            "pitch": {"kp": self.pitch_kp.value(), "ki": self.pitch_ki.value()}}}))



    def change_img(self, msg: Packet):
        """Updates the image_label with a new opencv image"""
        payload_img = msg.payload
        # for annotation in self.annotations_list:
        #     draw_tracked_object(payload_img, annotation)
        # qt_img = convert_cv_qt(payload_img)
        # self.label_img.setPixmap(qt_img)
        self.image_label.update_image(payload_img, self.annotations_list)


    @pyqtSlot(Packet)
    def update_incoming_msg(self, msg: Packet):
        if msg.packet_type == PacketType.CONTROL and "frame_detections" in msg.payload:
            self.annotations_list = msg.payload["frame_detections"]
        if msg.packet_type == PacketType.IMAGE:
            self.change_img(msg)

    @staticmethod  # move this somewhere else where it makes more sense?
    def packet_to_str(msg: Packet) -> str:
        # print(f"From {msg.packet_address}: ", end="")
        # print("WERE TRYING TO CHANGE THE LABEL")
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
    client = SocketClient("127.0.0.1", 12345, global_outgoing_data, global_incoming_data)
    # client = SocketClient("10.0.0.3", 12345, global_outgoing_data, global_incoming_data)
    a = GUI(global_outgoing_data, global_incoming_data)
    a.show()
    client.run()
    app.exec()
    # what is Error receiving: [WinError 10038] An operation was attempted on something that is not a socket
    client.shutdown()
