
from frames.framers.framer import Framer
import numpy as np
from PIL import Image
from enum import Enum
from time import time
from frames.utils import scale_fit, clip

class GifFramer(Framer):
    class LoopMode(Enum):
        LOOP = 0
        BOUNCE = 1
        ONCE = 2

    def __init__(self, gif_path, framerate=15, loop_mode:LoopMode = LoopMode.LOOP, auto_scale:bool = True):
        """
        Initializes a GifFramer object. The given framerate is used only if the framerate can't be determined from the GIF.

        Args:
            gif_path (str): The path to the GIF file.
            framerate (int, optional): The desired framerate for the GIF animation. Defaults to 15.
            loop_mode (LoopMode, optional): The loop mode for the GIF animation. Defaults to LoopMode.LOOP.
            auto_scale (bool, optional): Whether to automatically scale the frames to fit the desired dimensions. 
                                         Defaults to True.
        """
        self.gif_path = gif_path
        # TODO: Is there a better approach to this? Should the frameplayer control frame rate?
        # GIFs have a variable frame rate, so we'll set the framerate to 120 so update() is called frequently then
        # use time delta to determine when to update the frame.
        super().__init__(100)
        self.last_update_time = 0
        self.loop_mode = loop_mode
        self.play_forward = True

        gif = Image.open(self.gif_path)
        self.num_frames = gif.n_frames
        self.current_frame = 0

        # Check if the given path is a gif
        if gif.format != 'GIF':
            raise ValueError(f'File at {gif_path} is not a GIF')
        
        # Extract the frames. We could instead transform the GIF frame on every call to update() and not have to do all
        # this quagmire, but this reduces the overhead of that function
        self.frames = []
        for i in range(self.num_frames):
            gif.seek(i)
            frame = gif.copy().convert('RGB')
            if auto_scale:
                frame = scale_fit(frame, self.WIDTH, self.HEIGHT)
            else:
                frame = clip(frame, self.WIDTH, self.HEIGHT)

            # Get the duration of the frame. If the GIF doesn't have a duration, we'll use the given framerate
            # NOTE: framerate is not self.framerate, which is currently hardcoded to 60
            duration_ms = gif.info.get('duration') or (1 / framerate) * 1000
            self.frames.append({'frame': frame, 'duration_s': duration_ms / 1000})

    def update(self):
        """
        Updates the current frame of the GIF framer.

        Returns:
            frame_matrix (list): The matrix representation of the current frame.
        """

        # Update the current state
        if (time() - self.last_update_time) > self.frames[self.current_frame]['duration_s']:
            self.last_update_time = time()
            self.current_frame += 1 if self.play_forward else -1
            # If we reach the end of the GIF, decide what to do based on the loop mode
            if self.current_frame == self.num_frames or self.current_frame == -1:
                match self.loop_mode:
                    case self.LoopMode.LOOP:
                        # Just loop back to the beginning
                        self.current_frame = 0
                    case self.LoopMode.BOUNCE:
                        # Reverse the direction
                        self.current_frame += -1 if self.play_forward else 1
                        self.play_forward = not self.play_forward
                    case self.LoopMode.ONCE:
                        # Stop playing
                        return None

        frame_matrix = np.array(self.frames[self.current_frame]['frame'])
        return frame_matrix

    def reset(self):
        """
        Resets the GIF framer to its initial state.
        """
        self.current_frame = 0
        self.last_update_time = time()
        self.play_forward = True