from PIL import Image
import numpy as np
from scipy.ndimage import convolve as convolve
from scipy.ndimage import convolve1d as convolve1d
from scipy.ndimage import shift as _spline_shift
from numbers import Number
from typing import Sequence

_DEFAULT_SHIFT_EPS = 0.01
_DEFAULT_LANCZOS_A = 3
_DEFAULT_SPLINE_ORDER = 3

def _lanczos_kernel(x, a=_DEFAULT_LANCZOS_A) -> np.ndarray:
    """
    Lanczos kernel function.
    :param x: Input values.
    :param a: Size of the kernel, typically 2 or 3.
    :return: Lanczos kernel values over x.
    """
    L = np.zeros_like(x, dtype=np.float64)
    L[x == 0] = 1.0
    kernel_idx = abs(x) < a
    L[kernel_idx] = np.sinc(x[kernel_idx]) * np.sinc(x[kernel_idx] / a)
    return L

def pad(matrix: np.ndarray, 
        padding: tuple[tuple[int, int], tuple[int, int]], 
        mode: str = 'constant',
        value: tuple[Number, Number, Number] = 0
        ) -> np.ndarray:
    """
    Pads an NxMx3 matrix with a variety of padding options. See the mode argument list. This function is generally 
    faster than np.pad, especially for smaller matrices.

    TODO:
        - Implement 'reflect', 'mirror', 'wrap'

    Args:
        matrix (np.ndarray): The matrix to pad.
        padding (tuple[tuple[int, int], tuple[int, int]]): The number of pixels to pad on each side of the matrix.
            The order of the tuples is (top, bottom), (left, right).
        mode (str, optional): The padding mode. Available options are 'constant', 'wrap', 'reflect', and 'nearest'.
            Defaults to 'constant'.
        value (tuple[Number, Number, Number], optional): The value to fill the padded area with when mode is 'constant'.
            Defaults to (0, 0, 0).

    Returns:
        np.ndarray: The padded matrix.
    """

    match mode.lower():
        case 'constant':
            return _pad_constant(matrix, padding, value)
        case 'wrap':
            raise NotImplementedError('Wrap mode is not yet implemented')
        case 'reflect':
            raise NotImplementedError('Reflect mode is not yet implemented')
        case 'nearest':
            return _pad_nearest(matrix, padding)
        case 'mirror':
            raise NotImplementedError('Mirror mode is not yet implemented')

def _pad_nearest(matrix: np.ndarray,
                 padding: tuple[tuple[int, int], tuple[int, int]]
                ) -> np.ndarray:
    """
    Pad a matrix with the values around the edge of the matrix.

    Args:
        matrix (np.ndarray): The original matrix to be padded.
        padding (tuple[tuple[int, int], tuple[int, int]]): The number of pixels to pad on each side of the matrix.
            The order of the tuples is (top, bottom), (left, right).
    Returns:
        np.ndarray: The padded matrix.

    """
    
    top_padding, bottom_padding = padding[0]
    left_padding, right_padding = padding[1]
    
    # Create a new matrix with the correct shape
    padded_matrix = np.zeros((matrix.shape[0] + top_padding + bottom_padding,
                              matrix.shape[1] + left_padding + right_padding,
                              matrix.shape[2]),
                              dtype=matrix.dtype)
    
    # There are 8 zones to consider:
    #   1. Top edge
    #   2. Top right corner
    #   3. Right edge
    #   4. Bottom right corner
    #   5. Bottom edge
    #   6. Bottom left corner
    #   7. Left edge
    #   8. Top left corner
    # The following code fills each zone with the nearest pixel value from the original matrix

    top_padding_idx    =  top_padding    or None
    bottom_padding_idx = -bottom_padding or None
    left_padding_idx   =  left_padding   or None
    right_padding_idx  = -right_padding  or None
    # Get the indices of the new matrix where the original matrix will be placed
    if top_padding:
        # Fill the top edge
        row = matrix[0, :, :]
        padded_matrix[:top_padding, left_padding:right_padding_idx] = row[None, :, :]
    if top_padding and right_padding:
        # Fill the top right corner
        padded_matrix[:top_padding, -right_padding:] = matrix[0, -1, :]
    if right_padding:
        # Fill the right edge
        column = matrix[:, -1, :]
        padded_matrix[top_padding_idx:bottom_padding_idx, right_padding_idx:] = column[:, None, :]
    if right_padding and bottom_padding:
        # Fill the bottom right corner
        padded_matrix[-bottom_padding:, -right_padding:] = matrix[-1, -1, :]
    if bottom_padding:
        # Fill the bottom edge
        row = matrix[-1, :, :]
        padded_matrix[bottom_padding_idx:, left_padding_idx:right_padding_idx] = row[None, :, :]
    if bottom_padding and left_padding:
        # Fill the bottom left corner
        padded_matrix[-bottom_padding:, :left_padding] = matrix[-1, 0, :]
    if left_padding:
        # Fill the left edge
        column = matrix[:, 0, :]
        padded_matrix[top_padding_idx:bottom_padding_idx, :left_padding] = column[:, None, :]
    if left_padding and top_padding:
        # Fill the top left corner
        padded_matrix[:top_padding, :left_padding] = matrix[0, 0, :]

    # Place the original matrix into the new matrix
    padded_matrix[top_padding_idx:bottom_padding_idx, left_padding_idx:right_padding_idx] = matrix
    
    return padded_matrix

