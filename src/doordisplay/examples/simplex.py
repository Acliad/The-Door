from framing.framers.animations.simplexmap import SimplexMap
from framing.frameplayer import FramePlayer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
from time import sleep

ZOOM_FACTOR = 10
SPEED = 1

BRIGHTNESS = 0.40
SIMULATE = True

COLORS = ((255, 0, 0), (245, 245, 66), (0, 0, 255))

simplexmap = SimplexMap(zoom_factor=ZOOM_FACTOR, speed=SPEED, color_map=COLORS)

if SIMULATE:
    sim_frame(simplexmap)
else:
    try:
        led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
        player = FramePlayer(led_matrix, simplexmap)
        player.play_blocking()
    except KeyboardInterrupt:
        player.stop()
        print("Keyboard interrupt")
        exit()