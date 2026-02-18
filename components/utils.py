import json
import os

# Define the file path for storing configuration
CONFIG_FILE = "config.json"

def load_config():
    # Check if the configuration file exists
    if not os.path.exists(CONFIG_FILE):
        # Return default empty structure if no file found
        return {"channels": [], "email": "", "smtp_password": ""}
    
    # Open and read the JSON configuration
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(channels, email, smtp_password):
    # Process the input channels string into a clean list
    # Splits by comma and strips whitespace
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]
    
    # Create dictionary to store
    data = {
        "channels": channel_list,
        "email": email,
        "smtp_password": smtp_password
    }
    
    # Write dictionary to JSON file
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)