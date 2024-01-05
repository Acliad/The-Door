from frames.utils import pad
from frames.framers.animations.animsnowflake import Snowflake
import numpy as np
import matplotlib.pyplot as plt
import random
import timeit

seed = 10
random.seed(seed)

mode = 'nearest'
padding = ((2, 2), (2, 2))
num_runs = 10000
inside_mat = np.ones((124, 50, 3), dtype=np.uint8)

execution_time = timeit.timeit('pad(inside_mat, padding, mode=mode)', globals=globals(), number=num_runs)
print(f'zero pad execution time: {execution_time:.3f} sec')
print(f'zero pad average time:   {execution_time / num_runs * 1000:.3f} ms')

value = np.array([0, 1, 1], dtype=np.float64)
value = [0, 1, 1]
execution_time = timeit.timeit('pad(inside_mat, padding, mode=mode, value=[0, 255, 255])', globals=globals(), number=num_runs)
print(f'value pad execution time: {execution_time:.3f} sec')
print(f'value pad average time:   {execution_time / num_runs * 1000:.3f} ms')
