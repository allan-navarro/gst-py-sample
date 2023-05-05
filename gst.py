import sys
import ctypes
import threading
from datetime import datetime
import time

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

end=False
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


def flip(conv):
    global end
    flip_method = False
    while not end:
        conv.set_property('flip-method', int(flip_method))
        flip_method = not flip_method
        
        time.sleep(1)



def main(args):
    global end
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file>\n" % args[0])
        sys.exit(1)

    file = args[1]

    GObject.threads_init()
    Gst.init(None)

    pipeline_str = f'filesrc location={file}  ! queue ! qtdemux ! ' \
        ' h264parse ! nvv4l2decoder ! nvvidconv name=conv ! nvoverlaysink ' \
        ' sync=false enable-last-sample=false'

    pipeline = Gst.parse_launch(pipeline_str)
    if not pipeline:
        sys.stderr.write('could not create pipeline\n')
        sys.exit(1)

    h264parse = pipeline.get_by_name("h264parse0")

    if not h264parse:
        sys.stderr.write('could not get h264parse from pipeline\n')
        sys.exit(1)

    nvvidconv = pipeline.get_by_name("conv")
    if not nvvidconv:
        sys.stderr.write('could not get nvvidconv from pipeline\n')
        sys.exit(1)

    t = threading.Timer(0, flip, [nvvidconv])
    t.start()

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
    end = True

    # cleanup
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
