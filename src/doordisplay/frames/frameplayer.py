import time
from ledmat import LEDMatrix
from frames.framers.framer import Framer
from serial import Serial
import asyncio
from enum import Enum

class FramePlayer():
    """
    A class that plays frames on a LED matrix.

    Attributes:
        led_matrix (LEDMatrix): The LED matrix to play the frames on.
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

    def __init__(self, led_matrix:LEDMatrix, framer:Framer = None):
        # Initialize the LEDMatrix
        self.led_matrix = led_matrix
        self.set_framer(framer)
        self.playing_state = FramePlayer.PlayerState.STOPPED
        self.last_update_time = 0

    def set_framer(self, framer: Framer):
        """
        Sets the current framer to be played.

        Args:
            framer (Framer): The framer to be set.
        """
        if framer:
            self.framer = framer
            self.framerate = framer.framerate
            # A framerate of 0 indicates a static frame
            self.frame_interval = 1 / self.framerate if self.framerate else -1
        else:
            self.framer = None
            self.framerate = 0
            self.frame_interval = -1

    def play(self):
        """
        Start playing the frames. This function just updates the interal state, user must call update() periodically to
        actually play the frames.

        Raises:
            ValueError: If no framer is set.
        """
        if self.framer is None:
            raise ValueError("No framer set")
        
        self.playing_state = FramePlayer.PlayerState.PLAYING

    def play_blocking(self):
        """
        Start playing the frames. This function blocks until the animation is done.
        NOTE: Some animations never end, so this function could block forever. This function is mostly intended for
        testing purposes.

        Raises:
            ValueError: If no framer is set.
        """
        self.play()
        
        while self.playing_state != FramePlayer.PlayerState.STOPPED:
            self.update()

    async def play_async(self):
        """
        Start playing the frames. This function is asynchronous and should be called from an ascynio context. The user
        does not need to call update() if using this function.
        """
        self.play()
        
        while self.playing_state != FramePlayer.PlayerState.STOPPED:
            self.update()
            await asyncio.sleep(0)

    def stop(self):
        """
        Stops playing the frames.
        """
        self.playing_state = FramePlayer.PlayerState.STOPPED
        self.last_update_time = 0
        self.framer.reset()

    def pause(self):
        """
        Pauses the frame player.
        """
        self.is_playing = False

    def update(self):
        """
        Updates the current frame of the frame player if the frame interval has elapsed. This function should be called
        periodically to play the frames. Returns the estimated time (in seconds) until update() should be called again. 
        A negative value indicates that the frame player is stopped or paused.

        Raises:
            ValueError: If no framer is set.

        Returns:
            float: The estimated time (in seconds) until update() should be called again. A negative value indicates 
            that the frame player is stopped or paused.
        """
        if self.framer is None:
            raise ValueError("No framer set")

        # Do nothing if the player is stopped or paused
        if FramePlayer.PlayerState.PLAYING:
            # If the framerate is 0, it's a static frame so just display it and stop
            if self.framerate == 0:
                self.led_matrix.send_matrix(self.framer.update())
                self.stop()
            else:
                current_time = time.time()
                elapsed_time = current_time - self.last_update_time
                if elapsed_time >= self.frame_interval:
                    # NOTE: This assumes that each frame takes about the same amount of time to update and send.
                    # Putting last_update_time before the actual update means that each interval is shortened by the
                    # time it takes to update and send the frame, but then the frame continues to display until the
                    # matrix is updated which should, in theory, mean each frame is displayed for frame_interval
                    # time. Putting it after the update means that each interval is lengthened by the time it takes
                    # to update and send the frame.
                    self.last_update_time = current_time
                    updated_frame = self.framer.update()
                    if updated_frame is not None:
                        self.led_matrix.send_matrix(updated_frame)
                        return time.time() - self.last_update_time
                    else:
                        # A None value means the animation is done
                        self.stop()

            # If we reached here, the frame player is stopped or paused
            return -1


    @property
    def framerate(self) -> float:
        """
        The framerate of the frame player.
        """
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate: float):
        """
        Set the framerate of the frame player.

        Args:
            framerate (float): The desired framerate.

        """
        self._framerate = min(framerate, FramePlayer.MAX_FPS)
        self.frame_interval = 1 / self.framerate if self.framerate else -1
