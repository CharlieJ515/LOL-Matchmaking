import os
import requests
import psycopg

from dotenv import load_dotenv

load_dotenv()

VERSION = "15.15.1"
DATA_DRAGON_URL = (
    f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/champion.json"
)
POSTGRES_DSN = os.environ["POSTGRES_DSN"]


def main():
    response = requests.get(DATA_DRAGON_URL)
    response.raise_for_status()
    data = response.json()["data"]

    champions = []
    for champ in data.values():
        champions.append(
            {
                "champion_id": int(champ["key"]),
                "champion_name": champ["name"],
            }
        )

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                    INSERT INTO champions (champion_id, champion_name)
                    VALUES (%(champion_id)s, %(champion_name)s)
                """,
                champions,
            )
        conn.commit()


if __name__ == "__main__":
    main()
