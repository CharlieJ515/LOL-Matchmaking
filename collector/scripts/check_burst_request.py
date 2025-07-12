import requests
import time
from datetime import datetime

API_KEY = "RGAPI-87582a6f-4506-45b1-bc20-427340ea6318"

gameName = "Hide on bush"
tagLine = "KR1"
URL = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
HEADERS = {"X-Riot-Token": API_KEY}


def send_requests():
    BURST_SIZE = 10
    BURST_COUNT = 9  # total bursts → 6 bursts × ~30s = ~3 minutes
    BURST_INTERVAL = 20  # wait between bursts in seconds

    for burst in range(BURST_COUNT):
        print(f"\nStarting burst #{burst + 1}")
        for i in range(BURST_SIZE):
            now = datetime.now().strftime("%H:%M:%S")
            try:
                response = requests.get(URL, headers=HEADERS)
                print(
                    f"[Burst {burst+1} - {i+1}/{BURST_SIZE}] {now} - Status: {response.status_code}"
                )

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

        print(f"Sleeping for {BURST_INTERVAL} seconds...\n")
        time.sleep(BURST_INTERVAL)


send_requests()
