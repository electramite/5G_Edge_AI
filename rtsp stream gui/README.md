# GStreamer RTSP Webcam Streaming (Windows to Linux or Raspberry Pi)

## Overview
This guide explains how to stream a webcam over RTSP using **GStreamer** on Windows and receive the stream on a **Raspberry Pi**.

---
## Installation
### 1. Install GStreamer on Windows
1. Download GStreamer from [GStreamer Official Site](https://gstreamer.freedesktop.org/download/)
2. Install the **MSVC Runtime** version (Full Installation)
3. Add the GStreamer `bin` path to your **System Environment Variables**:
   ```
   C:\gstreamer\1.0\msvc_x86_64\bin
   ```

### 2. Install PyGObject (gi) on Windows
GStreamer requires **PyGObject** for Python support.

#### **Step 1: Install Dependencies**
1. Install **MSYS2** from [https://www.msys2.org/](https://www.msys2.org/)
2. Open **MSYS2 MinGW 64-bit** terminal and run:
   ```sh
   pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python-gobject
   ```
3. Close MSYS2.

#### **Step 2: Install Python Modules**
Run these commands in **Command Prompt (cmd)**:
```sh
pip install pycairo
pip install PyGObject
```

### Install GStreamer on Raspberry Pi
On your **Raspberry Pi**, install GStreamer with:
```sh
sudo apt update && sudo apt install -y gstreamer1.0-tools gstreamer1.0-rtsp gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
```

---
## Start RTSP Streaming (Windows)

Run the script:
```sh
python rtsp_server.py
```

---
## Access RTSP Stream on Raspberry Pi
To receive and view the stream, run this command on your **Raspberry Pi**:
```sh
gst-launch-1.0 -v rtspsrc location=rtsp://<WINDOWS_IP>:8554 ! decodebin ! autovideosink
```
Replace `<WINDOWS_IP>` with the actual **Windows machine's IP address**.

---
## Troubleshooting
1. **ModuleNotFoundError: No module named 'gi'**
   - Ensure **PyGObject** is installed correctly. Reinstall using:
     ```sh
     pip install pycairo
     pip install PyGObject
     ```

2. **RTSP Stream Not Playing on Raspberry Pi**
   - Ensure **GStreamer** is installed (`gstreamer1.0-tools` package)
   - Check Windows Firewall settings (allow UDP on port **8554**)
   - Verify **Windows IP address** is correct

---
## Summary
**Windows** streams webcam using **GStreamer RTSP**  
**Raspberry Pi** receives the stream via **GStreamer RTSP Source**

Enjoy real-time streaming! 🚀

