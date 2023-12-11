# This file contains the code for communicating with the LED strip and mapping matrix data to the strip pixels. 
import numpy as np
import serial
import serial.tools.list_ports
from time import time

class TeensyNotFoundException(Exception):
    pass

class LEDMatrix:
    WIDTH = 50
    HEIGHT = 124
    RGB_ORDER = [1, 0, 2]
    # Array of row, col indices of pixels that should be blanked out.
    BLANK_PIXELS = [
                    # Door handle cutout
                              (62, 46), (62, 47), (62, 48), (62, 49), 
                    (63, 45), (63, 46), (63, 47), (63, 48), (63, 49), 
                    (64, 45), (64, 46), (64, 47), (64, 48), (64, 49), 
                    (65, 45), (65, 46), (65, 47), (65, 48), (65, 49), 
                    (66, 45), (66, 46), (66, 47), (66, 48), (66, 49), 
                              (67, 46), (67, 47), (67, 48), (67, 49),
                    ]
    NUM_BANKS = 13
    COLUMNS_PER_BANK = 4
    NUM_LEDS = WIDTH * HEIGHT - len(BLANK_PIXELS)
    # Must be sent to Teensy before the pixel data
    SOF_FLAG = bytes('*', 'utf-8')
    TEENSY_PID_VID = "16C0:0483"

    def __init__(self, serial_port: serial.Serial=None, brightness: float=0.25, contrast:float = 1.0, gamma: float=2.4):
        self.idx_map = LEDMatrix.generate_idx_map()
        self.serial_port = serial_port or LEDMatrix.get_teensy_serial()
        self._brightness = brightness
        self._contrast = contrast
        self._gamma = gamma
        self.gamma_lut = LEDMatrix.gen_gamma_lut(gamma)
        self.pixel_data = np.zeros((LEDMatrix.NUM_LEDS*3), dtype=np.uint8)

    def generate_idx_map() -> np.ndarray:
        """Generates an index map for mapping a 3D matrix to a 1D array of data. The returned array is of shape 
        (WIDTH*HEIGHT*3, 3) where the 1x3 array are the indices of the 3D matrix. The first index is the row, the
        second index is the column, and the third index is the color channel. 

        Returns:
            np.ndarray: An array of indices that flattens a 3D matrix into a 1D array of pixel data.
        """
        idx_map_len = LEDMatrix.NUM_LEDS * 3
        idx_map = np.zeros((idx_map_len, 3), dtype=np.intp)
        map_idx = 0 # This is confusing naming. This is the index of the idx_map array, not the index of the matrix
        for col in range(LEDMatrix.WIDTH):
            # LED strips are mounted with data starting at lower left of door, going up. There are 4 strips per bank,
            # so the "strip" as the teensy sees it will be 4 columns wide, meaning every even column starts at the
            # bottom of the matrix and every odd column starts at the top of the matrix.
            # Data Dir: ↑ ↓ ↑ ↓  ↑ ↓ ↑ ↓  ↑ ↓ ↑ ↓  ...  ↑ ↓ ↑ ↓
            #           ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...  ■ ■ ■ ■
            #           ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...  ■ ■ ■ ■
            #           ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...  ■ ■ ■ ■
            #           . . . .  . . . .  . . . .  ...  . . . .
            #           . . . .  . . . .  . . . .  ...  . . . .
            #           . . . .  . . . .  . . . .  ...  . . . .
            #           ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...  ■ ■ ■ ■
            #           ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...  ■ ■ ■ ■
            # Data Dir: ↑ ↓ ↑ x  ↑ ↓ ↑ x  ↑ ↓ ↑ x  ...  ↑ ↓ ↑ x
            # NOTE: Rows will be reversed for odd columns
            rows = range(LEDMatrix.HEIGHT-1, -1, -1) if col % 2 == 0 else range(LEDMatrix.HEIGHT)
            for row in rows:
                if (row, col) in LEDMatrix.BLANK_PIXELS:
                    continue
                idx_map[map_idx]   = [row, col, LEDMatrix.RGB_ORDER[0]]
                idx_map[map_idx+1] = [row, col, LEDMatrix.RGB_ORDER[1]]
                idx_map[map_idx+2] = [row, col, LEDMatrix.RGB_ORDER[2]]
                map_idx += 3
        
        return idx_map

    def map_matrix(self, matrix: np.ndarray) -> list:
        """Apply the index map to the matrix and return the 1D array of pixel data.

        Args:
            matrix (np.ndarray): array of shape (WIDTH, HEIGHT, 3) where the 3rd dimension is the RGB channels.

        Returns:
            list: list of pixel data to be sent to the LED strip.
        """
        return matrix[self.idx_map[:, 0], self.idx_map[:, 1], self.idx_map[:, 2]].tolist()
    
    def send_pixels(self, pixels: list | np.ndarray):
        """Send the pixel data to the teensy.

        Args:
            pixels (list | np.ndarray): 1D array of length NUM_LEDS*3 of pixel data to be sent to the LED strip.
        """
        # Apply the color correction
        self.pixel_data[:] = pixels
        pixel_data_corrected = self._apply_color_correction(self.pixel_data)

        self.serial_port.write(LEDMatrix.SOF_FLAG)
        self.serial_port.write(pixel_data_corrected)



    def send_matrix(self, matrix: np.ndarray):
        """Map the matrix to the LED strip and send the data to the teensy.

        Args:
            matrix (np.ndarray): array of shape (WIDTH, HEIGHT, 3) where the 3rd dimension is the RGB channels.
        """
        pixels = self.map_matrix(matrix)
        self.send_pixels(pixels)

    def refresh(self):
        """Refresh the LED matrix by resending the current pixel data. Used to update color correction.
        """
        self.send_pixels(self.pixel_data)

    def _apply_color_correction(self, pixel_data: np.ndarray) -> np.ndarray:
        """Adjust the color of the pixel_data by applying the contrast and gamma values.

        TODO: Add saturation adjustment

        Args:
            pixel_data (np.ndarray): 1D array of of pixel data.

        Returns:
            np.ndarray: The adjusted matrix.
        """
        # Apply the contrast
        corrected = self._contrast * (pixel_data - 255*0.5) + 255*0.5
        corrected = np.clip(corrected, 0, 255)
        # Apply the brightness
        corrected = corrected * self._brightness
        # Apply the gamma
        corrected = self.gamma_lut[corrected.round().astype(np.uint8)]
        return corrected.round().astype(np.uint8)

    @classmethod
    def get_teensy_serial(cls) -> serial.Serial:
        """Finds the serial port of the teensy and returns a serial.Serial object for communicating with it.

        Returns:
            serial.Serial: Serial object for communicating with the teensy.
        Raises:
            Exception: If the teensy is not found.
        """
        # Find the serial port of the teensy
        ports = list(serial.tools.list_ports.comports())
        print("Available serial ports:")
        for port in ports:
            print(port)
            if cls.TEENSY_PID_VID in port.hwid:
                print(port.hwid)
                return serial.Serial(port.device, 921600, timeout=1)

        raise TeensyNotFoundException("Teensy not found. Is it plugged in?")
    
    @staticmethod
    def gen_gamma_lut(gamma: float) -> np.ndarray:
        """Generates a gamma lookup table for the given gamma value.

        Args:
            gamma (float): The gamma value to use.

        Returns:
            np.ndarray: The gamma lookup table.
        """
        lut = (np.arange(256, dtype=np.float32) / 255) ** gamma * 255
        return np.round(lut).astype(np.uint8)
    
    @property
    def brightness(self) -> float:
        return self._brightness
    
    @brightness.setter
    def brightness(self, value: float):
        """
        Set the brightness scale of the LED matrix.

        Args:
            value (float): The brightness scale value to set.
        """
        self._brightness = value
    
@property
def contrast(self) -> float:
    return self._contrast

@contrast.setter
def contrast(self, value: float):
    """
    Set the contrast scale of the LED matrix.

    Args:
        value (float): The contrast scale value to set.
    """
    self._contrast = value

@property
def gamma(self) -> float:
    return self._gamma

@gamma.setter
def gamma(self, value: float):
    """
    Set the gamma value of the LED matrix.

    Args:
        value (float): The gamma value to set.
    """
    self._gamma = value
    self.gamma_lut = LEDMatrix.gen_gamma_lut(value)
