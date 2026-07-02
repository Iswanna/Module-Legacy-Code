import datetime

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data.connection import db_cursor
from data.users import User

from psycopg2.errors import UniqueViolation

@dataclass
class Bloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime
    rebloomer_username: str = None
    rebloom_count: int = 0
    is_rebloomed_by_me: bool = False


def add_bloom(*, sender: User, content: str) -> Bloom:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def get_blooms_for_user(
    username: str, *, viewer_id: Optional[int] = None, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {
            "sender_username": username,
            "viewer_id": viewer_id
        }
        if before is not None:
            before_clause = "AND send_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before
        else:
            before_clause = ""

        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp,
              COUNT(reblooms.id),
              EXISTS (
                  SELECT 1 FROM reblooms 
                  WHERE reblooms.bloom_id = blooms.id 
                  AND rebloomer_id = %(viewer_id)s
              )
            FROM
              blooms 
              INNER JOIN users ON users.id = blooms.sender_id
              LEFT JOIN reblooms ON reblooms.bloom_id = blooms.id
            WHERE
              username = %(sender_username)s
              {before_clause}
            GROUP BY 
              blooms.id, users.username, content, send_timestamp
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            # 1. Provide a name for every column in the SQL (order matters!)
            bloom_id, sender_username, content, timestamp, count, rebloomed_by_me = row
            # 2. Use those names to build the object
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    rebloom_count=count,
                    is_rebloomed_by_me=rebloomed_by_me
                )
            )
    return blooms


def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT blooms.id, users.username, content, send_timestamp FROM blooms INNER JOIN users ON users.id = blooms.sender_id WHERE blooms.id = %s",
            (bloom_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        bloom_id, sender_username, content, timestamp = row
        return Bloom(
            id=bloom_id,
            sender=sender_username,
            content=content,
            sent_timestamp=timestamp,
        )


def get_blooms_with_hashtag(
    hashtag_without_leading_hash: str, *, limit: int = None
) -> List[Bloom]:
    kwargs = {
        "hashtag_without_leading_hash": hashtag_without_leading_hash,
    }
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp
            FROM
              blooms INNER JOIN hashtags ON blooms.id = hashtags.bloom_id INNER JOIN users ON blooms.sender_id = users.id
            WHERE
              hashtag = %(hashtag_without_leading_hash)s
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                )
            )
    return blooms


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause


def add_rebloom(*, rebloomer: User, original_bloom_id: int):
    now = datetime.datetime.now(tz=datetime.UTC)
    rebloom_id = int(now.timestamp() * 1000000)

    with db_cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO reblooms (id, rebloomer_id, bloom_id, rebloom_timestamp) VALUES (%(id)s, %(rebloomer_id)s, %(original_id)s, %(timestamp)s)",
                dict(
                    id=rebloom_id,
                    rebloomer_id=rebloomer.id,
                    original_id=original_bloom_id, 
                    timestamp=datetime.datetime.now(datetime.UTC),
                ),
            )
        except UniqueViolation:
            pass

def get_reblooms_for_user(
    username: str, *, viewer_id: Optional[int] = None, limit: Optional[int] = 50
):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT 
                r.id AS id,
                r.rebloom_timestamp AS sent_timestamp, -- We name it the same as the original for sorting!
                rebloomer.username AS rebloomer_username,
                b.content AS content,
                author.username AS sender,
                EXISTS (
                    SELECT 1
                    FROM reblooms viewer_reblooms
                    WHERE viewer_reblooms.bloom_id = b.id
                      AND viewer_reblooms.rebloomer_id = %(viewer_id)s
                ) AS is_rebloomed_by_me
            FROM reblooms r
            JOIN users rebloomer ON r.rebloomer_id = rebloomer.id
            JOIN blooms b ON r.bloom_id = b.id
            JOIN users author ON b.sender_id = author.id
            WHERE rebloomer.username = %(username)s
            ORDER BY r.rebloom_timestamp DESC
            LIMIT %(limit)s
            """,
            {
                "username": username,
                "viewer_id": viewer_id,
                "limit": limit,
            },
        )
        rows = cur.fetchall()
        results = []
        for row in rows:
            # 1. Unpack the tuple in the EXACT order of your SELECT statement above
            rebloom_id, timestamp, rebloomer, content, original_author, is_rebloomed_by_me = row
            
            # 2. Now these names exist! We can use them to build the object
            b = Bloom(
                id=rebloom_id,
                sender=original_author,
                content=content,
                sent_timestamp=timestamp,
                rebloomer_username=rebloomer,
                is_rebloomed_by_me=is_rebloomed_by_me,
            )
            results.append(b)
    return results