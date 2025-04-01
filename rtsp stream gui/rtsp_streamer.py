import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gst, GstRtspServer, GObject

# Initialize GStreamer
Gst.init(None)

# Create RTSP server
class RTSPServer:
    def __init__(self):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("8554")
        
        # Create a mount point
        self.mounts = self.server.get_mount_points()
        self.factory = GstRtspServer.RTSPMediaFactory()
        
        # Set up media pipeline for streaming
        self.factory.set_launch("v4l2src device=/dev/video0 ! videoconvert ! "
                                "video/x-raw,format=I420,width=640,height=480 ! "
                                "jpegenc ! rtpjpegpay ! rtspclientsink")
        
        # Attach the media to the server
        self.mounts.add_factory("/stream", self.factory)
        
    def start(self):
        self.server.attach(None)
        print("RTSP server is running at rtsp://<raspberry_pi_ip>:8554/stream")
        loop = GObject.MainLoop()
        loop.run()

# Start RTSP server
if __name__ == "__main__":
    server = RTSPServer()
    server.start()