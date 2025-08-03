import requests
import time
from datetime import datetime

API_KEY = "RGAPI-87582a6f-4506-45b1-bc20-427340ea6318"

gameName = "Hide on bush"
tagLine = "KR1"
URL = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
HEADERS = {"X-Riot-Token": API_KEY}

INTERVAL = 5
DURATION = 6 * 60


def send_requests(interval, duration):
    total_requests = duration // interval
    for i in range(total_requests):
        now = datetime.now().strftime("%H:%M:%S")
        try:
            response = requests.get(URL, headers=HEADERS)
            print(f"[{i+1}/{total_requests}] {now} - Status: {response.status_code}")

            # Print rate limit headers if present
            for header in [
                "X-App-Rate-Limit",
                "X-App-Rate-Limit-Count",
                "X-Method-Rate-Limit",
                "X-Method-Rate-Limit-Count",
            ]:
                if header in response.headers:
                    print(f"    {header}: {response.headers[header]}")

        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(interval)


send_requests(INTERVAL, DURATION)