def _pad_constant(matrix: np.ndarray, 
                  pad_width: tuple[tuple[int, int], tuple[int, int]],  
                  value: tuple[Number, Number, Number]
                  ) -> np.ndarray:
    """
    Pad a matrix with a constant value.

    Args:
        matrix (np.ndarray): The matrix to be padded.
        pad_width (tuple[tuple[int, int], tuple[int, int]]): The amount of padding to add on each side of the matrix.
        value (tuple[Number, Number, Number]): The constant value to fill the padding with.

    Returns:
        np.ndarray: The padded matrix.
    """
    # Create a new matrix with the correct shape
    padded_matrix = np.zeros((matrix.shape[0] + pad_width[0][0] + pad_width[0][1], 
                            matrix.shape[1] + pad_width[1][0] + pad_width[1][1],
                            matrix.shape[2]),
                            dtype=matrix.dtype)
    
    # Fill the new matrix with the pad value
    if isinstance(value, Sequence):
        for i, val in enumerate(value):
            padded_matrix[:, :, i].fill(val)
    elif value:
        padded_matrix.fill(value)

    # Copy the original matrix into the new matrix
    row_slice = slice(pad_width[0][0], -pad_width[0][1] or None)
    col_slice = slice(pad_width[1][0], -pad_width[1][1] or None)
    padded_matrix[row_slice, col_slice] = matrix
    return padded_matrix

