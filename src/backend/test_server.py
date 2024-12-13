from fastapi import FastAPI
import uvicorn
import threading
import time

# Create FastAPI app
app = FastAPI()


# Function to print "1" every 2 seconds
def print_task():
    while True:
        print(1)
        time.sleep(2)


# Define a simple route
@app.get("/")
def read_root():
    return {"message": "Server is running..."}


if __name__ == "__main__":
    # Start the print task in a separate thread
    print_thread = threading.Thread(target=print_task, daemon=True)
    print_thread.start()

    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8080)
