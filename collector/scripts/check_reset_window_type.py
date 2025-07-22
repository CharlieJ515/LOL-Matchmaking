import requests
import time
from datetime import datetime, timedelta

API_KEY = "RGAPI-87582a6f-4506-45b1-bc20-427340ea6318"

gameName = "Hide on bush"
tagLine = "KR1"
URL = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
HEADERS = {"X-Riot-Token": API_KEY}


def send_requests(burst_num, burst_size):
    for i in range(burst_size):
        now = datetime.now().strftime("%H:%M:%S")
        try:
            response = requests.get(URL, headers=HEADERS)
            print(
                f"[Burst {burst_num} - {i+1}/{burst_size}] {now} - Status: {response.status_code}"
            )

            for header in [
                "X-App-Rate-Limit",
                "X-App-Rate-Limit-Count",
                "X-Method-Rate-Limit",
                "X-Method-Rate-Limit-Count",
            ]:
                if header in response.headers:
                    print(f"    {header}: {response.headers[header]}")

            if response.status_code != 200:
                break

        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(0.1)


start = datetime.now()
send_requests(1, 50)

print(f"Sleeping for {90} seconds...\n")
time.sleep(90)

send_requests(2, 50)
wait_time = start + timedelta(minutes=2, seconds=10) - datetime.now()
time.sleep(wait_time.total_seconds())
send_requests(3, 50)

time.sleep(90)
