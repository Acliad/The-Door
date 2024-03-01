from framing.framers.framer import Framer
from typing import Sequence
from dataclasses import dataclass
import numpy as np
import random
import opensimplex # NOTE: Installing numba will increase performance of noise generation
from time import time

class SimplexMap(Framer):
    _DEFAULT_COLOR_MAP = ((255, 0, 0), (245, 245, 66), (0, 0, 255)) # Red, Yellow, Blue
    
    @dataclass
    class Positions:
        x:np.ndarray
        y:np.ndarray
        t:np.ndarray

    def __init__(self, zoom_factor:float, temporal_speed:float, color_map:tuple[tuple]=_DEFAULT_COLOR_MAP) -> None:
        super().__init__()
        self._position_scaler = 1/zoom_factor
        self.temporal_speed = temporal_speed
        self.color_map = color_map

        # Reset will initialize self.matrix and self._positions
        self.reset()

    def update(self) -> tuple[np.ndarray, float]:
        start_time = time()
        # Get the noise values
        noise = opensimplex.noise3array(self._positions.t, self._positions.x, self._positions.y)
        noise_time = time() - start_time
        # Convert the noise values to colors. Need to squeeze the matrix because noise3array() will return a 
        # HEIGHT x WIDTH x 1 ndarray, _value_to_color() expects an M x N array. sin values are shifted to a 0-1 range.
        self.matrix = self._value_to_color(np.sin(noise.squeeze() * np.pi)*0.5 + 0.5)
        
        # Update the positions
        # TODO: Add a random element? Maybe a filtered random walk?
        # self._positions[0] += self.speed * self.dt
        # self._positions[1] += self.speed * self.dt * 1.5
        self._positions.t += self.temporal_speed * self.dt
        total_time = time() - start_time

        print(f"Time to generate noise (ms): {noise_time*1e3:.3f} ms")
        print(f"Time to update matrix (ms): {(total_time - noise_time)*1e3:.3f} ms")
        
        return super().update()

    def reset(self) -> None:
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self._positions:SimplexMap.Positions = SimplexMap.Positions(
            x=np.arange(0, self.WIDTH, 1) * self._position_scaler,
            y=np.arange(0, self.HEIGHT, 1) * self._position_scaler,
            t=np.ones(1)
        )


    def _value_to_color(self, value: np.ndarray) -> np.ndarray:
        num_colors = len(self.color_map)
        # NOTE: take the min to prevent index out of bounds
        first_color_indices = np.minimum(value * (num_colors - 1), num_colors - 2).astype(np.intc)
        next_color_index  = first_color_indices + 1

        # Calculate the percentage of the way between the two colors
        value_spacing = 1 / (num_colors - 1) # The spacing between each color
        color_percentages = (value - first_color_indices * value_spacing) / value_spacing

        # Get the colors
        first_color = self.color_map[first_color_indices]
        next_color  = self.color_map[next_color_index]

        # Interpolate the colors
        # NOTE: color_percentages is a HEIGHT x WIDTH array, so we need to broadcast it to HEIGHT x WIDTH x 3
        color_percentages = color_percentages[:, :, np.newaxis]
        # print(self.color_map)
        return np.round(first_color * (1 - color_percentages) + next_color * color_percentages).astype(np.uint8)

    @property
    def zoom_factor(self) -> float:
        return 1/self._position_scaler
    
    @zoom_factor.setter
    def zoom_factor(self, value: float) -> None:
        old_scaler = self._position_scaler
        self._position_scaler = 1/value
        # Rescale the positions
        self._positions[0] = self._positions[0] / old_scaler * self._position_scaler # x-coords
        self._positions[1] = self._positions[1] / old_scaler * self._position_scaler # y-coords

    @property
    def color_map(self) -> np.ndarray[np.ndarray]:
        return self._color_map
    
    @color_map.setter
    def color_map(self, value: Sequence[Sequence]) -> None:
        if len(value) < 2:
            raise ValueError("Color map must have at least 2 colors.")
        self._color_map = [np.array(color) for color in value]
        self._color_map = np.array(self._color_map, dtype=np.uint8) # Convert to a numpy array