import gi
import sys

gi.require_version('Gst', '1.0')
from gi.repository import Gst

def launch_camera():
    Gst.init(None)
    pipeline = Gst.parse_launch(
        "v4l2src device=/dev/video0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480 ! jpegenc ! rtpjpegpay ! udpsink host=127.0.0.1 port=5000"
    )
    pipeline.set_state(Gst.State.PLAYING)
    
    try:
        bus = pipeline.get_bus()
        msg = None
        while True:
            msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                break
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.set_state(Gst.State.NULL)
        print("Camera stream stopped.")

if __name__ == "__main__":
    launch_camera()