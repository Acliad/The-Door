from framing.frameplayer import FramePlayer
from framing.framers.slideshowframer import SlideshowFramer
from framing.framers.slideshowframer import TransitionType
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
from pathlib import Path

BRIGHTNESS = 0.50
SCALE_IMAGE = True
SIMULATE = True
CONTRAST = 1.0
GAMMA = 2.2

display_duration = 2  # Duration (in seconds) for each image
shuffle = True
transition_type = TransitionType.RANDOM
transition_duration = 1 # in seconds

# List of image paths for the slideshow
# Path to the data/Slideshow folder
slideshow_folder = Path(__file__).parent / "data" / "slideshow"

# Get a list of all image files in the folder
img_paths = [slideshow_folder / f
             for f in slideshow_folder.iterdir()
                if (slideshow_folder / f).is_file()]

# Create the framer with the list of image paths
framer = SlideshowFramer(img_paths, transition_type, auto_scale=SCALE_IMAGE, display_duration=display_duration, 
                         shuffle=shuffle, transition_duration=transition_duration)


if SIMULATE:
    sim_frame(framer)
else:
    # Create the frame player
    led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=GAMMA, contrast=CONTRAST)
    player = FramePlayer(led_matrix, framer)

    # Play the frames
    player.play_blocking()
