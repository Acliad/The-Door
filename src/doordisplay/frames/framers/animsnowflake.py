"""
Animation of a snowfall. Current features:
    - Snowflakes are randomly generated. The generation rate can be adjusted.
    - Snowflakes fall at a constant speed. The fall speed can be adjusted.
    - Wind blows the snowflakes horizontally. The wind speed follows opensimplex (Perlin) noise.
    - Storm intensity amplifies the wind speed and generation rate. The storm intensity follows opensimplex (Perlin)
      noise.
    - There are multiple sizes of snowflakes (default 3). The sizes are drawn and affected by speed such that larger
      snowflakes appear to be "closer" than smaller snowflakes.
    - Snowflakes can drawn with a trail factor that fades out the snowflakes as they fall.
    - Snowflakes can be drawn with interpolation to make the snowflakes move smoother.

TODO:
    - Improve snowflake generation to make them more realistic and faster to generate
    - Add more accumulation modes (constant, blow away, etc.)
    - Add a fancy accumulation wipe animation
    - Add random wind gusts
"""

from frames.framers.framer import Framer
from PIL import Image
import numpy as np
import random
import bisect
import time
import colorsys
from frames.utils import place_in
from typing import Callable, Sequence
from dataclasses import dataclass
import opensimplex # NOTE: Installing numba will increase performance of noise generation


class Snowflake:
    """
    Returns a randomly generated snowflake of the specified size. These rules apply to the generation of the snowflake:
    TODO: Implement these rules
    1. The snowflake must be symmetric about the center x-axis and y-axis. TODO: Make this have odd symmetry only?
    2. The snowflake must have at least one pixel at the extents of size. I.e. if size=5, then the snowflake must have
       at least one pixel at (0, 0), (0, 1), (0, 2), (1, 0), (2, 0) and follow rule 1. This prevents the snowflake from
       being smaller than the specified size.
    3. One edge of the snowflake cannot be fully filled. I.e., if the snowflake is size=5, then the snowflake cannot
       cannot have all pixels filled at (0, 0), (0, 1), (0, 2) OR all pixels filled at (0, 0), (1, 0), (2, 0). This
       prevents square shapes, T-shapes, and H-shapes from being generated.
    4. Corner of a snowflake cannot be next to two filled pixel on the edge of the snowflake. This prevents the
       snowflake from appearing square. TODO: Maybe this only applies if snowflake is fully symmetric, not odd
       symmetric?

    Attributes:
        size (int): The size of the snowflake. x (float): The x-coordinate of the snowflake's position. y (float): The
        y-coordinate of the snowflake's position. speed (float): The speed of the snowflake. color (tuple): The color of
        the snowflake in RGB format. matrix (ndarray): The matrix representation of the snowflake.

    Methods:
        make_snowflake_matrix: Generates the matrix representation of the snowflake.
    """
    def __init__(self, size, x:float, y:float, speed_x:float=1.0, speed_y:float=0.0,
                 color:tuple[int, int, int]=(255, 255, 255)):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.color = color
        self.size = size
            
        self.matrix: np.ndarray = self.make_snowflake_matrix()

    def make_snowflake_matrix(self) -> np.ndarray:
        flake = np.zeros((self.size, self.size, 3), dtype=np.uint8)

        # Center pixel if odd size
        if self.size % 2 == 1:
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
    
