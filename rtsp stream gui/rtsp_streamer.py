import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

from gi.repository import Gst, GstRtspServer, GObject

class WebcamRTSPServer(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        super(WebcamRTSPServer, self).__init__()
        self.set_shared(True)

    def do_create_element(self, url):
        pipeline_str = (
            "ksvideosrc ! videoconvert ! video/x-raw,width=640,height=480,framerate=30/1 ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! rtph264pay config-interval=1 name=pay0 pt=96"
        )
        return Gst.parse_launch(pipeline_str)

class RTSPServer:
    def __init__(self):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("8554")  # RTSP Port
        self.factory = WebcamRTSPServer()
        self.factory.set_shared(True)
        self.server.get_mount_points().add_factory("/webcam", self.factory)
        self.server.attach(None)

    def run(self):
        print("RTSP Stream available at rtsp://127.0.0.1:8554/webcam")
        GObject.MainLoop().run()

if __name__ == "__main__":
    Gst.init(None)
    server = RTSPServer()
    server.run()
