from frames.frameplayer import FramePlayer
from frames.framers.staticframer import StaticFramer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
from pathlib import Path


BRIGHTNESS = 0.50
scale_image = True
SIMULATE = True

# img = "BarTest.png"
# img = "Clicky.png"
# img = "ClickyWhite.png"
# img = "Hamilton.png"
# img = "TestImage.png"
# img = "Color.jpg"
# img = "talltest.png"
# img = "sports.png"
img = "FireTest.png"
# img = "Cats.png"
# img = "DavidDog.png"
# img = "sports1.jpg"
# img = "sports2.png"

# Get the path to the data/ folder
data_folder = Path(__file__).parent / "data"
img_path = data_folder / img

# Create the framer
framer = StaticFramer(img_path, auto_scale=scale_image)

if SIMULATE:
    sim_frame(framer)
else:
    # Create the frame player
    led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
    player = FramePlayer(led_matrix, framer)

    # Play the frames
    player.play()