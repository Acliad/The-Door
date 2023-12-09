from frames.framers.framer import Framer
from PIL import Image
import numpy as np
import random

class Snowflake:
    def __init__(self, size, x, y, speed, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.size = size
        self.matrix: np.ndarray = self.make_snowflake_matrix()

    def make_snowflake_matrix(self) -> np.ndarray:
        flake = np.zeros((self.size, self.size, 3), dtype=np.uint8)

        # Center pixel
        flake[self.size // 2][self.size // 2] = self.color

        # Randomize other pixels around the center with symmetry
        num_pixels = 0
        for i in range(self.size // 2 + 1):
            for j in range(self.size // 2 + 1):
                if random.choice([True, False]):
                    flake[i][j] = self.color
                    flake[self.size - i - 1][j] = self.color
                    flake[i][self.size - j - 1] = self.color
                    flake[self.size - i - 1][self.size - j - 1] = self.color
                    num_pixels += 1
                if num_pixels == self.size // 4:
                    break

        return flake

class AnimSnowflake(Framer):
    DEFAULT_FRAMERATE = 60
    RENDER_WIDTH = Framer.WIDTH * 4
    RENDER_HEIGHT = Framer.HEIGHT * 4

    def __init__(self):
        """
        Initializes a new instance of the AnimSnowflake class.
        """
        super().__init__(AnimSnowflake.DEFAULT_FRAMERATE)
        self.snowflakes = []
        self.matrix = np.zeros((self.RENDER_HEIGHT, self.RENDER_WIDTH, 3), dtype=np.uint8)

    def update(self):
        """
        Updates the snowflake matrix by randomly generating new snowflakes and shifting existing snowflakes down by 
        their speed.
        """
        self.matrix = np.zeros((self.RENDER_HEIGHT, self.RENDER_WIDTH, 3), dtype=np.uint8)

        # Add a new snowflake with a 1% chance
        if random.randint(0, 100) > 80:
            self.add_snowflake()

        # Shift existing snowflakes down by their speed
        for snowflake in self.snowflakes:
            snowflake.y += snowflake.speed
            self.draw_snowflake(snowflake)
            
        
        # Remove snowflakes that have fallen off the bottom of the matrix
        self.snowflakes = [snowflake for snowflake in self.snowflakes if snowflake.y < self.HEIGHT]
        snowflake_img = Image.fromarray(self.matrix)
        return np.array(snowflake_img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS))

    def draw_snowflake(self, snowflake: Snowflake):
        # Calculate the bounds of the snowflake within the frame
        row0 = round(snowflake.y)
        row1 = round(snowflake.y) + snowflake.size
        col0 = snowflake.x
        col1 = min(snowflake.x + snowflake.size, self.WIDTH)

        try:
            self.matrix[row0:row1, col0:col1] = snowflake.matrix[:row1 - row0, :col1 - col0]
        except ValueError as e:
            print("Snowflake out of bounds")
            print(e)
            print(row0, row1, col0, col1)

    def add_snowflake(self):
        size = random.randint(3, 5) * 4
        x = random.randint(0, self.RENDER_WIDTH)
        y = 0
        speed = random.random() * 0.25 + 0.25
        # color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        color = (255, 255, 255)
        self.snowflakes.append(Snowflake(size, x, y, speed, color))

    def reset(self):
        """
        Resets the state of the snowflake animation.
        """
        self.snowflakes = []
        self.matrix = np.zeros((self.RENDER_HEIGHT, self.RENDER_WIDTH, 3), dtype=np.uint8)