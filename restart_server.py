import os
import sys
import time

def restart_flask_server():
    print("Restarting Flask server...")
    time.sleep(2)  # Optional: Add a delay before restarting
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    restart_flask_server()
