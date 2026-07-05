import requests
import json
import logging
import os
from datetime import datetime

# CONFIGURATION
API_URL = "https://worldcup26.ir/get/games"
MASTER_FILE = "wc_matches.json"
OUTPUT_FILE = "daily_wc_matches.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_update():
    # Ensure working directory is the folder where the script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        logging.info("Fetching data from API...")
        response = requests.get(API_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Safely extract list
        matches = data.get('games', []) if isinstance(data, dict) else data
        
        # Save master copy for reference
        with open(MASTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=4)
        logging.info(f"Master file saved with {len(matches)} total matches.")

        # FILTERING: Find matches for today based on 'local_date'
        today_target = datetime.now().strftime("%m/%d/%Y")
        today_matches = []

        for m in matches:
            # Check the local_date field specifically
            m_date = str(m.get('local_date', ''))
            
            # If the target date string is found in the local_date field, add it
            if today_target in m_date:
                today_matches.append(m)
        
        # Save the filtered results to the daily file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(today_matches, f, indent=4)
            
        logging.info(f"Process complete. Found {len(today_matches)} matches for {today_target}.")

    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    run_update()