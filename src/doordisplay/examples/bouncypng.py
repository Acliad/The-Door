from framing.framers.animations.animbouncypng import AnimBouncyPNG
from framing import FramePlayer
from ledmat.ledsim import sim_frame
from ledmat import LEDMatrix
from pathlib import Path

SIMULATE = False
scale_image =  False
BRIGHTNESS = 0.6

img = "logo_test.png"

data_folder = Path(__file__).parent / "data"
img_path = data_folder / img

bouncypng = AnimBouncyPNG(img_path, auto_scale=scale_image)
                           
if SIMULATE:
    sim_frame(bouncypng)
else:
    try:
        led_matrix = LEDMatrix(brightness=BRIGHTNESS)
        player = FramePlayer(led_matrix, bouncypng)
        player.play_blocking()
    except KeyboardInterrupt:
        print("Exiting...")