class Accumulator:
    """
    Accumulates snowflakes that have fallen to the bottom of the matrix.

    When a snowflake falls to the top of the pile, one of the following happens:
        - If the column struck is empty, then a bin is created the width of the snowflake
        - If the column struck is a partially full bin, then the snowflake is added to the bin
        - If the column struck is a full bin, then the snowflake is added to the next closest bin or the bin is expanded
          if the closest would-be bin is empty

    Attributes:
        matrix (ndarray): The matrix representation of the accumulated snowflakes. Generally this should be the same
            size as the matrix that the snowflakes are falling into.
        bins (list[Accumulator.Bin | None]): The list of bins that accumulate the fallen snowflakes.
        layers (int): The current number of layers.
        bin_level_scaler (int): The scaler used to determine the full level of a bin.

    Methods:
        __init__(self, height:int = Framer.HEIGHT, width:int = Framer.WIDTH, bin_level_scaler:int = 10) -> None:
            Initializes the Accumulator object.
        accumulate(self, snowflake: Snowflake) -> bool:
            Accumulates a snowflake that has fallen to the bottom of the matrix.
        _blend_colors(color1: tuple[int, int, int], color2: tuple[int, int, int], weight:float=0.2) -> tuple[int, int, int]:
            Blends two colors together.
        _new_bin(self, x:int, snowflake:Snowflake) -> None:
            Adds a new bin to the accumulation.
        _add_to_bin(self, accumulation_bin:Bin, snowflake: Snowflake) -> None:
            Adds a snowflake to the given bin.
        _closest_fillable_bin_idx(self, x: int) -> int:
            Finds the closest fillable bin to the given x-coordinate.
        accumulation(self) -> np.ndarray:
            Gets the accumulation matrix.
    """

    @dataclass
    class Bin:
        """
        Represents a bin that accumulates fallen snowflakes.

        Attributes:
            idx (int): The index of the bin.
            width (int): The width of the bin.
            full_level (int): The full level of the bin.
            color (tuple[int, int, int]): The color of the bin.
            _level (int): The current level of the bin.
        """
        idx: int
        width: int
        full_level: int
        color: tuple[int, int, int]
        _level: int = 0

        def full(self) -> bool:
            """
            Checks if the bin is full.

            Returns:
                bool: True if the bin is full, False otherwise.
            """
            return self.level >= self.full_level

        @property
        def current_color(self) -> tuple[int, int, int]:
            """
            Gets the current color of the bin.

            Returns:
                tuple[int, int, int]: The current color of the bin.
            """
            scaler = self.level / self.full_level
            r = int(round(self.color[0] * scaler))
            g = int(round(self.color[1] * scaler))
            b = int(round(self.color[2] * scaler))
            return (r, g, b)
        
        @property
        def level(self) -> int:
            """
            Gets the current level of the bin.

            Returns:
                int: The current level of the bin.
            """
            return self._level
        
        @level.setter
        def level(self, value: int):
            """
            Sets the current level of the bin.

            Args:
                value (int): The value to set as the current level of the bin.
            """
            self._level = max(0, min(value, self.full_level))

    def __init__(self, height:int = Framer.HEIGHT, width:int = Framer.WIDTH, bin_level_scaler:int = 50) -> None:
        self.matrix = np.zeros((height, width, 3), dtype=np.uint8)
        # Bins is a list of Bin objects. The element at index i points to the bin that occupies that space. For a bin
        # of width 3, the elements at indices i, i+1, and i+2 will all point to the same bin object.
        self.bins:list[Accumulator.Bin | None] = [None] * width
        self.layers = 1 # Current number of layers
        self.bin_level_scaler = bin_level_scaler

    def accumulate(self, snowflake: Snowflake) -> bool:
        """
        Accumulates a snowflake that has fallen to the bottom of the matrix.

        Args:
            snowflake (Snowflake): The snowflake to accumulate.

        Returns:
            bool: True if the snowflake was accumulated, False otherwise.
        """
        snowflake_x = round(snowflake.x)
        # Check if the snowflake is in the accumulation area
        if snowflake_x < 0 or snowflake_x >= self.matrix.shape[1]:
            return False
        
        # Check if the snowflake landed on an existing bin
        accumulation_bin:Accumulator.Bin | None = self.bins[snowflake_x]
        if accumulation_bin: # Bin exists
            if not accumulation_bin.full(): # Bin is not full
                self._add_to_bin(accumulation_bin, snowflake)
            else: # Bin is full
                # Check for the closest non-full bin
                closest_bin_idx = self._closest_fillable_bin_idx(snowflake_x)
                closest_bin = self.bins[closest_bin_idx]
                if closest_bin: # Closest bin exists
                    self._add_to_bin(closest_bin, snowflake)
                else: # Closest bin does not exist
                    self._new_bin(closest_bin_idx, snowflake)
        else: # Bin does not exist
            self._new_bin(snowflake_x, snowflake)

        if all([(b.full() if b else False) for b in self.bins]):
            self.layers += 1
            self.bins = [None] * self.matrix.shape[1]
            if self.layers == self.matrix.shape[0]:
                self.matrix.fill(0)
                self.layers = 1

        return True

    @staticmethod
    def _blend_colors(color1: tuple[int, int, int], 
                      color2: tuple[int, int, int], 
                      weight:float=0.2
                      ) -> tuple[int, int, int]:
        """
        Blends two colors together.

        Args:
            color1 (tuple[int, int, int]): The first color to blend.
            color2 (tuple[int, int, int]): The second color to blend.
            weight (float, optional): The weight of the first color. Defaults to 0.2.

        Returns:
            tuple[int, int, int]: The blended color.
        """
        return (int(round(color1[0]*weight + color2[0]*(1-weight))), 
                int(round(color1[1]*weight + color2[1]*(1-weight))),
                int(round(color1[2]*weight + color2[2]*(1-weight)))
                )

    def _new_bin(self, x:int, snowflake:Snowflake) -> None:
        """
        Adds a new bin to the accumulation. If the bin cannot be inserted at the given x-coordinate, then the bin is
        shifted to the left until it fits. If there are not enough empty spaces within the range of the given x 
        coordinate, then the bin is compressed.

        Args:
            x (int): The x-coordinate of the bin to add. The value of self.bins[x] must be None.
            snowflake (Snowflake): The snowflake to add to the bin.
        """
        assert self.bins[x] == None

        desired_width = snowflake.size
        left_idx = x
        right_idx = x
        # Search for empty space to the right of x
        for _ in range(min(desired_width-1, len(self.bins)-x)-1):
            if self.bins[right_idx+1] == None:
                right_idx += 1
            else:
                break

        # If there is not enough space to the right of x, then search to the left of x
        actual_width = right_idx - left_idx + 1
        for _ in range(min(desired_width-actual_width-1, x)):
            if self.bins[left_idx-1] == None:
                left_idx -= 1
            else:
                break
        # If there is still not enough space, then compress the bins
        actual_width = right_idx - left_idx + 1

        bin_full_level = snowflake.size * self.bin_level_scaler
        accumulation_bin = Accumulator.Bin(left_idx, actual_width, bin_full_level, snowflake.color)
        self.bins[left_idx:right_idx+1] = [accumulation_bin] * actual_width
        self._add_to_bin(accumulation_bin, snowflake)

    def _add_to_bin(self, accumulation_bin:Bin, snowflake: Snowflake) -> None:
        """
        Adds a snowflake to the given bin.

        Args:
            accumulation_bin (Accumulator.Bin): The bin to add the snowflake to.
            snowflake (Snowflake): The snowflake to add to the bin.
        """
        accumulation_bin.level += snowflake.size
        accumulation_bin.color = self._blend_colors(snowflake.color, accumulation_bin.color, 0.2)

        col_start_idx = accumulation_bin.idx
        col_end_idx = accumulation_bin.idx + accumulation_bin.width
        self.matrix[-self.layers, col_start_idx:col_end_idx] = accumulation_bin.current_color

    def _closest_fillable_bin_idx(self, x: int) -> int:
        """
        Finds the closest fillable (i.e., non-full) bin to the given x-coordinate and returns the index of that bin.

        Args:
            x (int): The x-coordinate to search around.

        Returns:
            int: The index of the closest fillable bin.
        
        Raises:
            RuntimeError: If no fillable bin is found.
        """
        left_idx = x - 1
        right_idx = x + 1

        while True:
            # Look for the closest non-full bin, which can be either None or not full
            if left_idx >= 0 and (self.bins[left_idx] == None or not self.bins[left_idx].full()):
                return left_idx
            elif right_idx < len(self.bins) and (self.bins[right_idx] == None or not self.bins[right_idx].full()):
                return right_idx
            elif left_idx < 0 and right_idx >= len(self.bins):
                break
            left_idx -= 1
            right_idx += 1

        for bin in self.bins:
            print(bin)
        raise RuntimeError("No fillable bin found")

    @property
    def accumulation(self) -> np.ndarray:
        """
        Gets the accumulation matrix.

        Returns:
            np.ndarray: The accumulation matrix.
        """
        return self.matrix[-self.layers:]

    
