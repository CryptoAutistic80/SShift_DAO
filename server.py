from queue import Queue
from src.database_manager import insert_data, setup_db
from threading import Thread
from flask import Flask, request
import asyncio
import time

# Initialize queue for handling webhooks
webhook_queue = Queue()

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    data['timestamp'] = int(time.time())  # Add the current UNIX timestamp
    print(f"Received webhook: {data}")  # Print the incoming webhook data
    
    # Push the data to the queue for processing
    webhook_queue.put(data)
    
    return '', 204

def process_webhook_data():
    """
    Continuously process data from the webhook queue and insert it into the database.
    """
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        data = webhook_queue.get()  # This will block until an item is available
        
        # Using the created event loop to run the asynchronous function
        loop.run_until_complete(insert_data(data))
        
        webhook_queue.task_done()

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Start the webhook processing thread
    t1 = Thread(target=process_webhook_data)
    t1.start()
    
    # Start the Flask server
    t2 = Thread(target=run)
    t2.start()

# Initialize the database (create table if it doesn't exist)
loop = asyncio.get_event_loop()
loop.run_until_complete(setup_db())

# Start the server
keep_alive() 
