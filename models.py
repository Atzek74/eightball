# Data models for your extension

from sqlite3 import Row
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request

from lnbits.lnurl import encode as lnurl_encode
from urllib.parse import urlparse


class CreateEightBallData(BaseModel):
    wallet: Optional[str]
    name: Optional[str]
    wordlist: Optional[str]
    lnurlpayamount: Optional[int]

class EightBall(BaseModel):
    id: str
    wallet: Optional[str]
    name: Optional[str]
    wordlist: Optional[str]
    lnurlpayamount: Optional[int]
    lnurlpay: Optional[str]
 
    @classmethod
    def from_row(cls, row: Row) -> "EightBall":
        return cls(**dict(row))
