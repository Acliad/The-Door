from abc import ABC, abstractmethod
from numpy import ndarray
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

    def __init__(self, framerate):
        self.framerate = framerate
        self.current_frame = None

    @abstractmethod
    def update(self) -> ndarray | None:
        """
        Updates the frame.

        This method should be implemented by subclasses to update the frame's state. This method relies on the caller
        to call at the specified frame rate to correctly animate the frame.

        Returns:
            ndarray: The updated frame.
        """
        pass

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
        self._framerate = framerate
        self._dt = 1 / framerate

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
        self._dt = dt
        self._framerate = 1 / dt