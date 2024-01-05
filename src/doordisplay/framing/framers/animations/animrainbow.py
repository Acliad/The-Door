from framing.framers.framer import Framer
import numpy as np
from colorsys import hsv_to_rgb

class AnimRainbow(Framer):
    """
    A class representing an animated rainbow effect.

    Attributes:
        DEFAULT_FRAMERATE (int): The default framerate for the animation.
        speed (float): The speed of the rainbow animation.
        frequency (float): The frequency of hue cycles in the width of the matrix.
        phase_deg (float): The starting location offset of the hue cycle.
        saturation (float): The saturation of the rainbow colors.
        matrix (numpy.ndarray): The matrix of RGB values representing the rainbow animation.
    """

    def __init__(self):
        """
        Initializes a new instance of the AnimRainbow class.
        """
        super().__init__()
        self.framerate = Framer.DEFAULT_FRAMERATE
        self.speed = 1.0
        self.frequency = 1.0
        self.phase_deg = 0.0
        self.saturation = 1.0

    def get_rgb_array(self):
        """
        Generates an array of RGB values representing the rainbow animation.

        Returns:
            numpy.ndarray: The array of RGB values.
        """
        hue_range = self.frequency * 360
        start_hue = self.phase_deg
        end_hue = start_hue + hue_range

        rgb_array = np.zeros((self.WIDTH, 3), dtype=np.uint8)
        for i, hue in enumerate(np.linspace(start_hue, end_hue, self.WIDTH)):
            hue_normalized = (hue % 360) / 360
            rgb = hsv_to_rgb(hue_normalized, self.saturation, 1.0)
            rgb_array[i] = np.array(rgb) * 255

        return rgb_array

    def update(self):
        """
        Updates the rainbow animation by shifting the matrix of RGB values.

        Returns:
            numpy.ndarray: The updated matrix of RGB values.
        """
        rgb_array = self.get_rgb_array()
        # matrix = np.tile(rgb_array, (self.HEIGHT, 1, 1))
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        for row in range(self.HEIGHT):
            self.matrix[row] = np.roll(rgb_array, row, axis=0)
        
        self.phase_deg += self.speed

        return super().update()

    def reset(self):
        """
        Resets the state of the rainbow animation.
        """
        self.phase_deg = 0.0

    