class AnimSnowflake(Framer):
    DEFAULT_FRAMERATE:float  = 60.0
    MAX_WIND_INTENSITY:float = 10.0
    MIN_FALL_SPEED:float     = 0.05

    def __init__(self, 
                 gen_rate:float = 1000, 
                 interpolate:bool = False, 
                 trail_factor:float = 0.0, 
                 fall_speed:float = 1.0, 
                 wind_speed:float = 0.0, 
                 wind_step:float = 0.00005,
                 wind_start_pos:float = 0.0,
                 wind_intensity:float = 3.0, 
                 wind_seed:int | None = None,
                 storm_factor:float = 2.0,
                 storm_step:float = 0.00002,
                 storm_start_pos:float = 0.0,
                 snowflake_sizes: list[int, int, int] = [1, 3, 5],
                 snowflake_speed_scalers: list[float, float, float] = [0.3, 0.45, 0.6],
                 snowflake_brightness_scalers: list[float, float, float] = [0.7, 0.8, 1.0],
                 snowflake_color: str | Callable[[int], Sequence[int]] = 'random',
                 speed_randomness: float = 0.2,
                ) -> None:
        """
        Initializes a new instance of the AnimSnowflake class.

        Args:
            gen_rate (float, optional): The generation rate of snowflakes in milliseconds. Defaults to 1000.
            interpolate (bool, optional): Whether to interpolate the position of snowflakes. Defaults to False.
            trail_factor (float, optional): The trail factor for fading out snowflakes. Defaults to 0.0.
            fall_speed (float, optional): The fall speed of snowflakes. Defaults to 1.0.
            wind_speed (float, optional): The initial wind speed. Defaults to 0.0.
            wind_step (float, optional): The increment used for opensimplex noise for wind speed. Defaults to 0.00005.
            wind_start_pos (float, optional): The starting position of the wind speed in opensimplex noise space. 
                Defaults to 0.0.
            wind_intensity (float, optional): The intensity of the wind. Defaults to 3.0.
            wind_seed (int | None, optional): The seed for the opensimplex noise generator for wind speed. If None, a 
                random seed will be used. Defaults to None.
            storm_factor (float, optional): The factor to amplify the storm intensity. Defaults to 2.0.
            storm_step (float, optional): The increment used for opensimplex noise for storm intensity. Defaults to 
                0.00002.
            storm_start_pos (float, optional): The starting position of the storm intensity in opensimplex noise space. 
                Defaults to 0.0.
            snowflake_sizes (list[int, int, int], optional): The sizes of the snowflakes. Defaults to [1, 3, 5].
            snowflake_speed_scalers (list[float, float, float], optional): The speed scalers for the snowflakes. 
                Defaults to [0.3, 0.45, 0.6].
            snowflake_brightness_scalers (list[float, float, float], optional): The brightness scalers for the 
                snowflakes. Defaults to [0.7, 0.8, 1.0].
            snowflake_color (str | Callable[[int], Sequence[int]], optional): The color of the snowflakes. Can be 
                'random', 'white', or a callable function that takes the size of the snowflake as input and returns a 
                sequence of RGB values. Defaults to 'random'.
            speed_randomness (float, optional): The randomness factor for the snowflake speed. Defaults to 0.2.
        """
        super().__init__(AnimSnowflake.DEFAULT_FRAMERATE)
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.accumulator = Accumulator(self.HEIGHT, self.WIDTH)
        self.snowflakes:list[Snowflake] = []

        self.snowflake_sizes = snowflake_sizes
        self.snowflake_sizes.sort() # Make sure the snowflake sizes are non-decreasing
        self.snowflake_speed_scalers = snowflake_speed_scalers
        self.snowflake_brightness_scalers = snowflake_brightness_scalers
        self.snowflake_color = snowflake_color
        self.speed_randomness = speed_randomness

        self.snowflake_gen_rate = gen_rate # NOTE: Also sets self._snowflake_chance
        self.interpolate = interpolate

        self.fall_speed = fall_speed
        self.trail_factor = trail_factor

        # The increment used for opensimplex noise. Larger values will cause the wind speed to change more quickly
        self.wind_step = wind_step
        self.wind_intensity = wind_intensity
        self.wind_pos = wind_start_pos # The current "position" of the wind speed in opensimplex noise space
        self.wind_speed = wind_speed

        self.storm_factor = storm_factor
        self.storm_step = storm_step
        self.storm_pos = storm_start_pos
        self.storm_intensity = 0

        self._simplex_wind_speed_idx = 0
        self._simplex_storm_idx = 10
        

        opensimplex.seed(wind_seed or random.randint(0, 2**64-1))

         # TODO: Remove after debugging
        self.max_draw_time = [0, 0, 0]
        self.avg_draw_time = 0
        self.max_accumulate_time = 0
        self.avg_accumulate_time = 0

    def update(self) -> np.ndarray:
        """
        Updates the snowflake matrix by randomly generating new snowflakes and shifting existing snowflakes down by 
        their speed.

        Returns:
            np.ndarray: The updated snowflake matrix.
        """
        self.matrix = (self.matrix * self.trail_factor).astype(np.uint8)

        start_time = time.time()
        for pos in self._get_new_snowflake_positions():
            self.add_snowflake(pos[0], pos[1])
        end_time = time.time()
        add_time = end_time - start_time

        start_time = time.time()
        if self.storm_factor:
            simplex_storm_intensity = opensimplex.noise2(self.storm_pos, self._simplex_storm_idx) + 1
            self.storm_intensity = self.storm_factor * simplex_storm_intensity
            self.storm_pos += self.storm_step
        else:
            self.storm_intensity = 1.0

        simplex_wind_speed = opensimplex.noise2(self.wind_pos, self._simplex_wind_speed_idx)
        self.wind_speed = self.storm_intensity * self.wind_intensity * simplex_wind_speed
        self.wind_pos += self.wind_step
        noise_time = time.time() - start_time
        
        accumulate_total_time = 0
        start_time = time.time()
        # Remove snowflakes that have fallen off the bottom of the matrix
        snowflakes_trimmed = []
        for snowflake in self.snowflakes:
            snowflake.y += snowflake.speed_y
            snowflake.x += self.wind_speed*snowflake.speed_x
            if self.in_frame(snowflake):
                snowflakes_trimmed.append(snowflake)
                x = snowflake.x if self.interpolate else round(snowflake.x)
                y = snowflake.y if self.interpolate else round(snowflake.y)
                # NOTE: Since snowflakes are sorted by size, the larger ones should be drawn on top of the smaller ones
                place_in(self.matrix, snowflake.matrix, y, x, transparent_threshold=5)
            elif snowflake.y >= self.HEIGHT - self.accumulator.layers:
                accumulate_start_time = time.time()
                # Accumulate snowflakes that have fallen off the bottom of the matrix
                self.accumulator.accumulate(snowflake)
                accumulate_total_time += time.time() - accumulate_start_time

        self.snowflakes = snowflakes_trimmed
        self.matrix[-self.accumulator.layers:] = self.accumulator.accumulation
        end_time = time.time()

        if self.snowflakes:
            time_per_snowflake = (end_time - start_time) / len(self.snowflakes) * 1000
            time_all_snowflakes = (end_time - start_time) * 1000
            # Track the top 3 max draw times
            self.max_draw_time[0] = round(time_all_snowflakes, 2) if time_all_snowflakes > self.max_draw_time[0] else round(self.max_draw_time[0], 2)
            self.max_draw_time.sort()
            self.max_accumulate_time = max(self.max_accumulate_time, accumulate_total_time)
            alpha = 0.995
            self.avg_accumulate_time = self.avg_accumulate_time * alpha + accumulate_total_time * (1-alpha)
            self.avg_draw_time = self.avg_draw_time * alpha + time_all_snowflakes * (1-alpha)
            print(f"Add time: {add_time:.3f} ms")
            # print(f"Noise time: {noise_time:.3f} ms")
            print(f"Accumulate time: {self.avg_accumulate_time*1e3:.3f} ms")
            print(f"Max accumulate time: {self.max_accumulate_time*1e3:.3f} ms")
            print(f"Draw time: {time_per_snowflake:.3f} ms")
            print(f"Total draw time: {time_all_snowflakes:.3f} ms")
            print(f"Avg draw time: {self.avg_draw_time:.3f} ms")
            print(f"Max draw time: {self.max_draw_time} ms")
            print(len(self.snowflakes))
            # print(f"Wind speed: {self.wind_speed:.2f}")
            # print(f"Storm intensity: {self.storm_intensity:.2f}")
        
        return self.matrix
    
    def in_frame(self, snowflake: Snowflake) -> bool:
        """
        Checks if the snowflake is in bounds of the frame such that any part of it will be displayed.

        Args:
            snowflake (Snowflake): The snowflake to check.

        Returns:
            bool: True if the snowflake is in bounds of the matrix, False otherwise.
        """
        size = snowflake.size
        x = snowflake.x
        y = snowflake.y
        return y + size > 0 and y < self.HEIGHT-self.accumulator.layers and x + size > 0 and x < self.WIDTH
    
    def add_snowflake(self, x:float, y:float):
        """
        Adds a snowflake to the animation.

        Args:
            x (float): The x-coordinate (column) of the snowflake's position.
            y (float): The y-coordinate (row) of the snowflake's position.
        """
        depth_idx = random.randint(0, len(self.snowflake_sizes)-1)
        speed_y = self.snowflake_speed_scalers[depth_idx]*self.fall_speed + \
                    random.normalvariate(sigma=0.2)*self.speed_randomness
        speed_y = max(AnimSnowflake.MIN_FALL_SPEED, speed_y)
        speed_scaler_x =self.snowflake_speed_scalers[depth_idx]
        brightness_scaler = self.snowflake_brightness_scalers[depth_idx]
        size = self.snowflake_sizes[depth_idx]

        # Adjust x, y so the snowflake spawns just off the edge of the matrix
        #   - If the snowflake is on the top edge of the matrix, shift it up by its size and left by its size//2
        #   - If the snowflake is on the left edge of the matrix, shift it left by its size
        #   - If the snowflake is on the right edge of the matrix, shift it right by 1 so it's just off the edge
        # TODO: Should this be done in update() instead?
        if y == 0:
            y -= size
            x -= size // 2
        elif x == 0:
            x -= size
        elif x == self.WIDTH - 1:
            x += 1

        if isinstance(self.snowflake_color, Callable):
            flake_color = np.array(self.snowflake_color(size))
        elif self.snowflake_color == 'random':
            max_rand = 127
            flake_color = np.random.randint(0, max_rand, 3) + random.randint(0, 255-max_rand)
        elif self.snowflake_color == 'white':
            flake_color = np.array((255, 255, 255))
        else:
            raise ValueError(f"Invalid snowflake color: {self.snowflake_color}")
        
        # Make smaller snowflakes slightly smaller than larger snowflakes
        flake_color = np.round(flake_color * brightness_scaler)

        bisect.insort(self.snowflakes, 
                      Snowflake(size, x, y, speed_scaler_x, speed_y, color=flake_color), 
                      key=lambda s: s.size
                     )

    def reset(self) -> None:
        """
        Resets the state of the snowflake animation.
        """
        self.snowflakes = []
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)

    def _get_new_snowflake_positions(self) -> list:
        """Returns a 2D list of snowflake positions to generate. The first column is the x-coordinate and the second
        column is the y-coordinate.

        TODO: This could be optimized with a lookup table, but is it slow enough to worry about? 

        Returns:
            list: list of snowflake positions to generate.
        """
        prob_horizontal = self._snowflake_chance * self.storm_intensity
        # If the probability of generating a snowflake on the on pixel of the horizontal edge is P_horz, then the
        # probability of generating a snowflake on a given update is P_horz*WIDTH. Refering to the drawing below, the
        # edge probability is equal to the probability of generating the snowflakes on the horizontal edge scaled by how
        # many of those horizontal pixels "covers" the edge. In other words, how much horizontal space can be blown into
        # the vertical space by wind. 
        #
        # Right Edge of Matrix
        #        ↓
        #         ------ ← Number of columns contributing to snowflakes blowing into the vertical space
        #        |     /
        #        |    /
        # HEIGHT |   /
        #        |  /
        #        | / 
        #        |/
        #
        # The probability of generating a snowflake within a horizontal space Nc is P_horz * Nc. The number of vertical
        # pixels (HEIGHT) "covered" by this horizontal space (Nc) is determined by how fast the wind is blowing. If
        # theta is the angle made by the right edge of the matrix and the hypotenuse, then tan(theta) = x/y =
        # wind_speed/fall_speed. The probability of generating a snowflake anywhere on the edge is then 
        # P_edge = HEIGHT * tan(theta) * P_horz. Thus the probability per pixel of generating a snowflake on the edge
        # is P_edge/HEIGHT = tan(theta) * P_horz = wind_speed/fall_speed * P_horz.

        # Edge probability is symmetric, handle direction when creating position list
        prob_edge = abs(self.wind_speed / self.fall_speed * prob_horizontal)

        horizontal_chances = np.random.rand(self.WIDTH)
        horizontal_samples = np.where(horizontal_chances < prob_horizontal)[0]
        positions = [[x, 0] for x in horizontal_samples]

         # -1 because the top edge is already covered by horizontal
        vertical_chances = np.random.rand(self.HEIGHT-self.accumulator.layers-1)
        vertical_samples = np.where(vertical_chances < prob_edge)[0]
        # If wind is negative, then the snowflakes will spawn only on the right edge of the matrix. 
        if self.wind_speed < 0:
            positions += [[self.WIDTH-1, y+1] for y in vertical_samples]
        elif self.wind_speed: # Don't need to process if wind_speed == 0
            positions += [[0, y+1] for y in vertical_samples]
        
        return positions

    @property
    def snowflake_gen_rate(self) -> int:
        """
        Gets the generation rate of snowflakes. The rate is equal to the average number of snowflakes per minute that
        are generated at the top edge of the frame. I.e., the number of snowflakes per minute when wind_speed == 0.

        Returns:
            int: The snowflake generation rate.
        """
        return self._snowflakes_gen_rate
    
    @snowflake_gen_rate.setter
    def snowflake_gen_rate(self, rate: int):
        """
        Sets the snowflake generation rate. The rate is equal to the average number of snowflakes per minute that
        are generated at the top edge of the frame. I.e., the number of snowflakes per minute when wind_speed == 0.

        Args:
            snowflakes_per_minute (int): The snowflake generation rate.
        """
        self._snowflakes_gen_rate = rate

        snowflakes_per_update = self._snowflakes_gen_rate/60 * self.dt
        self._snowflake_chance = snowflakes_per_update / self.WIDTH

    @property
    def fall_speed(self) -> float:
        """
        Gets the fall speed of the snowflakes. Units are pixels per 1/60 seconds.

        Returns:
            float: The fall speed of the snowflakes.
        """
        return self._fall_speed * AnimSnowflake.DEFAULT_FRAMERATE/self.framerate
    
    @fall_speed.setter
    def fall_speed(self, speed: float):
        """
        Sets the fall speed of the snowflakes. Units are pixels per 1/60 seconds.

        Args:
            speed (float): The fall speed of the snowflakes.
        """
        self._fall_speed = max(speed, AnimSnowflake.MIN_FALL_SPEED)

    @property
    def wind_speed(self) -> float:
        """
        Gets the wind speed. Units are pixels per 1/60 seconds.

        Returns:
            float: The wind speed.
        """
        return self._wind_speed * AnimSnowflake.DEFAULT_FRAMERATE/self.framerate
    
    @wind_speed.setter
    def wind_speed(self, speed: float):
        """
        Sets the wind speed. Units are pixels per 1/60 seconds.

        Args:
            speed (float): The wind speed.
        """
        self._wind_speed = speed