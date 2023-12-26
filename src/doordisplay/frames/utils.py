from PIL import Image
import numpy as np
from scipy.signal import convolve

def _lanczos_kernel(x, a=3):
    """
    Lanczos kernel function.
    :param x: Input values.
    :param a: Size of the kernel, typically 2 or 3.
    :return: Lanczos kernel values over x.
    """
    L = np.zeros_like(x)
    L[x == 0] = 1.0
    kernel_idx = abs(x) < a
    L[kernel_idx] = np.sinc(x[kernel_idx]) * np.sinc(x[kernel_idx] / a)
    return L

def shift(pos1:np.ndarray, shiftx:float, shifty:float, shift_eps=0.01, **kwargs):
    """
    Shifts the canvas by the specified amount in the x and y directions.

    TODO: 
        - Add modes for wrap, clip, and extend
        - Add choices for interpolation strategy

    Args:
        pos1 (np.ndarray): The input canvas to be shifted.
        shiftx (float): The amount of shift in the x direction.
        shifty (float, optional): The amount of shift in the y direction.
        shift_eps (float, optional): The threshold for considering fractional shift. Values less than this will be 
                                     considered int shifts. Defaults to 0.01.
        **kwargs: Additional keyword arguments.
            a (int): The size of the Lanczos kernel. Defaults to 3.

    Returns:
        np.ndarray: The shifted canvas.
    """
    a = kwargs.get('a', 3)

    # Get the fractional and integer parts of the shift
    shiftx_frac = shiftx % 1 if shiftx >= 0 else -(-shiftx % 1)
    shifty_frac = shifty % 1 if shifty >= 0 else -(-shifty % 1)
    shiftx_int = int(shiftx)
    shifty_int = int(shifty)

    if shiftx_frac >= shift_eps or shifty_frac >= shift_eps:
        # Create the Lanczos kernel for convolution
        lki = np.arange(-a + 1, a + 1, 1)
        lanczos_kernelx = _lanczos_kernel(shiftx_frac - lki)
        lanczos_kernely = _lanczos_kernel(shifty_frac - lki)
        lanczos_kernelxy = lanczos_kernelx[:, None] @ lanczos_kernely[:, None].T

        # Convolve the image with the Lanczos kernel
        pos2 = convolve(pos1, lanczos_kernelxy[:, :, None], mode='same')
        # Clip negative values to 0
        pos2 = np.maximum(pos2, 0)
    else:
        pos2 = pos1

    # Shift the image by the integer part of the shift
    pos2 = np.roll(pos2, (shifty_int, shiftx_int), axis=(0, 1))

    return pos2.astype(pos1.dtype)

def scale_fit(image:Image.Image, width:int, height:int) -> Image.Image:
    """Scales an image to fit within a frame while maintaining the aspect ratio

    Args:
        image (Image): The image to scale
        width (int): The width to resize the image to
        height (int): The height to resize the image to

    Returns:
        Image: The scaled image
    """
    # Calculate the new size while maintaining the aspect ratio
    img_width, img_height = image.size
    img_aspect_ratio = img_width / img_height
    frame_aspect_ratio = width / height

    # Check if the given image's aspect ration fits in the frame

    if img_aspect_ratio > frame_aspect_ratio:
        # Landscape image
        new_width = int(width)
        new_height = int(new_width / img_aspect_ratio)
    else:
        # Portrait image
        new_height = int(height)
        new_width = int(new_height * img_aspect_ratio)

    # Resize the image and pad and center vertically and horizontally in the returned frame
    image_resized = image.resize((new_width, new_height))
    frame = Image.new('RGB', (width, height))
    frame.paste(image_resized, ((width - new_width) // 2, (height - new_height) // 2))
    return frame

def clip(image: Image.Image, width: int, height: int, position: str = 'center') -> Image.Image:
    """
    Clips an image to fit within a frame.

    Args:
        image (Image): The image to clip.
        width (int): The width of the frame.
        height (int): The height of the frame.
        position (str, optional): The position of the clipped image within the frame.
            Valid options are 'center', 'topleft', 'topright', 'bottomleft', and 'bottomright'.
            Defaults to 'center'.

    Returns:
        Image: The clipped image.
    """
    # Check if the image fits in the frame
    img_width, img_height = image.size
    if img_width > width or img_height > height:
        match position.lower():
            case 'center':
                # Calculate the center coordinates
                center_x = img_width // 2
                center_y = img_height // 2

                # Calculate the half-width and half-height of the frame
                half_width = width // 2
                half_height = height // 2

                # Calculate the coordinates for cropping
                left = center_x - half_width
                top = center_y - half_height
                right = center_x + half_width
                bottom = center_y + half_height
            case 'topleft':
                left = 0
                top = 0
                right = width
                bottom = height
            case 'topright':
                left = img_width - width
                top = 0
                right = img_width
                bottom = height
            case 'bottomleft':
                left = 0
                top = img_height - height
                right = width
                bottom = img_height
            case 'bottomright':
                left = img_width - width
                top = img_height - height
                right = img_width
                bottom = img_height

        # Clip the image to fit in the frame
        return image.crop((left, top, right, bottom))
    else:
        return image