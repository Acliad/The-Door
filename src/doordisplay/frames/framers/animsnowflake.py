from frames.framers.framer import Framer
from PIL import Image
import numpy as np
import random
import bisect
import time

class Snowflake:
    def __init__(self, size, x:float, y:float, speed:float, color=(255, 255, 255)):
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
    RENDER_WIDTH = Framer.WIDTH * 1
    RENDER_HEIGHT = Framer.HEIGHT * 1

    def __init__(self):
        """
        Initializes a new instance of the AnimSnowflake class.
        """
        super().__init__(AnimSnowflake.DEFAULT_FRAMERATE)
        self.snowflakes = []
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)

    def update(self):
        """
        Updates the snowflake matrix by randomly generating new snowflakes and shifting existing snowflakes down by 
        their speed.
        """
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)


        # Add a new snowflake with a 30% chance
        if random.randint(0, 100) > 70:
            self.add_snowflake()

        # start_time = time.time()
        # Shift existing snowflakes down by their speed
        for snowflake in self.snowflakes:
            # Since snowflakes are sorted by size, the larger ones should be drawn on top of the smaller ones
            snowflake.y += snowflake.speed
            self.draw_snowflake(snowflake)
        # end_time = time.time()
        # if self.snowflakes:
        #     time_per_snowflake = (end_time - start_time) / len(self.snowflakes) * 1000
        #     time_all_snowflakes = (end_time - start_time) * 1000
        #     print(f"Draw time: {time_per_snowflake:.2f} ms")
        #     print(f"Total draw time: {time_all_snowflakes:.2f} ms")
            
        # Remove snowflakes that have fallen off the bottom of the matrix
        self.snowflakes = [snowflake for snowflake in self.snowflakes if snowflake.y < self.RENDER_HEIGHT]
        snowflake_img = Image.fromarray(self.matrix)
        return self.matrix
        # return np.array(snowflake_img.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS))

    def draw_snowflake(self, snowflake: Snowflake):
        # TODO: The below is kind of gross, maybe this should be rethought for clarity. Part of the reason for doing
        # it so complicated is so that snowflakes can be drawn on top of other snowflakes and the empty pixels won't
        # overwrite the existing snowflake. This also allows arbitrary pixel colors for the flakes.

        # Calculate the bounds of the snowflake within the frame
        pixel_indices = np.where(snowflake.matrix)
        # Add snowflake position to pixel indices to shift the snowflake to the correct position for the matrix
        frame_matrix_indices = np.copy(pixel_indices)
        frame_matrix_indices[0] += round(snowflake.y)
        frame_matrix_indices[1] += round(snowflake.x)
        # This is a real noodle-baker. pixel_matrix_indices is a 2D array of shape (3, num_valid_pixels*3) where the
        # axis=0 values are the row, axis=1 values are the column, and axis=2 values are the color channel. We want to
        # check if any of the row or column values are out of bounds of the matrix. The next two lines create boolean
        # arrays of shape (num_valid_pixels*3,) where the values are True if the row or column is in bounds and False
        # otherwise. The last line combines the two boolean arrays to index pixel_matrix_indices and select only the
        # indices where the row and column are within the bounds of the matrix.
        in_bound_rows = (frame_matrix_indices[0] >= 0) & (frame_matrix_indices[0] < self.RENDER_HEIGHT)
        in_bound_cols = (frame_matrix_indices[1] >= 0) & (frame_matrix_indices[1] < self.RENDER_WIDTH)
        frame_matrix_indices = frame_matrix_indices[:, in_bound_rows & in_bound_cols]

        # We now back out the indices of the snowflake matrix that we want to use by subtracting the snowflake
        # position that we added earlier
        snowflake_matrix_indices = np.copy(frame_matrix_indices)
        snowflake_matrix_indices[0] -= round(snowflake.y)
        snowflake_matrix_indices[1] -= round(snowflake.x)

        # print(snowflake.matrix.shape)
        # print(snowflake_matrix_indices.shape)

        # Finally, we can draw the snowflake onto the frame matrix by placing the valid snowflake pixels into the
        # frame matrix
        self.matrix[frame_matrix_indices[0], frame_matrix_indices[1]] = snowflake.matrix[snowflake_matrix_indices[0], snowflake_matrix_indices[1]]

        # row0 = round(snowflake.y)
        # row1 = round(snowflake.y) + snowflake.size
        # col0 = snowflake.x
        # col1 = min(snowflake.x + snowflake.size, self.WIDTH)

        # try:
        #     self.matrix[row0:row1, col0:col1] = snowflake.matrix[:row1 - row0, :col1 - col0]
        # except ValueError as e:
        #     print("Snowflake out of bounds")
        #     print(e)
        #     print(row0, row1, col0, col1)

    def add_snowflake(self):
        size_idx = random.randint(0, 2)
        sizes = [1, 3, 5]
        speeds = [random.random()*0.2+0.3, random.random()*0.2+0.45, random.random()*0.2+0.6]
        brightes_scalers = [0.7, 0.85, 1.0]
        size = sizes[size_idx]
        x = random.randint(0, self.RENDER_WIDTH)
        y = -size
        flake_color = np.array((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        # flake_color = np.array((255, 255, 255))
        # Make smaller snowflakes slightly smaller than larger snowflakes
        flake_color = np.round(flake_color * brightes_scalers[size_idx])
        bisect.insort(self.snowflakes, Snowflake(size, x, y, speeds[size_idx], flake_color), key=lambda s: s.size)

    def reset(self):
        """
        Resets the state of the snowflake animation.
        """
        self.snowflakes = []
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)