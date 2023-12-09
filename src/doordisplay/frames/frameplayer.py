import time
from ledmat.ledmat import LEDMatrix
from frames.framers.framer import Framer
from serial import Serial
import threading
from enum import Enum

class FramePlayer(LEDMatrix):
    """
    A class that plays frames on a LED matrix.

    Attributes:
        framer (framer): The current framer to be played.
        framerate (int): The framerate of the frame.
        frame_interval (float): The time interval between each frame.
        is_playing (bool): Indicates whether the frame player is currently playing.

    Methods:
        set_framer(framer): Sets the current framer to be played.
        play(): Starts playing the frames in a separate thread.
        stop(): Stops playing the frames.
    """
    MAX_FPS = 60 # Each frame takes 15.9 ms to shift out to the LEDs, so 60 FPS leaves very little buffer

    class PlayerState(Enum):
        PLAYING = 0
        PAUSED = 1
        STOPPED = 2

    def __init__(self, framer, **kwargs):
        # Initialize the LEDMatrix
        super().__init__(**kwargs)
        self.framer = framer
        self.framerate = framer.framerate
        # A framerate of 0 indicates a static frame
        self.frame_interval = 1 / self.framerate if self.framerate else -1
        self.playing_state = FramePlayer.PlayerState.STOPPED

    def set_framer(self, framer: Framer):
        """
        Sets the current framer to be played.

        Args:
            framer (Framer): The framer to be set.
        """
        self.framer = framer
        self.framerate = framer.framerate
        # A framerate of 0 indicates a static frame
        self.frame_interval = 1 / self.framerate if self.framerate else -1

    def play(self):
        """
        Starts playing the frames in a separate thread.
        """
        # If the framrate is 0, it's a static frame so just display it and don't start a thread
        if self.framerate == 0:
            self.send_matrix(self.framer.update())
        else:
            self.playing_state = FramePlayer.PlayerState.PLAYING
            threading.Thread(target=self._play_loop).start()

    def stop(self):
        """
        Stops playing the frames.
        """
        self.playing_state = FramePlayer.PlayerState.STOPPED
        self.framer.reset()

    def pause(self):
        """
        Pauses the frame player.
        """
        self.is_playing = False

    def _play_loop(self):
        """
        The internal loop that plays the frames.
        """
        while True:
            if self.playing_state == FramePlayer.PlayerState.PLAYING:
                start_time = time.time()
                updated_frame = self.framer.update()
                if updated_frame is not None:
                    self.send_matrix(updated_frame)  
                    elapsed_time = time.time() - start_time
                    if elapsed_time < self.frame_interval:
                        time.sleep(self.frame_interval - elapsed_time)
                else:
                    # A None value means the animation is done
                    self.stop()
            if self.playing_state == FramePlayer.PlayerState.STOPPED:
                break

            # Do nothing if the player is paused

    @property
    def framerate(self) -> float:
        """
        The framerate of the frame player.
        """
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate: float):
        self._framerate = min(framerate, FramePlayer.MAX_FPS)
        self.frame_interval = 1 / self.framerate if self.framerate else -1