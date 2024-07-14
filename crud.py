from typing import List, Optional, Union

from lnbits.helpers import urlsafe_short_hash
from lnbits.lnurl import encode as lnurl_encode
from . import db
from .models import CreateEightBallData, EightBall
from loguru import logger
from fastapi import Request
from lnurl import encode as lnurl_encode
import shortuuid


async def create_eightball(
    wallet_id: str, data: CreateEightBallData, req: Request
) -> EightBall:
    eightball_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO eightball.maintable (id, wallet, name, lnurlpayamount, wordlist)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            eightball_id,
            wallet_id,
            data.name,
            data.lnurlpayamount,
            data.wordlist,
        ),
    )
    eightball = await get_eightball(eightball_id, req)
    assert eightball, "Newly created table couldn't be retrieved"
    return eightball


async def get_eightball(
    eightball_id: str, req: Optional[Request] = None
) -> Optional[EightBall]:
    row = await db.fetchone(
        "SELECT * FROM eightball.maintable WHERE id = ?", (eightball_id,)
    )
    if not row:
        return None
    rowAmended = EightBall(**row)
    if req:
        rowAmended.lnurlpay = lnurl_encode(
            req.url_for("eightball.api_lnurl_pay", eightball_id=row.id)._url
        )
     
    return rowAmended


async def get_eightballs(
    wallet_ids: Union[str, List[str]], req: Optional[Request] = None
) -> List[EightBall]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM eightball.maintable WHERE wallet IN ({q})", (*wallet_ids,)
    )
    tempRows = [EightBall(**row) for row in rows]
    if req:
        for row in tempRows:
            row.lnurlpay = lnurl_encode(
                req.url_for("eightball.api_lnurl_pay", eightball_id=row.id)._url
            )
    return tempRows


async def update_eightball(
    eightball_id: str, req: Optional[Request] = None, **kwargs
) -> EightBall:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE eightball.maintable SET {q} WHERE id = ?",
        (*kwargs.values(), eightball_id),
    )
    eightball = await get_eightball(eightball_id, req)
    assert eightball, "Newly updated eightball couldn't be retrieved"
    return eightball


async def delete_eightball(eightball_id: str) -> None:
    await db.execute(
        "DELETE FROM eightball.maintable WHERE id = ?", (eightball_id,)
    )
