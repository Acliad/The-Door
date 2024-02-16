from framing.framers.framer import Framer
from PIL import Image
import numpy as np
from pathlib import Path
from framing.utils import scale_fit, clip
from typing import List

class SlideshowFramer(Framer):
    def __init__(self, image_paths: List[str | Path], auto_scale: bool = True, duration: float = 2.0):
        super().__init__()
        self.auto_scale = auto_scale
        self.image_paths = image_paths
        self.current_image_index = 0
        self.matrix = None
        self.dt = duration
        self._load_slide()

    def set_images(self, image_paths: List[str | Path]):
        self.image_paths = image_paths
        self.current_image_index = 0
        self._load_slide()

    def update(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
        self._load_slide()
          
        return super().update()
    
    def reset(self):
        self.current_image_index = 0
        self._load_slide()

    def _load_slide(self):
        # Open the current image
        image_path = self.image_paths[self.current_image_index]
        image = Image.open(image_path)

        if self.auto_scale:
            image = scale_fit(image, self.WIDTH, self.HEIGHT)
        else:
            image = clip(image, self.WIDTH, self.HEIGHT)

        self.matrix = np.array(image)
