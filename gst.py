import sys
import ctypes
from datetime import timedelta
from datetime import datetime

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True


def overlay_sink_probe_cb(pad: Gst.Pad, info: Gst.PadProbeInfo, data) -> Gst.PadProbeReturn:


    str = datetime.now().isoformat(timespec='microseconds')

    data.set_property('text', str)

    return Gst.PadProbeReturn.OK


def main(args):
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file>\n" % args[0])
        sys.exit(1)

    file = args[1]

    GObject.threads_init()
    Gst.init(None)

    pipeline_str = f'filesrc location={file}  ! queue ! qtdemux ! video/x-h264 ! ' + \
        ' h264parse ! avdec_h264 ! textoverlay name=textoverlay0 ! videoconvert ! xvimagesink'

    pipeline = Gst.parse_launch(pipeline_str)
    if not pipeline:
        sys.stderr.write('could not create pipeline\n')
        sys.exit(1)

    h264parse = pipeline.get_by_name("h264parse0")

    if not h264parse:
        sys.stderr.write('could not get h264parse from pipeline\n')
        sys.exit(1)

    textoverlay = pipeline.get_by_name("textoverlay0")
    if not textoverlay:
        sys.stderr.write('could not get textoverlay from pipeline\n')
        sys.exit(1)

    video_sink_pad_overlay = h264parse.get_static_pad('sink')
    probe_sink_overlay_id = video_sink_pad_overlay.add_probe(
        Gst.PadProbeType.BUFFER, overlay_sink_probe_cb, textoverlay)

    # create and event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
