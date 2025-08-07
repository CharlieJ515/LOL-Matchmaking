import os
import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()

PERKS_URL = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json"
POSTGRES_DSN = os.environ["POSTGRES_DSN"]


def main():
    # Fetch perks.json
    response = requests.get(PERKS_URL)
    response.raise_for_status()
    perks = response.json()

    data = []
    for perk in perks:
        eog = perk.get("endOfGameStatDescs") or []
        var_descs = []
        for i in range(3):  # modified: loop instead of function
            var_descs.append(eog[i] if i < len(eog) else None)

        data.append(
            {
                "perk_id": perk["id"],
                "perk_name": perk["name"],
                "var1_desc": var_descs[0],
                "var2_desc": var_descs[1],
                "var3_desc": var_descs[2],
            }
        )

    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO perks (perk_id, perk_name, var1_desc, var2_desc, var3_desc)
                VALUES (%(perk_id)s, %(perk_name)s, %(var1_desc)s, %(var2_desc)s, %(var3_desc)s)
                """,
                data,
            )
        conn.commit()


if __name__ == "__main__":
    main()
