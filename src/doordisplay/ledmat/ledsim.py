
import pygame
from ledmat import LEDMatrix
import numpy as np
from time import sleep, time
from frames import StaticFramer, GifFramer, FramePlayer, AnimRainbow, AnimSnowflake


class LEDSimulator(LEDMatrix):
    DEFAULT_SCALE = 4.0
    DEFAULT_MAX_FPS = 60

    def __init__(self, serial_port=None, scale=DEFAULT_SCALE, **kwargs):
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
        print(f"Window size: {self.width}x{self.height}")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        self.frame = np.zeros((LEDMatrix.WIDTH, LEDMatrix.HEIGHT, 3), dtype=np.uint8)

        
class LEDSerialPortSimulator:
    def __init__(self, led_simulator: LEDSimulator) -> None:
        self.led_simulator = led_simulator

    def write(self, pixel_data) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
        if len(pixel_data) == 1 and pixel_data == self.led_simulator.SOF_FLAG:
            return

        self.led_simulator.screen.fill((0, 0, 0))  # Clear the screen

        # Convert the given pixel data to a matrix of pixel data for the pygame window
        self.led_simulator.frame[self.led_simulator.idx_map[:, 1], self.led_simulator.idx_map[:, 0], self.led_simulator.idx_map[:, 2]] = pixel_data

        # Create a surface from the frame and scale it to the size of the window
        surface = pygame.surfarray.make_surface(self.led_simulator.frame)
        surface = pygame.transform.scale(surface, (self.led_simulator.width, self.led_simulator.height))

        # Draw the surface to the screen
        self.led_simulator.screen.blit(surface, (0, 0))
        pygame.display.flip()

        self.led_simulator.clock.tick()  # Limit the frame rate to match the Teensy's max frame rate

if __name__ == "__main__":
    # Usage example
    upscale_factor = 6

    pixel_data = np.zeros((LEDMatrix.WIDTH*LEDMatrix.HEIGHT*3 - 3*28), dtype=np.uint8)
    pixel_data[0:LEDMatrix.HEIGHT*3:3] = 255
    pixel_data[1:LEDMatrix.HEIGHT*3+1:3] = 255
    pixel_data[LEDMatrix.HEIGHT*3:LEDMatrix.HEIGHT*3*2:3] = 255
    pixel_data[LEDMatrix.HEIGHT*3*2:LEDMatrix.HEIGHT*3*3:3] = 255
    pixel_data[LEDMatrix.HEIGHT*3*3:LEDMatrix.HEIGHT*3*4:3] = 255
    pixel_data[LEDMatrix.HEIGHT*3*4:LEDMatrix.HEIGHT*3*5:3] = 255

    matrix = np.zeros((LEDMatrix.HEIGHT, LEDMatrix.WIDTH, 3), dtype=np.uint8)
    matrix[:, :, 0] = 255

    img_path = r"/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/doordisplay/examples/data/Cats.png"
    img_framer = StaticFramer(img_path)

    gif_path = r"/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/doordisplay/examples/data/clickyfloat.gif"
    gif_framer = GifFramer(gif_path)

    rainbow_framer = AnimRainbow()
    snow_framer = AnimSnowflake()

    display = LEDSimulator(scale=upscale_factor, brightness=1.0, gamma=1.0, contrast=1.0)
    player = FramePlayer(display, gif_framer)

    try:
        player.play_blocking()
    except KeyboardInterrupt:
        print("Exiting...")
        pygame.quit()
