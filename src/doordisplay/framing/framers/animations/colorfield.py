from framing.framers.framer import Framer
from typing import Sequence, Callable
from dataclasses import dataclass
import numpy as np
import opensimplex # NOTE: Installing numba will increase performance of noise generation
from time import time

# ------------------------------------------
# Field maps
# ------------------------------------------
"""
Field maps are functions that take x, y, and t as input and return a 2D array of values. These values are used to
generate the color field. The field maps can be used to generate different types of fields, such as simplex noise or
sinusoidal fields.
"""
def simplex_field(x:np.ndarray, y:np.ndarray, t:float) -> np.ndarray:
    """Generates a field of simplex noise values.

    Args:
        x (np.ndarray): x-coordinates of the field.
        y (np.ndarray): y-coordinates of the field.
        t (float): current time parameter.

    Returns:
        np.ndarray: 2D array of simplex noise values.
    """
    noise = opensimplex.noise3array(np.array([t]), x, y)
    # simplex noise has the range [-1, 1], normalize to [0, 1]:
    noise = (noise + 1) * 0.5
    return noise.squeeze() # Return value should be a len(y) x len(x) array, so squeeze the extra dimension

def sin_field(x:np.ndarray, y:np.ndarray, t:float) -> np.ndarray:
    """Generates a field of sinusoidal inspired values. The field (scaling omitted) is created as:

        sin(x) * cos(t) + cos(y) * sin(t)

    Args:
        x (np.ndarray): x-coordinates of the field.
        y (np.ndarray): y-coordinates of the field.
        t (float): current time parameter.

    Returns:
        np.ndarray: 2D array of sinusoidal values.
    """
    # Create the sin input field
    x = x / len(x) * 2 * np.pi
    y = y / len(x) * 2 * np.pi

    # Create the sin field. Divide by 2 since these will be added together
    sin_x = np.sin(x) * np.cos(t) * 0.5
    sin_y = np.cos(y) * np.sin(t) * 0.5

    field = sin_x[np.newaxis, :] + sin_y[:, np.newaxis]
    # Normalize the field to be in the range [0, 1]
    return field * 0.5 + 0.5

# ------------------------------------------
# Value maps
# ------------------------------------------
"""
Value maps are functions that take a field map function as input and return a new function. The output of this new
function is the same as the output of the field map, but with the values remapped using a function like sin or sigmoid.

The remapping function is applied to each value in the output of the field map. This can be used to modify the
distribution of values in the field map, for example to make them follow a sinusoidal or sigmoid distribution.

These functions assume the field map returns values in the range [0, 1] and will remap the output to the same range. The
behavior is undefined if the field map returns values outside this range.
"""

def sin_value_map(
        field_map:Callable[[np.ndarray, np.ndarray, float], np.ndarray]
        ) -> Callable[[np.ndarray, np.ndarray, float], np.ndarray]:
    """Generates a function map based on the sin function.

    Args:
        field_map (Callable[[np.ndarray, np.ndarray, float], np.ndarray]): The field map function to use.

    Returns:
        Callable[[np.ndarray, np.ndarray, float], np.ndarray]: The new field map function with the sigmoid applied.
    """
    def value_map(x:np.ndarray, y:np.ndarray, t:float) -> np.ndarray:
        values = field_map(x, y, t)
        # Need to modify the values to be in the input range of sin
        values = (values * 2 - 1) * np.pi
        return np.sin(values) * 0.5 + 0.5 # Shift the sin values to be in the range [0, 1]
    return value_map

def sigmoid_value_map(
        field_map:Callable[[np.ndarray, np.ndarray, float], np.ndarray],
        a:float=5
        ) -> Callable[[np.ndarray, np.ndarray, float], np.ndarray]:
    """Generates a function map based on a sigmoid function. Specifically, the function is 1 / (1 + exp(-a * values)).

    Args:
        field_map (Callable[[np.ndarray, np.ndarray, float], np.ndarray]): The field map function to use.

    Returns:
        Callable[[np.ndarray, np.ndarray, float], np.ndarray]: The new field map function with the sigmoid applied.
    """
    def value_map(x:np.ndarray, y:np.ndarray, t:float) -> np.ndarray:
        a = value_map.a # Get the method's a value
        values = field_map(x, y, t)
        # Remap the values to be in the range [-1, 1]
        values = values * 2 - 1
        return 1 / (1 + np.exp(-a * values))
    # Set the a value to the method
    value_map.a = a
    return value_map

