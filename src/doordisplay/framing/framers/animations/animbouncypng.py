from framing.framers.framer import Framer
import numpy as np
from framing.utils import place_in
from PIL import Image
import numpy as np
from pathlib import Path
from framing.utils import scale_fit, clip


class BouncyPNG():

    def __init__(self,
                 x: float,
                 y: float,
                 speed_x: float,
                 speed_y: float,
                 image_path:str | Path, 
                 auto_scale:bool = True
                 ) -> None:
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.auto_scale = auto_scale
        self.image_path = image_path
        self.image_array = None

        self._load_image()

    def _load_image(self):
        # Open the image
        image = Image.open(self.image_path)
        image = image.convert("RGB")

        if self.auto_scale:
            image = scale_fit(image, Framer.WIDTH, Framer.HEIGHT)
        else:
            image = clip(image, Framer.WIDTH, Framer.HEIGHT)

        # Convert the image to an array
        self.image_array = np.array(image)


class AnimBouncyPNG(Framer):
    def __init__(self, image_path:str | Path, auto_scale:bool = True):

        super().__init__()
        self.auto_scale = auto_scale
        self.image_path = image_path

        # Create the matrix for the frame
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)

        # Create a png
        self.png = BouncyPNG(0, 0, 15.0, 15.0, image_path, auto_scale)

    def update(self):

        self.png.x += self.png.speed_x * self.dt
        self.png.y += self.png.speed_y * self.dt       

        # If the image hits the edge of the frame, reverse its direction
        if self.png.x >= self.WIDTH - self.png.image_array.shape[1] or self.png.x <= 0:
            self.png.speed_x *= -1
        if self.png.y >= self.HEIGHT - self.png.image_array.shape[0] or self.png.y <= 0:
            self.png.speed_y *= -1

            
        # Create the matrix for the frame
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        
        place_in(self.matrix, self.png.image_array, self.png.y, self.png.x, transparent_threshold=10)

        return super().update()
    

    def reset(self):
            pass
        

        
        