def shift(matrix:np.ndarray, 
          x:float, 
          y:float, 
          mode:str='wrap', 
          edge_strategy='constant', 
          interpolation_strategy='spline',
          **kwargs
          ) -> np.ndarray:
    """
    Shifts the canvas by the specified amount in the x and y directions.

    TODO:
        - Optimize spline interpolation. It's currently much slower than Lanczos interpolation for any order > 1.
        - Fix fractional wrap shifts at the edge. The shifted pixel current gets lost outside the matrix and not 
          wrapped back around to the other side of the matrix.

    Args:
        matrix (np.ndarray): The input canvas to be shifted.
        x (float): The amount of shift in the x direction.
        y (float): The amount of shift in the y direction.
        mode (str, optional): How to treat shifts at the edge. Valid options are 'wrap', 'clip', and 'extend'. Defaults 
            to 'wrap'.
        edge_strategy (str, optional): How to handle edge pixels. Valid options are 'reflect', 'constant', 'nearest', 
            'mirror', 'wrap'. Defaults to 'constant'.
        interpolation_strategy (str, optional): How to handle interpolation. Valid options are 'lanczos' and 'spline'. 
            Defaults to 'spline'. 
        **kwargs: Additional keyword arguments.
            shift_eps (float): The threshold for considering fractional shift. Values less than this will be considered 
                int shifts. Defaults to 0.01.
            a (int): The size of the Lanczos kernel. Defaults to 3.
            spline_order (int): The order of the spline interpolation. Defaults to 3.
            cval (tuple[Number, Number, Number]): The constant value to use when edge_strategy is 'constant'. Defaults
                to 0.

    Returns:
        np.ndarray: The shifted canvas.
    """
    shift_eps = kwargs.get('shift_eps', _DEFAULT_SHIFT_EPS)
    cval = kwargs.get('cval', 0)

    # Check if the requested shift is large
    if abs(x) < shift_eps and abs(y) < shift_eps:
        return matrix

    # Get the fractional and integer parts of the shift
    x_frac = x % 1 if x >= 0 else -(-x % 1)
    y_frac = y % 1 if y >= 0 else -(-y % 1)
    x_int = int(x)
    y_int = int(y)

    if mode == 'extend':
        # Extend the canvas by enough pixels to accommodate the shift
        # TODO: For larger shifts, it would make more sense to pad by 1 pixel for the fractional shift and then
        #       pad by the integer shift. 
        pad_x = int(np.ceil(abs(x)))
        pad_y = int(np.ceil(abs(y)))
        pad_x_tuple = (0, pad_x) if x >= 0 else (pad_x, 0)
        pad_y_tuple = (0, pad_y) if y >= 0 else (pad_y, 0)
        matrix = pad(matrix, (pad_y_tuple, pad_x_tuple), mode=edge_strategy, value=cval)


    if abs(x_frac) >= shift_eps or abs(y_frac) >= shift_eps:
        # Fractional shift is large enough to require interpolation
        match interpolation_strategy.lower():
            case 'spline':
                order = kwargs.get('spline_order', _DEFAULT_SPLINE_ORDER)
                # NOTE: I think grid-constant really behaves how I'd expect constant to behave.
                mode = 'grid-constant' if edge_strategy == 'constant' else edge_strategy
                shifted_matrix = _spline_shift(matrix, 
                                               (y_frac, x_frac, 0), 
                                               order=order, 
                                               mode=mode, 
                                               cval=cval)
            case 'lanczos':
                a = kwargs.get('a', _DEFAULT_LANCZOS_A)
                shifted_matrix = _shift_lanczos(matrix, x_frac, y_frac, a, edge_strategy, cval)
                # Clip negative values to 0
                shifted_matrix = np.maximum(shifted_matrix, 0)
            case _:
                raise ValueError(f'Invalid interpolation_strategy: {interpolation_strategy}')
    else:
        # Fractional shift is small enough to be handled by np.roll alone
        shifted_matrix = matrix

    # Shift the image by the integer portion of the shift
    shifted_matrix = np.roll(shifted_matrix, (y_int, x_int), axis=(0, 1))

    return shifted_matrix.astype(matrix.dtype)

def _shift_lanczos(matrix:np.ndarray, x:float, y:float, a:int, edge_strategy:str, cval:float) -> np.ndarray:
    """
    Shifts the given matrix using Lanczos interpolation. This function is only for fractional shifts (i.e., |x| < 1).
    The returned matrix will have dtype np.float64 regardless of the input matrix dtype.

    Args:
        matrix (np.ndarray): The input matrix to be shifted.
        x (float): The fractional shift along the x-axis.
        y (float): The fractional shift along the y-axis.
        a (int): The size of the Lanczos kernel.
        edge_strategy (str): The strategy to handle edges during convolution. See the edge_strategy arg of utils.shift.
        cval (float): The constant value to use for padding.

    Returns:
        np.ndarray: The shifted matrix.

    Raises:
        AssertionError: If the absolute value of x or y is not less than 1.
    """

    assert abs(x) < 1 and abs(y) < 1, '_shift_lanczos is only intended for fractional shifts'

    # Create the Lanczos kernel for convolution
    lki = np.arange(-a + 1, a + 1, 1)
    lanczos_kernelx = _lanczos_kernel(x - lki)
    lanczos_kernely = _lanczos_kernel(y - lki)

    # NOTE: Since the lanczos kernel is separable, we can convolve the x and y kernels separately. This provides a small
    # speedup over convolving the full kernel. 
    # NOTE: Origin is the center of the kernel, but for even numbered kernels, which this will always be,
    # ndimage.convolve uses the value to the right of the "center" and we want the value to the left of the "center".
    shifted_matrix = convolve1d(matrix.astype(np.float64), 
                                lanczos_kernelx, 
                                axis=1, 
                                mode=edge_strategy, 
                                cval=cval, 
                                origin=-1)
    shifted_matrix = convolve1d(shifted_matrix, 
                                lanczos_kernely, 
                                axis=0, 
                                mode=edge_strategy, 
                                cval=cval, 
                                origin=-1)
    
    return shifted_matrix

