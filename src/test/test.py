from tqdm.contrib.concurrent import thread_map
import time

# Function with two inputs
def add(x, y):
    time.sleep(1)
    return x + y

# Input lists
list1 = range(50)
list2 = range(50, 100)

# Apply thread_map
results = thread_map(add, list1, list2, desc="Adding Numbers")

print(results)  # [5, 7, 9, 11, 13]
