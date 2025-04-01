
# RTSP Server on Raspberry Pi/Linux (for video transmission)

This guide demonstrates how to set up an RTSP (Real-Time Streaming Protocol) server on a Raspberry Pi to stream video from a USB webcam using GStreamer. The RTSP stream can be accessed on another device (like another Raspberry Pi or computer) to view the live video feed.

## Requirements

- Raspberry Pi (Raspberry Pi 1 for the RTSP server and Raspberry Pi 2 or another device to access the stream)
- USB webcam
- GStreamer installed on Raspberry Pi

## Prerequisites

Before setting up the RTSP server, you need to install the necessary dependencies on Raspberry Pi. You can do this using the following commands:

```bash
sudo apt update
sudo apt install gstreamer1.0-tools gstreamer1.0-rtsp gstreamer1.0-plugins-good
```

## Steps

### 1. RTSP Server Setup on Raspberry Pi

Run the script on the Raspberry Pi to start the RTSP server:

```bash
python3 rtsp_streamer.py
```

The RTSP server will start running and can be accessed via `rtsp://<raspberry_pi_ip>:8554/stream`.

### 2. Access the Stream on Another Device

To access the video stream on another device, you can use an RTSP player such as VLC or GStreamer.

#### Using VLC:
Open VLC and click `Media -> Open Network Stream`, then enter:

```
rtsp://<raspberry_pi_ip>:8554/stream
```

#### Using GStreamer:
You can also use GStreamer to receive and display the stream. Run the following command on another device:

```bash
gst-launch-1.0 rtspsrc location=rtsp://<raspberry_pi_ip>:8554/stream ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
```

### Conclusion

You have successfully set up an RTSP server on your Raspberry Pi to stream video from a USB webcam. The video stream can be accessed from another device using RTSP players like VLC or GStreamer.
