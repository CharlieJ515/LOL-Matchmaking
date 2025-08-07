import os
import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()

VERSION = "15.15.1"
SUMMONERS_URL = (
    f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/summoner.json"
)
POSTGRES_DSN = os.environ["POSTGRES_DSN"]


def main():
    response = requests.get(SUMMONERS_URL)
    response.raise_for_status()
    summoners = response.json()["data"]

    data = []
    for summoner_info in summoners.values():
        data.append(
            {
                "summoner_id": int(summoner_info["key"]),
                "summoner_name": summoner_info["name"],
            }
        )

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO summoners (summoner_id, summoner_name)
                VALUES (%(summoner_id)s, %(summoner_name)s)
                """,
                data,
            )
        conn.commit()


if __name__ == "__main__":
    main()
