from framing.utils import shift
from framing.framers.animations.animsnowflake import Snowflake
import numpy as np
import matplotlib.pyplot as plt
import random

def test_lanczos(canvas: np.ndarray, edge_strategy: str):
    pos1 = shift(canvas, 0.25, 0.25, interpolation_strategy='lanczos', edge_strategy=edge_strategy)
    pos2 = shift(canvas, -0.75, -0.75, interpolation_strategy='lanczos', edge_strategy=edge_strategy)

    # Test circular shifts
    pos3 = shift(canvas, 1.25, 1.25, interpolation_strategy='lanczos', edge_strategy=edge_strategy)
    pos4 = shift(canvas, -1.75, -1.75, interpolation_strategy='lanczos', edge_strategy=edge_strategy)

    # Test extended shifts
    pos5 = shift(canvas, 10.5, 25.25, mode='extend', interpolation_strategy='lanczos', edge_strategy=edge_strategy)
    pos6 = shift(canvas, -2.75, -2.75, mode='extend', interpolation_strategy='lanczos', edge_strategy=edge_strategy)

    # Plot results on a subplot
    fig, axs = plt.subplots(4, 2, figsize=(10, 8))
    axs[0, 0].imshow(canvas)
    axs[0, 0].set_title('Original', fontsize=8)

    axs[0, 1].axis('off')

    axs[1, 0].imshow(pos1)
    axs[1, 0].set_title('Shifted by (0.25, 0.25)', fontsize=8)
    axs[1, 1].imshow(pos2)
    axs[1, 1].set_title('Shifted by (-0.75, -0.75)', fontsize=8)

    axs[2, 0].imshow(pos3)
    axs[2, 0].set_title('Circle Shifted by (1.25, 1.25)', fontsize=8)

    axs[2, 1].imshow(pos4)
    axs[2, 1].set_title('Circle Shifted by (-1.75, -1.75)', fontsize=8)

    axs[3, 0].imshow(pos5)
    axs[3, 0].set_title('Extended Shifted by (10.5, 25.25)', fontsize=8)

    axs[3, 1].imshow(pos6)
    axs[3, 1].set_title('Extended Shifted by (-2.75, -2.75)', fontsize=8)

    plt.subplots_adjust(hspace=0.5)  # Increase the padding between subplots

    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    plt.show()

def test_spline(canvas: np.ndarray, spline_order: int, edge_strategy: str):
    pos1 = shift(canvas, 0.25, 0.25, interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')
    pos2 = shift(canvas, -0.75, -0.75, interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')

    # Test circular shifts
    pos3 = shift(canvas, 1.25, 1.25, interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')
    pos4 = shift(canvas, -1.75, -1.75, interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')

    # Test extended shifts
    pos5 = shift(canvas, 10.5, 25.25, mode='extend', interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')
    pos6 = shift(canvas, -2.75, -2.75, mode='extend', interpolation_strategy='spline', spline_order=spline_order, edge_strategy='constant')

    # Plot results on a subplot
    fig, axs = plt.subplots(4, 2, figsize=(10, 8))
    axs[0, 0].imshow(canvas)
    axs[0, 0].set_title('Original', fontsize=8)

    axs[0, 1].axis('off')

    axs[1, 0].imshow(pos1)
    axs[1, 0].set_title('Shifted by (0.25, 0.25)', fontsize=8)
    axs[1, 1].imshow(pos2)
    axs[1, 1].set_title('Shifted by (-0.75, -0.75)', fontsize=8)

    axs[2, 0].imshow(pos3)
    axs[2, 0].set_title('Circle Shifted by (1.25, 1.25)', fontsize=8)

    axs[2, 1].imshow(pos4)
    axs[2, 1].set_title('Circle Shifted by (-1.75, -1.75)', fontsize=8)

    axs[3, 0].imshow(pos5)
    axs[3, 0].set_title('Extended Shifted by (10.5, 25.25)', fontsize=8)

    axs[3, 1].imshow(pos6)
    axs[3, 1].set_title('Extended Shifted by (-2.75, -2.75)', fontsize=8)

    plt.subplots_adjust(hspace=0.5)  # Increase the padding between subplots

    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    plt.show()

seed = 10
random.seed(seed)

snowflake_size = 5
snowflake = Snowflake(snowflake_size, 0, 0, 1, (255, 255, 255))
snowflake_mat = snowflake.matrix
bg_color = (0, 0, 0)
# Replace all the black pixels with background pixels
idx = np.where((snowflake_mat == [0, 0, 0]).all(axis=2))
snowflake_mat[idx] = bg_color

# Test shifts
padding = 0
canvas = np.full((snowflake_size+padding*2, snowflake_size+padding*2, 3), bg_color, dtype=np.uint8)
canvas[padding:snowflake_size+padding, padding:snowflake_size+padding] = snowflake_mat

spline_order = 1
edge_strategy = 'constant'

test_lanczos(canvas, edge_strategy)
# test_spline(canvas, spline_order, edge_strategy)