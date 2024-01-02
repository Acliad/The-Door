from frames.utils import place_in
from frames.framers.animsnowflake import Snowflake
from matplotlib import pyplot as plt
import numpy as np
import random
import timeit

seed = 10
random.seed(seed)

snowflake = Snowflake(5, 0, 0, 1, (0, 255, 255))
snowflake_mat = snowflake.matrix

canvas = np.zeros((124, 50, 3), dtype=np.uint8)

num_runs = 100000
place_in_execution_time = timeit.timeit('place_in(canvas, snowflake_mat, 20.25, 20.25, transparent_threshold=5)', globals=globals(), number=num_runs)
print(f'place_in execution time: {place_in_execution_time:.3f} sec')
print(f'place_in average time:   {place_in_execution_time / num_runs * 1000:.3f} ms')