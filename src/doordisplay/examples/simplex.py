from framing.framers.animations.simplexmap import SimplexMap
from framing.frameplayer import FramePlayer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
from time import sleep

ZOOM_FACTOR = 10
SPEED = 3

BRIGHTNESS = 0.40
SIMULATE = True

# colors = ((0, 0, 155), (253, 231, 37), (224, 22, 22)) # Blue, Yellow, Red
# colors = ((13, 22, 135), (84, 31, 163), (139, 35, 165), (185, 50, 137), (219, 92, 104), (244, 136, 72), 
#           (254, 188, 42), (240, 249, 32)) # Plasma
# colors = ((13, 22, 135), (185, 50, 137), (240, 249, 32)) # Plasma
colors = ((155, 216, 255), (115, 132, 255), (153, 84, 255), (176, 37, 204), (219, 0, 152), (215, 73, 165), 
          (255, 148, 194), (255, 219, 241)) # Berry

simplexmap = SimplexMap(zoom_factor=ZOOM_FACTOR, temporal_speed=SPEED, color_map=colors)

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