def place_in(target:np.ndarray, 
             source:np.ndarray, 
             row:float, 
             col:float, 
             transparent_threshold:float|None = None,
             **kwargs
             ) -> None:
    # TODO: 
    #   - Improve transparency handling. It would be nice to be able to place a matrix on top of another and interpolate
    #     the values based on the source matrix as a background.
    #   - Add support for different shift parameters

    shift_eps = kwargs.get('shift_eps', _DEFAULT_SHIFT_EPS)

    # Check if the target actually fits in the source
    if row >= target.shape[0] or col >= target.shape[1] or row + source.shape[0] < 0 or col + source.shape[1] < 0:
        return
    
    # Get the integer location of the source matrix in the target matrix
    row_int = int(row)
    col_int = int(col)
        
    # Create a version of the source matrix shifted by the fractional part of the x and y coordinates
    row_frac = row % 1 if row >= 0 else -(-row % 1)
    col_frac = col % 1 if col >= 0 else -(-col % 1)
    # Pad the source matrix edge by 1 pixel from the target matrix to accommodate the fractional shift
    source_shifted = shift(source, 
                           col_frac, 
                           row_frac, 
                           mode='extend', 
                           edge_strategy='constant', 
                           shift_eps=shift_eps,
                           interpolation_strategy='spline',
                           spline_order=1)

    # Row and column ints need to be -1 if the position is negative and a fractional shift is applied
    row_int = row_int - 1 if row < 0 and source_shifted.shape[0] > source.shape[0] else row_int
    col_int = col_int - 1 if col < 0 and source_shifted.shape[1] > source.shape[1] else col_int

    if transparent_threshold is None:
        target_row_start = max(row_int, 0)
        target_row_end   = min(row_int + source_shifted.shape[0], target.shape[0])
        target_col_start = max(col_int, 0)
        target_col_end   = min(col_int + source_shifted.shape[1], target.shape[1])

        source_row_start = max(-row_int, 0)
        source_row_end   = min(target.shape[0] - row_int, target.shape[0])
        source_col_start = max(-col_int, 0)
        source_col_end   = min(target.shape[1] - col_int, target.shape[1])

        target[target_row_start:target_row_end, target_col_start:target_col_end] = \
            source_shifted[source_row_start:source_row_end, source_col_start:source_col_end]
    else:
        # TODO: There should be better ways to handle transparency?
        # Get the largest value across RGB channels for each pixel
        source_shifted_max = np.max(source_shifted, axis=2)
        # Get the indices from the source that we want to place into the target based on the transparent threshold
        target_indices = np.array(np.where(source_shifted_max > transparent_threshold))
        # We only need the row/col indices, so eliminate the extra color channels
        # target_indices = target_indices[0:2, ::3]
        # Add source position to pixel indices to shift the source to the correct position for the target
        target_indices[0] += row_int
        target_indices[1] += col_int
        # This is a real noodle-baker. pixel_matrix_indices is a 2D array of shape (2, num_valid_pixels) where the axis=0
        # values are the row and axis=1 values are the column. We want to check if any of the row or column values are out
        # of bounds of the matrix. The next two lines create boolean arrays of shape (num_valid_pixels,) where the values
        # are True if the row or column is in bounds and False otherwise. The last line combines the two boolean arrays to
        # index pixel_matrix_indices and select only the indices where the row and column are within the bounds of the
        # matrix.
        in_bound_rows = (target_indices[0] >= 0) & (target_indices[0] < target.shape[0])
        in_bound_cols = (target_indices[1] >= 0) & (target_indices[1] < target.shape[1])
        target_indices = target_indices[:, in_bound_rows & in_bound_cols]

        # We now back out the indices of the snowflake matrix that we want to use by subtracting the snowflake
        # position that we added earlier
        snowflake_matrix_indices = np.copy(target_indices)
        snowflake_matrix_indices[0] -= row_int
        snowflake_matrix_indices[1] -= col_int
        # Finally, we can draw the snowflake onto the frame matrix by placing the valid snowflake pixels into the
        # frame matrix
        target[target_indices[0], target_indices[1]] = source_shifted[snowflake_matrix_indices[0], snowflake_matrix_indices[1]]

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