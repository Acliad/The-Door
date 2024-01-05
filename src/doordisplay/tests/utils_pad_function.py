from framing.utils import pad
from framing.framers.animations.animsnowflake import Snowflake
import numpy as np
import matplotlib.pyplot as plt
import random

def test_constant():
    inside_mat = np.ones((5, 5, 3), dtype=np.float64)
    outside_mat = pad(inside_mat, ((1, 1), (1, 1)), mode='constant', value=[0, 0, 0])

    outside_top_mat = pad(inside_mat, ((2, 0), (0, 0)), value=0.5)
    outside_bottom_mat = pad(inside_mat, ((0, 2), (0, 0)))

    outside_left_mat = pad(inside_mat, ((0, 0), (1, 0)), value=[0, 1, 1])
    outside_right_mat = pad(inside_mat, ((0, 0), (0, 1)), value=[0, 1, 1])

    # Test 'constant' padding
    fig, axs = plt.subplots(3, 2, figsize=(10, 10))
    axs[0, 0].imshow(inside_mat)
    axs[0, 0].set_title('Inside')
    axs[0, 1].imshow(outside_mat)
    axs[0, 1].set_title('Outside')
    axs[1, 0].imshow(outside_left_mat)
    axs[1, 0].set_title('Outside Left (value=[0, 1, 1])')
    axs[1, 1].imshow(outside_right_mat)
    axs[1, 1].set_title('Outside Right (value=[0, 1, 1])')
    axs[2, 0].imshow(outside_top_mat)
    axs[2, 0].set_title('Outside Top (value=0.5)')
    axs[2, 1].imshow(outside_bottom_mat)
    axs[2, 1].set_title('Outside Bottom')
    plt.show()


def test_nearest():
    # Test 'nearest' padding
    # Make the edges of inside_mat random arrays
    mat_size = 5
    inside_mat = np.random.rand(mat_size, mat_size, 3)
    # Make the inside of the new matrix white
    inside_mat[1:-1, 1:-1] = 1

    padding = 6

    outside_mat = pad(inside_mat, ((padding, padding), (padding, padding)), mode='nearest')

    outside_top_mat = pad(inside_mat, ((padding, 0), (0, 0)), mode='nearest')
    outside_topright_mat = pad(inside_mat, ((padding, 0), (0, padding)), mode='nearest')

    outside_right_mat = pad(inside_mat, ((0, 0), (0, padding)), mode='nearest')
    outside_bottomright_mat = pad(inside_mat, ((0, padding), (0, padding)), mode='nearest')

    outside_bottom_mat = pad(inside_mat, ((0, padding), (0, 0)), mode='nearest')
    outside_bottomleft_mat = pad(inside_mat, ((0, padding), (padding, 0)), mode='nearest')

    outside_left_mat = pad(inside_mat, ((0, 0), (padding, 0)), mode='nearest')
    outside_topleft_mat = pad(inside_mat, ((padding, 0), (padding, 0)), mode='nearest')

    fig, axs = plt.subplots(5, 2, figsize=(5, 10))
    fig.subplots_adjust(hspace=0.5)
    
    axs[0, 0].imshow(inside_mat)
    axs[0, 0].set_title('Inside')
    axs[0, 1].imshow(outside_mat)
    axs[0, 1].set_title('Outside')

    axs[1, 0].imshow(outside_top_mat)
    axs[1, 0].set_title('Outside Top')
    axs[1, 1].imshow(outside_topright_mat)
    axs[1, 1].set_title('Outside Top Right')

    axs[2, 0].imshow(outside_right_mat)
    axs[2, 0].set_title('Outside Right')
    axs[2, 1].imshow(outside_bottomright_mat)
    axs[2, 1].set_title('Outside Bottom Right')

    axs[3, 0].imshow(outside_bottom_mat)
    axs[3, 0].set_title('Outside Bottom')
    axs[3, 1].imshow(outside_bottomleft_mat)
    axs[3, 1].set_title('Outside Bottom Left')

    axs[4, 0].imshow(outside_left_mat)
    axs[4, 0].set_title('Outside Left')
    axs[4, 1].imshow(outside_topleft_mat)
    axs[4, 1].set_title('Outside Top Left')
    plt.show()

seed = 10
random.seed(seed)
np.random.seed(seed)
# test_constant()
test_nearest()