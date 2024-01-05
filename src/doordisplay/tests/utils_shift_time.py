from frames.utils import shift
from frames.framers.animations.animsnowflake import Snowflake
import numpy as np
import matplotlib.pyplot as plt
import random
import timeit

seed = 10
random.seed(seed)

snowflake_size = 5
snowflake = Snowflake(snowflake_size, 0, 0, 1, (255, 255, 255))
snowflake_mat = snowflake.matrix

# Time a wrap shift
padding = 2
canvas = np.zeros((snowflake_size+padding*2, snowflake_size+padding*2, 3), dtype=np.uint8)
canvas[padding:snowflake_size+padding, padding:snowflake_size+padding] = snowflake_mat

# interpolation_strategy = 'lanczos'
interpolation_strategy = 'spline'
spline_order = 1

num_runs = 10000
execution_time = timeit.timeit("shift(canvas, 2.25, 2.25, mode='wrap', interpolation_strategy=interpolation_strategy, spline_order=spline_order)", 
                               globals=globals(), 
                               number=num_runs)
print(f'shift (wrap) execution time: {execution_time:.3f} sec')
print(f'shift (wrap) average time:   {execution_time / num_runs * 1000:.3f} ms')

# Time an extend shift
execution_time = timeit.timeit("shift(canvas, 2.25, 2.25, mode='extend', interpolation_strategy=interpolation_strategy, spline_order=spline_order)", 
                               globals=globals(), 
                               number=num_runs)
print(f'shift (extend) execution time: {execution_time:.3f} sec')
print(f'shift (extend) average time:   {execution_time / num_runs * 1000:.3f} ms')