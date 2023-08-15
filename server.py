from flask import Flask, request
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    print(f"Received webhook: {data}")  # Print the incoming webhook data
    return '', 204

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()