from db.connections import get_connection


async def get_pitcher_ingestion_status(pitcher_id):
    sql = """
        SELECT hydrated FROM pitcher_ingestion_status WHERE pitcher_id = %s
        """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (pitcher_id,))
            return cur.fetchone()
