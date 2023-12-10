from frames.frameplayer import FramePlayer
from frames.framers.gifframer import GifFramer
from ledmat import LEDMatrix

from pathlib import Path

BRIGHTNESS = 0.4
scale_image = True
# gif = "simpsons.gif"
# gif = "simpsonsback.gif"
# gif = "vinnie.gif"
# gif = "color.gif"
# gif = "garmindoor_sized.gif"
# gif = "clickyscream.gif"
# gif = "clickyfloat.gif"
gif = "coffee.gif"

# Get the path to the data/ folder
data_folder = Path(__file__).parent / "data"
gif_path = data_folder / gif

# Create the framer
framer = GifFramer(gif_path, framerate=15, auto_scale=scale_image, loop_mode=GifFramer.LoopMode.LOOP)

# Create the frame player
led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.0)
player = FramePlayer(led_matrix, framer)

try:
    # Play the frames
    player.play()
except KeyboardInterrupt:
    player.stop()
    print("Keyboard interrupt")
