# USB Camera Streaming with GStreamer and PyQt

Demonstrates how to stream a USB camera feed using **GStreamer** over **UDP** and display it in a PyQt GUI application. The sender captures video from a USB camera and transmits it over UDP, while the receiver fetches the stream and displays it in a PyQt-based GUI.

---

## 📜 Project Structure

```
.
├── sender.py   # Captures and streams video over UDP
├── receiver.py # Receives and displays video in a PyQt GUI
├── README.md   # Documentation
```

---

## How It Works

### **1.Sender (Streaming the Camera)**

- Captures video from the USB camera using `v4l2src`.
- Converts it to **I420 (YUV 4:2:0)** format.
- Encodes the frames as **JPEG**.
- Wraps the JPEG stream in **RTP (Real-time Transport Protocol)**.
- Sends the RTP stream over **UDP** to `127.0.0.1:5000`.

#### **Pipeline in **``

```sh
v4l2src device=/dev/video0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480 ! jpegenc ! rtpjpegpay ! udpsink host=127.0.0.1 port=5000
```

### **2. Receiver (Displaying the Stream in PyQt)**

- Listens for the **UDP stream** on port `5000`.
- Extracts RTP-encoded **JPEG** frames.
- Decodes the JPEG stream back into **raw video frames**.
- Converts to **BGR** format for OpenCV compatibility.
- Displays the video inside a **PyQt GUI**.

#### **Pipeline in **``

```sh
udpsrc port=5000 ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink emit-signals=True
```

---

## Installation

Ensure you have the required dependencies installed:

```sh
pip install PyQt5 opencv-python numpy pygobject
```

Ensure GStreamer is installed on your system:

```sh
# Ubuntu/Debian
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav

# macOS (using Homebrew)
brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav

# Windows
# Install from: https://gstreamer.freedesktop.org/download/
```

---

## 🎯 How to Run

### **1. Start the Sender** (Stream the USB camera):

```sh
python sender.py
```

### **2. Start the Receiver** (View the stream in GUI):

```sh
python receiver.py
```

---

## Key Features

**Real-time USB Camera Streaming** using GStreamer.\
**UDP Transmission** for fast data transfer.\
**PyQt GUI** to display the video stream.\
**RTP-based Compression** using JPEG encoding.

---

## Note

**1.** If two receivers are there for single stream then it may not be able to serve for multiple receivers, better to use correct pipeline (receiving format) with single receiver for this method atleast.  
**2.** Also we can change the video encoding format for low latency but video quality will be the cost.


## Future Improvements

- Support for **multiple clients** (broadcast streaming).
- Add a **recording feature** to save the stream.
- Reduce latency using **H.264 encoding**.

---

🎉 Happy Streaming! 🚀

