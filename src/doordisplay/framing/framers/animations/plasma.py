from framing.framers.framer import Framer
from typing import Sequence
from dataclasses import dataclass
import numpy as np
import opensimplex # NOTE: Installing numba will increase performance of noise generation
from time import time

class Plasma(Framer):
    """
    A class representing a plasma animation framer.

    TODO: 
        - Add a way to non-linearly map the noise value to the color segments.

    Attributes:
        zoom_factor (float): The zoom factor of the noise map.
        temporal_speed (float): The speed of the animation in the temporal dimension.
        spatial_speed (float): The speed of the animation in the spatial dimension.
        spatial_type (str): The type of spatial movement in the animation.
            - "meander": Meandering movement.
            - "linear_x": Linear movement in the x-direction.
            - "linear_y": Linear movement in the y-direction.
            - "linear_xy": Linear movement in both the x and y directions.
            - "linear_xor": Linear movement in the x and y directions with opposite signs.
        meander_speed (float): The speed of meandering movement in the animation.
        color_map (tuple[tuple]): The color map used for mapping noise values to colors.

    Methods:
        update(): Updates the animation frame.
        reset(): Resets the animation to its initial state.
    """

    _DEFAULT_COLOR_MAP = ((255, 0, 0), (245, 245, 66), (0, 0, 255)) # Red, Yellow, Blue
# The value to use for the spacing between x and y simplex coordinates when using the random spatial type
    _MEANDER_SIMPLEX_SPACING = 10
    
    @dataclass
    class Positions:
        x:np.ndarray
        y:np.ndarray
        t:float

    def __init__(self, 
                     zoom_factor:float, 
                     temporal_speed:float, 
                     spatial_speed:float=0,
                     spatial_type:str="meander",
                     meander_speed:float=0.1,
                     color_map:tuple[tuple]=_DEFAULT_COLOR_MAP
                     ) -> None:
            """
            Initialize the Plasma animation with the given parameters.

            Args:
                zoom_factor (float): The zoom factor for the animation.
                temporal_speed (float): The speed of the temporal animation.
                spatial_speed (float, optional): The speed of the spatial animation. Defaults to 0.
                spatial_type (str, optional): The type of spatial animation. Defaults to "meander".
                meander_speed (float, optional): The speed of the meander animation. Defaults to 0.1.
                color_map (tuple[tuple], optional): The color map for the animation. Defaults to _DEFAULT_COLOR_MAP.
            """
            super().__init__()
            self._position_scaler = 1/zoom_factor
            self.temporal_speed = temporal_speed
            self.spatial_speed = spatial_speed
            self.meander_speed = meander_speed
            self.spatial_type = spatial_type
            self.color_map = color_map

            # Reset will initialize self.matrix and self._positions
            self._positions:Plasma.Positions = None
            self.reset()

    def update(self) -> tuple[np.ndarray, float]:
        """
        Updates the animation frame.

        Returns:
            tuple[np.ndarray, float]: The updated animation frame and the time elapsed.
        """
        noise = opensimplex.noise3array(np.array([self._positions.t * self.temporal_speed]), 
                                        self._positions.x, 
                                        self._positions.y)

        # Convert the noise values to colors. Need to squeeze the matrix because noise3array() will return a 
        # HEIGHT x WIDTH x 1 ndarray, _value_to_color() expects an M x N array. sin values are shifted to a 0-1 range.
        self.matrix = self._value_to_color(np.sin(noise.squeeze() * np.pi)*0.5 + 0.5)

        # Update the positions
        position_delta = self.spatial_speed * self.dt
        match self.spatial_type:
            case "meander":
                dx = opensimplex.noise2(self._positions.t * self.meander_speed, 0) * position_delta
                dy = opensimplex.noise2(self._positions.t * self.meander_speed, 
                                        Plasma._MEANDER_SIMPLEX_SPACING) * position_delta
                self._positions.x += dx
                self._positions.y += dy
                pass
            case "linear_x":
                self._positions.x += position_delta
            case "linear_y":
                self._positions.y += position_delta
            case "linear_xy":
                self._positions.x += position_delta
                self._positions.y += position_delta
            case "linear_xor":
                self._positions.x -= position_delta
                self._positions.y += position_delta

        self._positions.t += self.dt
        
        return super().update()

    def reset(self) -> None:
        """
        Resets the animation to its initial state.
        """
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self._positions:Plasma.Positions = Plasma.Positions(
            x=np.arange(0, self.WIDTH, 1) * self._position_scaler,
            y=np.arange(0, self.HEIGHT, 1) * self._position_scaler,
            t=0
        )


    def _value_to_color(self, value: np.ndarray) -> np.ndarray:
        """
        Converts noise values to colors.

        Args:
            value (np.ndarray): The noise values.

        Returns:
            np.ndarray: The colors corresponding to the noise values.
        """
        num_colors = len(self.color_map)
        # NOTE: take the min to prevent index out of bounds
        first_color_indices = np.minimum(value * (num_colors - 1), num_colors - 2).astype(np.intc)
        next_color_index  = first_color_indices + 1

        value_spacing = 1 / (num_colors - 1)
        color_percentages = (value - first_color_indices * value_spacing) / value_spacing

        first_color = self.color_map[first_color_indices]
        next_color  = self.color_map[next_color_index]

        # Interpolate the colors
        # NOTE: color_percentages is a HEIGHT x WIDTH array, so we need to broadcast it to HEIGHT x WIDTH x 3
        color_percentages = color_percentages[:, :, np.newaxis]

        return np.round(first_color * (1 - color_percentages) + next_color * color_percentages).astype(np.uint8)

    @property
    def zoom_factor(self) -> float:
        """
        The zoom factor of the animation.

        Returns:
            float: The zoom factor.
        """
        return 1/self._position_scaler
    
    @zoom_factor.setter
    def zoom_factor(self, value: float) -> None:
        """
        Sets the zoom factor of the animation.

        Args:
            value (float): The zoom factor.
        """
        old_scaler = self._position_scaler
        self._position_scaler = 1/value
        # Rescale the positions
        self._positions[0] = self._positions[0] / old_scaler * self._position_scaler # x-coords
        self._positions[1] = self._positions[1] / old_scaler * self._position_scaler # y-coords

    @property
    def color_map(self) -> np.ndarray[np.ndarray]:
        """
        The color map used for mapping noise values to colors.

        Returns:
            np.ndarray[np.ndarray]: The color map.
        """
        return self._color_map
    
    @color_map.setter
    def color_map(self, value: Sequence[Sequence]) -> None:
        """
        Sets the color map used for mapping noise values to colors.

        Args:
            value (Sequence[Sequence]): The color map.
        """
        if len(value) < 2:
            raise ValueError("Color map must have at least 2 colors.")
        self._color_map = [np.array(color) for color in value]
        self._color_map = np.array(self._color_map, dtype=np.uint8)
