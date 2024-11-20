from quart import Quart
import asyncio

app = Quart(__name__)

# Task 1: Print something every 2 seconds
async def task_one():
    while True:
        print("Task One is running...")
        await asyncio.sleep(2)

# Task 2: Print something every 3 seconds
async def task_two():
    while True:
        print("Task Two is running...")
        await asyncio.sleep(3)

# Register tasks to run with Quart
@app.before_serving
async def before_serving():
    print("Starting background tasks...")
    asyncio.create_task(task_one())
    asyncio.create_task(task_two())

@app.route('/')
async def home():
    return "Hello, Quart with Background Tasks!"

if __name__ == "__main__":
    app.run()
