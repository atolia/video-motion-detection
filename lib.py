import time
import sys
import argparse


def eprint(*args, **kwargs):
    print(time.strftime('I%m%d %H:%M:%S%z', time.localtime()),
          *args, file=sys.stderr, **kwargs)
    sys.stderr.flush()


def parseArgs():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", type=str,
                    # help="path to dir with input video files. All videos need to have same aspect ratio " +
                    help="path to dir with input video files. All videos need to have same resolution " +
                    "Or '0' for capture video from camera device 0, '1' for dev 1 etc...")
    ap.add_argument("-o", "--output", type=str,
                    help="path to output video file. ie out.avi for AVI, .mp4, .mkv etc. " +
                    "In case of codec errors try to change OUTPUT_CODEC")
    # return vars(ap.parse_args())
    if len(sys.argv) < 2:
        ap.print_help(sys.stderr)
        sys.exit(1)
    return ap.parse_args()


def safe_cast(val, to_type, base=10, default=None):
    try:
        return to_type(val, base)
    except (ValueError, TypeError):
        return default
