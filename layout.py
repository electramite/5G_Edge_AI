import sys
import subprocess
import socket
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QButtonGroup, 
    QComboBox, QFileDialog, QSpinBox, QDoubleSpinBox, QTextEdit, QHBoxLayout, QFrame, QRadioButton, QMessageBox, QSizePolicy
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QColor, QFont
import numpy as np
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import time 
import psutil
import shutil
import os 

def get_hef_files(directory):
    """Retrieve HEF files from the specified directory."""
    if os.path.exists(directory):
        return [f for f in os.listdir(directory) if f.endswith(".hef")]
    return []

def get_available_cameras():
    """Detect available camera devices using v4l2."""
    try:
        result = subprocess.run(["ls /dev/video*"], capture_output=True, text=True, shell=True)
        available_cameras = result.stdout.strip().split("\n")
        return available_cameras if available_cameras and available_cameras[0] else ["No Camera Found"]
    except Exception:
        return ["No Camera Found"]

class SocketThread(QThread):
    data_received = pyqtSignal(str)

    def run(self):
        """Continuously listen for incoming connections and handle data."""
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow socket reuse
                server_socket.bind(('0.0.0.0', 57344))
                server_socket.listen(1)

                print("Waiting for connection...")
                connection, client_address = server_socket.accept()
                print(f"Connected to {client_address}")

                while True:
                    data = connection.recv(1024)
                    if not data:
                        print("Client disconnected. Waiting for new connection...")
                        break  # Break out of the inner loop and wait for a new connection

                    try:
                        json_data = json.loads(data.decode('utf-8'))
                        formatted_data = self.format_json(json_data)
                        self.data_received.emit(formatted_data)
                    except json.JSONDecodeError:
                        self.data_received.emit("Failed to decode JSON data.")

                connection.close()  # Ensure the socket is closed before looping again

            except Exception as e:
                print(f"Socket error: {e}")
                server_socket.close()  # Ensure the socket is properly closed before retrying

    def format_json(self, json_data):
        """Format JSON data to a readable dictionary."""
        if isinstance(json_data, list) and len(json_data) > 0:
            json_data = json_data[0]  # Extract first object if it's a list
        formatted_dict = {
            "boxex": json_data.get("boxex", []),
            "confidence": json_data.get("confidence", 0.0),
            "label": json_data.get("label", "unknown")
        }
        return str(formatted_dict)

class DetectionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.startSocketThread()
        self.initGStreamer()

        self.process = None
        self.last_frame_time = None
        self.fps_counter = 0
        self.total_fps = 0.0
        self.metadata_history_len = 20
        self.metadata_history = []

    def initUI(self):
        main_layout = QHBoxLayout()
        control_layout = QVBoxLayout()

        # Inference Mode Dropdown
        self.infer_label = QLabel("Inference Mode:")
        self.infer_combo = QComboBox()
        self.infer_combo.addItems(["detection", "Segmentation", "PoseEstimation"])
        self.infer_combo.currentTextChanged.connect(self.update_hef_dropdown)
        self.infer_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.infer_combo.setMaximumWidth(180) 
        control_layout.addWidget(self.infer_label)
        control_layout.addWidget(self.infer_combo)
        
        # HEF Path Dropdown
        self.hef_label = QLabel("HEF Path:")
        self.hef_dropdown = QComboBox()
        self.hef_dropdown.addItem("Upload Model")
        self.hef_dropdown.activated.connect(self.handle_hef_selection)
        self.hef_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hef_dropdown.setMaximumWidth(180) 
        control_layout.addWidget(self.hef_label)
        control_layout.addWidget(self.hef_dropdown)
        self.update_hef_dropdown()

        # Input Source Selection
        self.input_label = QLabel("Input Source:")
        control_layout.addWidget(self.input_label)

        self.camera_radio = QRadioButton("Camera")
        self.rtsp_radio = QRadioButton("RTSP")
        self.camera_radio.setChecked(True)
        self.camera_radio.toggled.connect(self.update_input_options)
        self.rtsp_radio.toggled.connect(self.update_input_options)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.camera_radio)
        radio_layout.addWidget(self.rtsp_radio)
        control_layout.addLayout(radio_layout)

        self.input_dropdown = QComboBox()
        self.input_dropdown.addItems(get_available_cameras())
        self.input_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_dropdown.setMaximumWidth(180) 
        control_layout.addWidget(self.input_dropdown)

        self.rtsp_input = QLineEdit()
        self.rtsp_input.setPlaceholderText("Enter RTSP URL")
        self.rtsp_input.setVisible(False)
        self.rtsp_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rtsp_input.setMaximumWidth(180) 
        control_layout.addWidget(self.rtsp_input)

        # IOU Threshold
        self.iou_label = QLabel("IOU Threshold:")
        self.iou_input = QDoubleSpinBox()
        self.iou_input.setRange(0.0, 1.0)
        self.iou_input.setSingleStep(0.1)
        self.iou_input.setValue(0.1)
        control_layout.addWidget(self.iou_label)
        control_layout.addWidget(self.iou_input)
        self.iou_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.iou_input.setMaximumWidth(180) 

        # Confidence Threshold
        self.conf_label = QLabel("Confidence Threshold:")
        self.conf_input = QDoubleSpinBox()
        self.conf_input.setRange(0.0, 1.0)
        self.conf_input.setSingleStep(0.1)
        self.conf_input.setValue(0.2)
        control_layout.addWidget(self.conf_label)
        control_layout.addWidget(self.conf_input)
        self.conf_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.conf_input.setMaximumWidth(180) 

        self.fps_label = QLabel("Avg FPS: 0")
        # self.fps_label.setStyleSheet("font-size: 10px;")
        layout = QVBoxLayout()
        control_layout.addWidget(self.fps_label)

        # Horizontal layout for "Save JSON?" section
        save_json_layout = QHBoxLayout()
        self.radio_label = QLabel("Save JSON:")
        save_json_layout.addWidget(self.radio_label)
        self.radio_yes = QRadioButton("Yes")
        self.radio_no = QRadioButton("No")
        self.radio_no.setChecked(True)  # Default to "No"
        save_json_layout.addWidget(self.radio_yes)
        save_json_layout.addWidget(self.radio_no)

        self.save_json_group = QButtonGroup(self)
        self.save_json_group.addButton(self.radio_yes)
        self.save_json_group.addButton(self.radio_no)

        control_layout.addLayout(save_json_layout)
        self.radio_yes.toggled.connect(self.toggle_json_path)

        # JSON Path Input
        self.json_path_label = QLabel("JSON Path:")
        control_layout.addWidget(self.json_path_label)
        self.json_path_input = QLineEdit(self)
        self.json_path_input.setPlaceholderText("Enter JSON path...")
        self.json_path_input.setEnabled(False)  # Initially disabled
        self.json_path_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.json_path_input.setMaximumWidth(180) 
        control_layout.addWidget(self.json_path_input)


        # JSON Frame Interval
        self.json_label = QLabel("JSON Frame Interval:")
        self.json_input = QSpinBox()
        self.json_input.setRange(1000, 10000)
        self.json_input.setValue(1000)
        self.json_input.setEnabled(False)
        
        control_layout.addWidget(self.json_label)
        control_layout.addWidget(self.json_input)
        self.json_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.json_input.setMaximumWidth(180) 

        # Launch Button
        self.launch_button = QPushButton("Run")
        self.launch_button.clicked.connect(self.runDetection)
        control_layout.addWidget(self.launch_button)
        self.launch_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.launch_button.setMaximumWidth(180)

        # stop button 
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stopDetection)
        control_layout.addWidget(self.stop_button)
        self.stop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop_button.setMaximumWidth(180)


        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: grey; border: 3px solid black;")

        # Allow QLabel to expand
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Refresh every 30ms

        self.video_widget = QVideoWidget(self.video_label)

        # # Make QVideoWidget resize dynamically
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)

        video_layout.addWidget(self.video_label)
        main_layout.addLayout(video_layout)

        #################################################

        self.metadata_label = QLabel("Model Metadata:")
        self.metadata_display = QTextEdit()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setFixedHeight(150)  
        self.metadata_display.setStyleSheet("background-color: black; color: orange; font-family: monospace;")
        self.metadata_display.setFont(QFont("Courier", 10))

        video_layout.addWidget(self.metadata_label)  
        video_layout.addWidget(self.metadata_display) 

        main_layout.addLayout(video_layout) 
        main_layout.addLayout(control_layout) 
        
        self.setLayout(main_layout)
        self.setWindowTitle("Detection Launcher")
        
        # Set Color Theme
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

    def toggle_json_path(self):
        json_status = self.radio_yes.isChecked()
        self.json_path_input.setEnabled(json_status)
        self.json_input.setEnabled(json_status)

