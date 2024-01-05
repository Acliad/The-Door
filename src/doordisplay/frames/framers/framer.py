from abc import ABC, abstractmethod
from numpy import ndarray
from typing import TypedDict
from ledmat import LEDMatrix

class Framer(ABC):
    """
    Abstract base class for frames in a frame player.

    Attributes:
        framerate (int): The frame rate of the frame player.

    Methods:
        update(): Updates the frame.
        reset(): Resets the frame to its initial state.
    """
    WIDTH = LEDMatrix.WIDTH
    HEIGHT = LEDMatrix.HEIGHT
    DEFAULT_FRAMERATE = 60

    def __init__(self):
        self.framerate = Framer.DEFAULT_FRAMERATE # NOTE: Also sets self.dt
        self.matrix = None

    @abstractmethod
    def update(self) -> tuple[ndarray, float]:
        """
        Updates the frame.

        This method should be implemented by subclasses to update the frame's state. This method relies on the caller
        to call at the specified frame rate to correctly animate the frame.

        Returns:
            tuple[ndarray, float]: The updated frame and the frame duration.
        """
        return (self.matrix, self.dt)

    @abstractmethod
    def reset(self):
        """
        Resets the frame to its initial state.

        This method should be implemented by subclasses to reset the frame to its initial state.
        """
        pass

    @property
    def framerate(self) -> int:
        """
        Gets the frame rate of the frame player.

        Returns:
            int: The frame rate of the frame player.
        """
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate: int):
        """
        Sets the frame rate of the frame player.

        Args:
            framerate (int): The frame rate of the frame player.
        """
        if framerate:
            self._framerate = framerate
            self._dt = 1 / framerate
        else:
            self._framerate = 0
            self._dt = 0

    @property
    def dt(self) -> float:
        """
        Gets the time between frames.

        Returns:
            float: The time between frames.
        """
        return self._dt
    
    @dt.setter
    def dt(self, dt: float):
        """
        Sets the time between frames.

        Args:
            dt (float): The time between frames.
        """
        if dt:
            self._dt = dt
            self._framerate = 1 / dt
        else:
            self._dt = 0
            self._framerate = 0