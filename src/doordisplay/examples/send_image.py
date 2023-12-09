from frames.frameplayer import FramePlayer
from frames.framers.staticframer import StaticFramer

from pathlib import Path


BRIGHTNESS = 0.50
scale_image = True

img = "BarTest.png"
# img = "Clicky.png"
# img = "ClickyWhite.png"
# img = "Hamilton.png"
# img = "TestImage.png"
# img = "Color.jpg"
# img = "talltest.png"
# img = "sports.png"
# img = "FireTest.png"
# img = "Cats.png"
# img = "DavidDog.png"

# Get the path to the data/ folder
data_folder = Path(__file__).parent / "data"
img_path = data_folder / img

# Create the framer
framer = StaticFramer(img_path, auto_scale=scale_image)

# Create the frame player
player = FramePlayer(framer, brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)

# Play the frames
player.play()