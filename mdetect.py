#!/usr/bin/env python3

import cv2
import time
import sys
import os
import signal
import glob
from imutils.video import FPS
import imutils
from lib import *

# how long to shoot a video when something is moving
MAX_MOTION_TIME = 3  # sec

# Stop even if we still detecting someting. Need this in case background was
# chagned and we can fall into infinite loop.
MAX_GLOBAL_MOTION_TIME = 9  # sec

SLEEP_SECONDS = 0  # sec. float. to reduce CPU. can be 0
OUT_FPS = 30  # fps setting for video output. for Pi will be ~30 if SLEEP == 0
DRAW_RECTS = True  # mark all movments on video with green rectangles
DEBUG = False  # print lots of debug info
# OUTPUT_CODEC = "MJPG"
# OUTPUT_CODEC = "XVID"
OUTPUT_CODEC = "H264"

OUT_SIZE = None  # default no resise
# OUT_SIZE = 500  # resize output frames for concatinating videos with different resolution 
# # (still need to be same aspect ratio)

# Minimum size of object height to detect. to reduce noice
OBJ_SIZE_RATIO = 10  # like 1/5 of frame


def signal_handler(sig, frame):
    eprint('Program finished')
    fps.stop()
    eprint("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    eprint("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    video.release()
    # Destroying all the windows
    writer.release()
    cv2.destroyAllWindows()
    sys.exit(0)

args = parseArgs()
OUT = args.output
signal.signal(signal.SIGINT, signal_handler)

if type(safe_cast(args.input, int)) == int:
    eprint('Capturing video')
    IN = [args.input]
    time.sleep(2)
else:
    IN = []
    INDEX = 0
    for f in glob.glob(os.path.join(args.input, "*.[ma][kvop][vi4]")):
        if os.path.isfile(f):
            IN.append(f)
    eprint(f'processing video files {IN}')

video = cv2.VideoCapture(IN[INDEX])

# Initializing motion = 0 (no motion)
motion = 0
startMotionTime = 0
FRAME_NUM = 0

writer = None
# Assigning our static_back to None
static_back = None
MINIMUM_CONTOUR_AREA = None
# Infinite while loop to treat stack of image as video
# for _ in range(100):
while True:
    # Reading frame(image) from video
    check, frame = video.read()
    if not MINIMUM_CONTOUR_AREA:
        (H, W) = frame.shape[:2]
        MINIMUM_CONTOUR_AREA = (H // OBJ_SIZE_RATIO) ** 2  
        eprint(f"[INFO] frame size area: {W}, {H}")
        eprint(f"[INFO] Detecting obj area: {MINIMUM_CONTOUR_AREA}")

    # if we are viewing a video and we did not grab a frame then we
    # have reached the end of the video. Restart it for debug
    if frame is None:
        fps.stop()
        eprint("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
        eprint("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

        if INDEX < len(IN) - 1:
            INDEX += 1
            video = cv2.VideoCapture(IN[INDEX])
        else:
            break

        static_back = None
        fps = FPS().start()
        FRAME_NUM = 0
        eprint(f"[INFO] opening next video file {IN[INDEX]}")
        check, frame = video.read()

    if OUT_SIZE:
        gray = imutils.resize(frame, width=OUT_SIZE)

    # Converting color image to gray_scale image
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Converting gray scale image to GaussianBlur
    # so that change can be find easily
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    # In first iteration we assign the value
    # of static_back to our first frame
    if static_back is None:
        static_back = gray
        eprint(f'New motion detected. Frame N {FRAME_NUM}')
        continue

    # Difference between static background
    # and current frame(which is GaussianBlur)
    diff_frame = cv2.absdiff(static_back, gray)
    # If change in between static background and
    # current frame is greater than 30 it will show white color(255)
    thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
    thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
    # Finding contour of moving object
    # (_, cnts, _) = cv2.findContours(thresh_frame,   # for opencv-3
    (cnts, _) = cv2.findContours(thresh_frame,  # for opencv-4
                                 cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detect = 0
    for contour in cnts:
        if cv2.contourArea(contour) < MINIMUM_CONTOUR_AREA:
            continue
        else:
            detect += 1
            if DRAW_RECTS:
                # making green rectangle arround the moving object
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

    if detect > 0:
        # motion start
        if not motion:
            print('New Motion started!, detect=', detect) if DEBUG else None
            startMotionTime = time.monotonic()
            fps = FPS().start()
        # motion was alread started
        else:
            print('Already. ', end='') if DEBUG else None
        motion = 1
    else:
        if motion:
            print('Stopped? ', end='') if DEBUG else None
            if time.monotonic() - startMotionTime > MAX_MOTION_TIME:
                motion = 0
                eprint('Motion timeout Inside stopped mode! stop shoting.') if DEBUG else None
                static_back = None

                fps.stop()
                eprint("[INFO] approx. FPS: {:.2f}".format(fps.fps())) if DEBUG else None

    if motion:
        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*OUTPUT_CODEC)
            (H, W) = frame.shape[:2]
            writer = cv2.VideoWriter(OUT, fourcc, OUT_FPS,  (W, H), True)

        writer.write(frame)
        fps.update()
        FRAME_NUM += 1
        print('Shooting ', end='') if DEBUG else None
        # max  sec to allow motion
        if time.monotonic() - startMotionTime > MAX_GLOBAL_MOTION_TIME:
            motion = 0
            print('Global Motion timout! stop shoting.') if DEBUG else None
            fps.stop()
            eprint("[INFO] approx. FPS: {:.2f}".format(fps.fps())) if DEBUG else None
            static_back = None

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)

signal_handler(0, 0)
