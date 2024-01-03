from frames.framers.framer import Framer
from PIL import Image
import numpy as np
import random
import bisect
import time
import colorsys
from frames.utils import place_in
from typing import Callable, Sequence
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
    
class AnimSnowflake(Framer):
    DEFAULT_FRAMERATE = 60
    MAX_WIND_INTENSITY = 10
    MIN_FALL_SPEED = 0.05

    def __init__(self, 
                 gen_rate:float = 1000, 
                 interpolate:bool = False, 
                 trail_factor:float = 0.0, 
                 fall_speed:float = 1.0, 
                 wind_speed:float = 0.0, 
                 wind_step:float = 0.0001,
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
                ):
        """
        Initializes a new instance of the AnimSnowflake class.
        """
        super().__init__(AnimSnowflake.DEFAULT_FRAMERATE)
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
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

    def update(self):
        """
        Updates the snowflake matrix by randomly generating new snowflakes and shifting existing snowflakes down by 
        their speed.
        """
        self.matrix = (self.matrix * self.trail_factor).astype(np.uint8)

        for pos in self._get_new_snowflake_positions():
            self.add_snowflake(pos[0], pos[1])

        start_time = time.time()
        if self.storm_factor:
            simplex_storm_intensity = opensimplex.noise2(self.storm_pos, self._simplex_storm_idx) + 1
            self.storm_intensity = self.storm_factor * simplex_storm_intensity
            self.storm_pos += self.storm_step
        else:
            self.storm_intensity = 1.0

        simplex_wind_speed = opensimplex.noise2(self.wind_pos, self._simplex_wind_speed_idx)
        self.wind_speed = self.storm_intensity * self.wind_intensity * simplex_wind_speed
        # self.wind_speed += opensimplex.noise2(self.wind_pos*200, 100) * 0.5 * self.wind_speed
        self.wind_pos += self.wind_step
        for snowflake in self.snowflakes:
            # NOTE: Since snowflakes are sorted by size, the larger ones should be drawn on top of the smaller ones
            snowflake.y += snowflake.speed_y
            snowflake.x += self.wind_speed*snowflake.speed_x
            x = snowflake.x if self.interpolate else round(snowflake.x)
            y = snowflake.y if self.interpolate else round(snowflake.y)
            place_in(self.matrix, snowflake.matrix, y, x, transparent_threshold=5)

        end_time = time.time()
        if self.snowflakes:
            time_per_snowflake = (end_time - start_time) / len(self.snowflakes) * 1000
            time_all_snowflakes = (end_time - start_time) * 1000
            # Track the top 3 max draw times
            self.max_draw_time[0] = round(time_all_snowflakes, 2) if time_all_snowflakes > self.max_draw_time[0] else round(self.max_draw_time[0], 2)
            self.max_draw_time.sort()
            alpha = 0.995
            self.avg_draw_time = self.avg_draw_time * alpha + time_all_snowflakes * (1-alpha)
            print(f"Draw time: {time_per_snowflake:.2f} ms")
            print(f"Total draw time: {time_all_snowflakes:.2f} ms")
            print(f"Avg draw time: {self.avg_draw_time:.2f} ms")
            print(f"Max draw time: {self.max_draw_time} ms")
        
        print(len(self.snowflakes))
        print(f"Wind speed: {self.wind_speed:.2f}")
        print(f"Storm intensity: {self.storm_intensity:.2f}")
        # Remove snowflakes that have fallen off the bottom of the matrix
        self.snowflakes = [snowflake for snowflake in self.snowflakes if self.in_frame(snowflake)]
        return self.matrix
    
    def in_frame(self, snowflake: Snowflake) -> bool:
        """
        Checks if the snowflake is in bounds of the frame such that any part of it will be displayed.

        Args:
            snowflake (Snowflake): The snowflake to check.
            x (float): The x-coordinate of the snowflake's position.
            y (float): The y-coordinate of the snowflake's position.

        Returns:
            bool: True if the snowflake is in bounds of the matrix, False otherwise.
        """
        size = snowflake.size
        x = snowflake.x
        y = snowflake.y
        return y + size > 0 and y < self.HEIGHT and x + size > 0 and x < self.WIDTH
    
    def add_snowflake(self, x:float, y:float):
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

    def reset(self):
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

        vertical_chances = np.random.rand(self.HEIGHT-1) # -1 because the top edge is already covered by horizontal
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