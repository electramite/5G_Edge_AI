import sys
import gi
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap

gi.require_version('Gst', '1.0')
from gi.repository import Gst

class GstViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        Gst.init(None)
        self.initGstPipeline()

    def initUI(self):
        self.setWindowTitle("USB Camera Stream Viewer")
        self.setGeometry(100, 100, 640, 480)
        
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        
        self.stream_button = QPushButton("Start Stream", self)
        self.stream_button.clicked.connect(self.start_stream)
        
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.stream_button)
        self.setLayout(layout)

    def initGstPipeline(self):
        self.pipeline = Gst.parse_launch(
            "udpsrc port=5000 ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink emit-signals=True"
        )
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.connect("new-sample", self.on_new_sample)

    def start_stream(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            width = caps.get_structure(0).get_int("width")[1]
            height = caps.get_structure(0).get_int("height")[1]
            
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 3))
                buffer.unmap(map_info)
                self.display_frame(frame)
        return Gst.FlowReturn.OK

    def display_frame(self, frame):
        image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        self.pipeline.set_state(Gst.State.NULL)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GstViewer()
    window.show()
    sys.exit(app.exec_())
