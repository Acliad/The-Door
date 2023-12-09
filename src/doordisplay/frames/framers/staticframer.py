from frames.framers.framer import Framer
from PIL import Image
import numpy as np
from pathlib import Path
from frames.utils import scale_fit, clip

class StaticFramer(Framer):
    def __init__(self, image_path:str | Path, auto_scale:bool = True):
        # Framerate is 0 for static frames
        super().__init__(0)
        self.auto_scale = auto_scale
        self.image_path = image_path
        self._load_image()

    def update(self):
        return self.current_frame
    
    def reset(self):
        self._load_image()

    def _load_image(self):
        # Open the image
        image = Image.open(self.image_path)

        if self.auto_scale:
            image = scale_fit(image, self.WIDTH, self.HEIGHT)
        else:
            image = clip(image, self.WIDTH, self.HEIGHT)

        # Convert the image to an array
        image_array = np.array(image)

        # Calculate the starting position for placing the image in the frame matrix
        start_row = (self.HEIGHT - image_array.shape[0]) // 2
        start_col = (self.WIDTH - image_array.shape[1]) // 2

        # Create the frame matrix
        frame_matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        frame_matrix[start_row:start_row+image_array.shape[0], start_col:start_col+image_array.shape[1]] = image_array

        self.current_frame = frame_matrix