#######################################################################
    def browseHef(self):
        hef_path, _ = QFileDialog.getOpenFileName(self, "Select HEF File", "", "HEF Files (*.hef);;All Files (*)")
        if hef_path:
            self.hef_input.setText(hef_path)

    def update_hef_dropdown(self):
        infer_mode = self.infer_combo.currentText()
        directory_map = {
            "detection": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/Detection",
            "Segmentation": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/Segmentation",
            "PoseEstimation": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/PoseEstimation"
        }
        directory = directory_map.get(infer_mode, "")
        hef_files = get_hef_files(directory)
        self.hef_dropdown.clear()
        self.hef_dropdown.addItems(hef_files if hef_files else ["No HEF files found"])
        self.hef_dropdown.addItem("Upload Model")

    def handle_hef_selection(self, index):
        if self.hef_dropdown.itemText(index) == "Upload Model":
            self.upload_model()

    def upload_model(self):
        if not self.fetch_target_dir_path():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Model File", "", "HEF Files (*.hef)")
        target_directory = self.fetch_target_dir_path()
        if file_path and file_path.endswith(".hef"):
            try:
                shutil.copy(file_path, target_directory)
                self.update_hef_dropdown()
            except Exception as e:
                print("Error uploading file:", e)

    def update_input_options(self):
        if self.camera_radio.isChecked():
            self.input_dropdown.setVisible(True)
            self.rtsp_input.setVisible(False)
            self.input_dropdown.clear()
            self.input_dropdown.addItems(get_available_cameras())
        else:
            self.input_dropdown.setVisible(False)
            self.rtsp_input.setVisible(True)
