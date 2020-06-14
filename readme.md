# Python video concation and motion detecttion

## Important constants:

- MAX_MOTION_TIME: how long to shoot a video when something is moving
- MAX_GLOBAL_MOTION_TIME: Stop even if we still detecting someting
- OBJ_SIZE_RATIO: Minimum size of object height to detect
- OUT_SIZE: resize output video. If defined then video with different resolution can be concatinated. Aspect ratio needs to be the same


## Example usage:
`./mdetect.py -i IN -o out.mp4`