def tan_value_map(
        field_map:Callable[[np.ndarray, np.ndarray, float], np.ndarray],
        a:float = 1
        ) -> Callable[[np.ndarray, np.ndarray, float], np.ndarray]:
    """Generates a function map where the output values are remapped using the tan function. This tends to produce a
    distribution of values that are more evenly distributed around the center (0). The tan function is tan(a * values).
    Thus, the value a can be used to control the steepness of the curve. a is clipped between 0 and pi/2.

    Args:
        field_map (Callable[[np.ndarray, np.ndarray, float], np.ndarray]): the field map function to use.

    Returns:
        Callable[[np.ndarray, np.ndarray, float], np.ndarray]: The new field map function with the tan applied.
    """
    def value_map(x:np.ndarray, y:np.ndarray, t:float) -> np.ndarray:
        a = value_map.a # Get the method's a value
        # Create a "static" value a
        values = field_map(x, y, t)
        # Remap the values to be in the range [-1, 1]
        values = values * 2 - 1
        a = np.clip(a, 0, np.pi/2)
        # Calculate the scaler to use such that tan(a) is in the range [-1, 1]
        scaler = 1 / np.tan(a)
        return np.tan(a * values) * scaler * 0.5 + 0.5 # Shift the tan values to be in the range [0, 1]
    # Set the a value to the method
    value_map.a = a
    return value_map

class ColorField(Framer):
    """
    A class representing a Color Field animation framer.

    TODO: 
        - Currently, it's assume that the position space is continuous and can be represented by two 1D arrays of x and
          y coordinates. Would it be better to have a 2D matrix of x, y coordinates so each pixel can have its own
          position?
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
                 field_function:Callable[[np.ndarray, np.ndarray, float], np.ndarray],
                 zoom_factor:float, 
                 temporal_speed:float, 
                 spatial_speed:float=0,
                 spatial_type:str="meander",
                 meander_speed:float=0.1,
                 color_map:tuple[tuple]=_DEFAULT_COLOR_MAP
                 ) -> None:
            """
            Initialize the Color Field animation with the given parameters.

            Args:
                field_function (function): The function to use for generating the color field. 
                    This function has two parameters:
                        - x (np.ndarray): A length WIDTH array of x positions along the width of the matrix.
                        - y (np.ndarray): A length HEIGHT array of y positions along the height of the matrix.
                        - t (float): The time parameter.
                    It returns a HEIGHTxWIDTH matrix of values in the range [0, 1].
                zoom_factor (float): The zoom factor for the animation.
                temporal_speed (float): The speed of the temporal animation.
                spatial_speed (float, optional): The speed of the spatial animation. Defaults to 0.
                spatial_type (str, optional): The type of spatial animation. Defaults to "meander".
                meander_speed (float, optional): The speed of the meander animation. Defaults to 0.1.
                color_map (tuple[tuple], optional): The color map for the animation. Defaults to _DEFAULT_COLOR_MAP.
            """
            super().__init__()
            self.field_function = field_function
            self._position_scaler = 1/zoom_factor
            self.temporal_speed = temporal_speed
            self.spatial_speed = spatial_speed
            self.meander_speed = meander_speed
            self.spatial_type = spatial_type
            self.color_map = color_map

            # Reset will initialize self.matrix and self._positions
            self._positions:ColorField.Positions = None
            self.reset()

    def update(self) -> tuple[np.ndarray, float]:
        """
        Updates the animation frame.

        Returns:
            tuple[np.ndarray, float]: The updated animation frame and the time elapsed.
        """
        self.matrix = self._value_to_color(self.field_function(self._positions.x, self._positions.y, self._positions.t))

        # Update the positions
        position_delta = self.spatial_speed * self.dt
        match self.spatial_type:
            case "meander":
                dx = opensimplex.noise2(self._positions.t * self.meander_speed, 0) * position_delta
                dy = opensimplex.noise2(self._positions.t * self.meander_speed, 
                                        ColorField._MEANDER_SIMPLEX_SPACING) * position_delta
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

        self._positions.t += self.dt * self.temporal_speed
        
        return super().update()

    def reset(self) -> None:
        """
        Resets the animation to its initial state.
        """
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self._positions:ColorField.Positions = ColorField.Positions(
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
