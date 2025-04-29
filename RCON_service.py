from flask import Flask, render_template, jsonify
from rcon.source import Client
import time
import threading
from datetime import datetime
import psutil

app = Flask(__name__)

# RCON Configuration
RCON_HOST = "0.0.0.0" # or input your ip address 
RCON_PORT = 25575 # default RCON port
RCON_PASSWORD = "print your RCON password"
RCON_TIMEOUT = 5

# Global data storage
server_data = {
    "player_list": "No data",
    "tick_query": "No data",
    "player_ping": "No data",
    "system_stats": {
        "cpu_usage": 0,
        "memory_usage": 0,
        "memory_total": 0
    },
    "last_update": "Never"
}

def get_rcon_response(command):
    try:
        with Client(
            RCON_HOST, 
            RCON_PORT, 
            passwd=RCON_PASSWORD, 
            timeout=RCON_TIMEOUT
        ) as client:
            response = client.run(command)
            return response.strip()
    except Exception as e:
        print(f"Command execution error '{command}': {str(e)}")
        return f"Error: {str(e)}"

def get_system_stats():
    """Get system stats using psutil"""
    try:
        # Get CPU usage (1 second interval for accurate reading)
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        mem = psutil.virtual_memory()
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": round(mem.used / (1024 ** 3), 2),  # GB
            "memory_total": round(mem.total / (1024 ** 3), 2)  # GB
        }
    except Exception as e:
        print(f"System stats error: {e}")
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "memory_total": 0
        }

def update_server_data():
    global server_data
    while True:
        try:
            # Get RCON data
            new_data = {
                "player_list": get_rcon_response("list"),
                "tick_query": get_rcon_response("tick query"),
                "player_ping": get_rcon_response("neoforge entity list"),
                "system_stats": get_system_stats(),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update only if at least one command succeeded
            if not all("Error:" in str(v) for v in new_data.values()):
                server_data = new_data
            else:
                print("All commands failed")
            
        except Exception as e:
            print(f"Update loop error: {e}")
        finally:
            time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html', data=server_data)

@app.route('/data')
def get_data():
    return jsonify(server_data)

if __name__ == '__main__':
    # Connection test before starting
    try:
        test_response = get_rcon_response("list")
        print(f"Connection test: {test_response}")
        
        update_thread = threading.Thread(target=update_server_data)
        update_thread.daemon = True
        update_thread.start()
        
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Startup error: {e}")
