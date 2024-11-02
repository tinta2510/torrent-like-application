from colorama import Fore, Style, init
from tabulate import tabulate
from tqdm import tqdm
import time

# Initialize colorama
init()

# Print header
print(Fore.CYAN + "="*30)
print(" CLI Dashboard ")
print("="*30 + Style.RESET_ALL)

# Print table
data = [["Dinh", 95], ["Alice", 88], ["Bob", 76]]
headers = ["Name", "Score"]
print(tabulate(data, headers, tablefmt="grid"))

# Progress bar
print("\nProcessing data:")
for i in tqdm(range(100)):
    time.sleep(0.05)

print("\nAll tasks complete!")
