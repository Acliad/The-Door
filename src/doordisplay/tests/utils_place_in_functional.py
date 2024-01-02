from frames.utils import place_in
from frames.framers.animsnowflake import Snowflake
from matplotlib import pyplot as plt
import numpy as np
import random
import timeit

seed = 10
random.seed(seed)

snowflake_size = 5
snowflake = Snowflake(snowflake_size, 0, 0, 1, (0, 200, 255))
snowflake_mat = snowflake.matrix
bg_color = (0, 0, 0)
# Replace all the black pixels with red pixels
idx = np.where((snowflake_mat == [0, 0, 0]).all(axis=2))
snowflake_mat[idx] = bg_color

# Test shifts
padding = 0
padded_snowflake = np.full((snowflake_size+padding*2, snowflake_size+padding*2, 3), bg_color, dtype=np.uint8)
padded_snowflake[padding:snowflake_size+padding, padding:snowflake_size+padding] = snowflake_mat

canvas_bg_color = (255, 0, 0)
canvas = np.full((124, 50, 3), canvas_bg_color, dtype=np.uint8)

c = place_in(canvas, padded_snowflake, 25, 25.25, transparent_threshold=5)

plt.imshow(canvas)
plt.show()
