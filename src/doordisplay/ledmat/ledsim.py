
import pygame
from ledmat import LEDMatrix
import numpy as np
from time import sleep, time
from frames import StaticFramer, GifFramer, FramePlayer, AnimRainbow, AnimSnowflake, Framer


class LEDSimulator(LEDMatrix):
    """
    A class representing a simulator for an LED matrix display.

    Attributes:
        DEFAULT_SCALE (float): The default scale factor for the simulator.
        DEFAULT_MAX_FPS (int): The default maximum frames per second for the simulator.

    Args:
        serial_port (str, optional): The serial port to connect to the Teensy. Defaults to None.
        scale (float, optional): The scale factor for the simulator. Defaults to DEFAULT_SCALE.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Methods:
        __init__(self, serial_port=None, scale=DEFAULT_SCALE, **kwargs): Initializes the LEDSimulator object.
    """

    DEFAULT_SCALE = 4.0
    DEFAULT_MAX_FPS = 60

    def __init__(self, serial_port=None, scale=DEFAULT_SCALE, **kwargs):
        """
        Initializes the LEDSimulator object.

        Args:
            serial_port (str, optional): NOTE: Not implemented. The serial port to connect to the Teensy. Defaults to 
            None. 
            scale (float, optional): The scale factor for the simulator. Defaults to DEFAULT_SCALE.
            **kwargs: Additional keyword arguments to be passed to the parent class:

                gamma (float, optional): The gamma value to use for the LED matrix. Defaults to 1.0.
                brightness (float, optional): The brightness scale to use for the LED matrix. Defaults to 1.0.
                contrast (float, optional): The contrast scale to use for the LED matrix. Defaults to 1.0.
        """
        # Check if gamma and brightness were passed in as keyword arguments and if not, set them to their default values
        gamma = kwargs.pop("gamma", 1.0)
        brightness = kwargs.pop("brightness", 1.0)

        # NOTE: serial_port is an empty list string now just to prevent LEDMatrix from trying to connect to a Teensy. I
        # think this class can be updated to run both the simulator and the Teensy at the same time, but that's a TODO
        serial_port = LEDSerialPortSimulator(self)
        super().__init__(serial_port=serial_port, gamma=gamma, brightness=brightness, **kwargs)
        pygame.init()
        
        self.scale = scale
        self.width = LEDMatrix.WIDTH * self.scale
        self.height = LEDMatrix.HEIGHT * self.scale
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.window_title = "The Door Simulator - FPS: {:.2f}"
        pygame.display.set_caption(self.window_title.format(0))
        self.clock = pygame.time.Clock()
        
        self.frame = np.zeros((LEDMatrix.WIDTH, LEDMatrix.HEIGHT, 3), dtype=np.uint8)

    def update(self):
        """
        Update the LED matrix display.

        This method handles the updating of the pygame window and the frame rate limitation.
        It also handles events such as quitting the program and resizing the window. It should be called in a main loop.

        Parameters:
            None

        Returns:
            None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                new_height = event.h
                new_width = int(new_height / LEDMatrix.HEIGHT * LEDMatrix.WIDTH)

                self.width = new_width
                self.height = new_height
                self.scale = new_width / LEDMatrix.WIDTH
                self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

        self.clock.tick(self.DEFAULT_MAX_FPS)

    def __del__(self):
        pygame.quit()

        
class LEDSerialPortSimulator:
    """
    Simulates a serial port for LED display communication.

    Args:
        led_simulator (LEDSimulator): The LED simulator object.

    Attributes:
        led_simulator (LEDSimulator): The LED simulator object.

    Methods:
        write(pixel_data): Writes pixel data to the LED simulator.
    """

    def __init__(self, led_simulator: LEDSimulator) -> None:
        self.led_simulator = led_simulator

    def write(self, pixel_data) -> int:
        """
        Writes pixel data to the LED simulator.

        Args:
            pixel_data: The pixel data to be written.

        Returns:
            None
        """
        if len(pixel_data) == 1 and pixel_data == self.led_simulator.SOF_FLAG:
            # write() normally returns the number of bytes written, which would be one in this case.
            return 1

        self.led_simulator.screen.fill((0, 0, 0))  # Clear the screen

        # Convert the given pixel data to a matrix of pixel data for the pygame window
        self.led_simulator.frame[self.led_simulator.idx_map[:, 1], 
                                 self.led_simulator.idx_map[:, 0], 
                                 self.led_simulator.idx_map[:, 2]] = pixel_data

        # Create a surface from the frame and scale it to the size of the window
        surface = pygame.surfarray.make_surface(self.led_simulator.frame)
        surface = pygame.transform.scale(surface, (self.led_simulator.width, self.led_simulator.height))

        # Draw the surface to the screen
        self.led_simulator.screen.blit(surface, (0, 0))
        pygame.display.flip()

        # Add an FPS counter to the window title
        pygame.display.set_caption(self.led_simulator.window_title.format(self.led_simulator.clock.get_fps()))

        return len(pixel_data)



def sim_frame(frame: Framer, scale=6, brightness=1.0, gamma=1.0, contrast=1.0):
    """
    Simple debug helper that simulates a frame by displaying it in a pygame window. This function is blocking. 

    Args:
        frame (Framer): The frame to be simulated.
    """
    # Initialize the LEDMatrix
    led_matrix = LEDSimulator(scale=scale, brightness=brightness, gamma=gamma, contrast=contrast)
    player = FramePlayer(led_matrix, frame)

    player.play()
    try:
        while True:
            player.update()
            led_matrix.update()
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    # Usage example

    img_path = r"/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/doordisplay/examples/data/Cats.png"
    img_framer = StaticFramer(img_path)

    gif_path = r"/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/doordisplay/examples/data/clickyfloat.gif"
    gif_framer = GifFramer(gif_path)

    rainbow_framer = AnimRainbow()
    snow_framer = AnimSnowflake()

    sim_frame(snow_framer)