#############################################################################
    def toggleInputField(self):
        selected_source = self.input_combo.currentText()
        if selected_source == "/dev/video0":
            self.rtsp_input.setText("/dev/video0")
        else:
            self.rtsp_input.clear()

    def fetch_target_dir_path(self):
        infer_mode = self.infer_combo.currentText()
        directory_map = {
            "detection": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/Detection/",
            "Segmentation": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/Segmentation/",
            "PoseEstimation": "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/Models/PoseEstimation/"
        }
        target_directory = directory_map.get(infer_mode, "")
        return target_directory

    def runDetection(self):
        # warning if no HEF is selected 
        if self.hef_dropdown.currentText() == "Upload Model":
            QMessageBox.critical(self, "Error", "No valid HEF file selected! Please select a HEF file.")
            return False
        hef_path = self.fetch_target_dir_path() + self.hef_dropdown.currentText()
        rtsp_url = self.rtsp_input.text() if self.rtsp_radio.isChecked() else self.input_dropdown.currentText()
        # warning if no RTSP url 
        if len(rtsp_url) == 0:
            QMessageBox.critical(self, "Error", "Please enter the RTSP URL.")
            return False  
        # Warning for JSON path
        if self.radio_yes.isChecked():
            json_path = self.json_path_input.text()
            if len(json_path) == 0:
                QMessageBox.critical(self, "Error", "Please enter JSON path")
                return False


        if self.radio_yes.isChecked():
            json_frame = self.json_input.value()  
        else:
            json_frame = 0
        print(f"JSON frame {json_frame}")        
        iou = self.iou_input.value()
        conf = self.conf_input.value()
        infer_type = self.infer_combo.currentText()
        

        command = [
            "python", "/home/mantiswave/shashwat/hailo-rpi5-examples/basic_pipelines/new_pipe/np_detection_test.py",
            "--hef-path", hef_path,
            "--input", rtsp_url,
            # "--iou", str(iou),
            # "--conf", str(conf),
            "--infer", infer_type,
            "--jsonframe", str(json_frame)
        ]
        self.process = subprocess.Popen(command)
        print(command)
        # Start GStreamer-based RTSP playback
        self.startStream(rtsp_url)

    def stopDetection(self):
        """Terminate the running script."""
        if self.process:
            self.process.terminate()  # Send SIGTERM
            self.process.wait()  # Wait for the process to exit
            self.process = None
        #     self.status_label.setText("Status: Stopped")
        # else:
        #     self.status_label.setText("Status: No Process Running")
    
    def startStream(self, rtsp_url):
        media = QMediaContent(QUrl(rtsp_url))
        self.player.setMedia(media)
        self.player.play()
    
    def startSocketThread(self):
        self.socket_thread = SocketThread()
        self.socket_thread.data_received.connect(self.updateMetadata)
        self.socket_thread.start()
    
    def updateMetadata(self, data):
        self.metadata_history.append(data)
        if len(self.metadata_history) > self.metadata_history_len:
            self.metadata_history.pop(0)

        self.metadata_display.setText("\n".join(self.metadata_history))

        # self.metadata_display.setText(data)

    def initGStreamer(self):
        """Initialize the GStreamer pipeline to receive UDP video."""
        Gst.init(None)
        ## Pipeline with low resolution
        # pipeline_str = (
        #     "udpsrc port=5000 caps=\"application/x-rtp,encoding-name=H264,payload=96\" ! "
        #     "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! "
        #     "appsink name=sink emit-signals=true"
        # )

        pipeline_str = (
            "udpsrc port=5000 ! application/x-rtp,encoding-name=JPEG,payload=26\""
            " ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink emit-signals=True"
        )

        self.pipeline = Gst.parse_launch("udpsrc port=5000 ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink emit-signals=True")
        self.appsink = self.pipeline.get_by_name("sink")

        if not self.appsink:
            print("Error: appsink element not found in pipeline")
            return

        self.appsink.set_property("emit-signals", True)
        self.appsink.connect("new-sample", self.on_new_sample)
        # self.appsink.connect("fps-measurements", self.on_fps_measurement)

        # Start GStreamer pipeline
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Error: Could not start GStreamer pipeline.")

    def on_new_sample(self, sink):
        """Callback function to retrieve frames from appsink."""
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            width = caps.get_structure(0).get_int("width")[1]
            height = caps.get_structure(0).get_int("height")[1]
            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                frame = np.frombuffer(map_info.data, np.uint8).reshape((height, width, 3))
                self.display_frame(frame)
                buf.unmap(map_info)

            current_time = time.time()
            if self.last_frame_time:
                delta = current_time - self.last_frame_time
                if delta > 0:
                    fps = 1 / delta
                    self.total_fps += fps
                    self.fps_counter += 1
                    avg_fps = self.total_fps / self.fps_counter
                    # print(f"Instant FPS: {fps:.2f} | Avg FPS: {avg_fps:.2f}")
                    self.fps_label.setText(f"Avg FPS: {avg_fps:.2f}")
            self.last_frame_time = current_time

        return Gst.FlowReturn.OK

    def display_frame(self, frame):
        """Convert OpenCV frame to PyQt format and display it."""
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)

        # Scale image to fit 480x480
        label_width = self.video_label.width()
        label_height = self.video_label.height()
        if label_width > 1080 or label_height > 720:  # Adjust limits as per your UI
            label_width = 1080
            label_height = 720
        print(f"{label_height} {label_width}")
        scaled_img = q_img.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(QPixmap.fromImage(scaled_img))

    def update_frame(self):
        """Force repaint the QLabel to refresh the video display."""
        self.video_label.repaint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DetectionApp()
    window.show()
    sys.exit(app.exec_())

