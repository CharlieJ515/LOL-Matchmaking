import os
import requests
import psycopg

from dotenv import load_dotenv

load_dotenv()

VERSION = "14.2.1"
DATA_DRAGON_URL = f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/champion.json"
POSTGRES_DSN = os.environ["POSTGRES_DSN"]

def main():
    url = DATA_DRAGON_URL
    response = requests.get(url)
    response.raise_for_status()
    data =  response.json()["data"]

    champions = []
    for champ in data.items():
        champions.append({
            "champion_id": int(champ["key"]),
            "champion_name":champ["name"]
        })

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                    INSERT INTO champions (champion_id, champion_name)
                    VALUES (%(champion_id)s, %(champion_name)s)
                    ON CONFLICT (champion_id) DO UPDAT
                    SET champion_name = EXCLUDED.champion_name;
                """,
                champions,
            )
        conn.commit()

if __name__ == "__main__":
    main()
