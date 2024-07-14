from http import HTTPStatus
import json

import httpx
from fastapi import Depends, Query, Request
from lnurl import decode as decode_lnurl
from loguru import logger
from starlette.exceptions import HTTPException

from lnbits.core.crud import get_user
from lnbits.core.models import Payment
from lnbits.core.services import create_invoice
from lnbits.core.views.api import api_payment
from lnbits.decorators import (
    WalletTypeInfo,
    check_admin,
    get_key_type,
    require_admin_key,
    require_invoice_key,
)

from . import eightball_ext
from .crud import (
    create_eightball,
    update_eightball,
    delete_eightball,
    get_eightball,
    get_eightballs,
)
from .models import CreateEightBallData


#######################################
##### ADD YOUR API ENDPOINTS HERE #####
#######################################

## Get all the records belonging to the user


@eightball_ext.get("/api/v1/myex", status_code=HTTPStatus.OK)
async def api_eightballs(
    req: Request,
    all_wallets: bool = Query(False),
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    wallet_ids = [wallet.wallet.id]
    if all_wallets:
        user = await get_user(wallet.wallet.user)
        wallet_ids = user.wallet_ids if user else []
    return [
        eightball.dict() for eightball in await get_eightballs(wallet_ids, req)
    ]


## Get a single record


@eightball_ext.get("/api/v1/myex/{eightball_id}", status_code=HTTPStatus.OK)
async def api_eightball(
    req: Request, eightball_id: str, WalletTypeInfo=Depends(get_key_type)
):
    eightball = await get_eightball(eightball_id, req)
    if not eightball:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="EightBall does not exist."
        )
    return eightball.dict()


## update a record


@eightball_ext.put("/api/v1/myex/{eightball_id}")
async def api_eightball_update(
    req: Request,
    data: CreateEightBallData,
    eightball_id: str,
    wallet: WalletTypeInfo = Depends(get_key_type),
):
    if not eightball_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="EightBall does not exist."
        )
    eightball = await get_eightball(eightball_id, req)
    assert eightball, "EightBall couldn't be retrieved"

    if wallet.wallet.id != eightball.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your EightBall."
        )
    eightball = await update_eightball(
        eightball_id=eightball_id, **data.dict(), req=req
    )
    return eightball.dict()


## Create a new record


@eightball_ext.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_eightball_create(
    req: Request,
    data: CreateEightBallData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    eightball = await create_eightball(
        wallet_id=wallet.wallet.id, data=data, req=req
    )
    return eightball.dict()


## Delete a record


@eightball_ext.delete("/api/v1/myex/{eightball_id}")
async def api_eightball_delete(
    eightball_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    eightball = await get_eightball(eightball_id)

    if not eightball:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="EightBall does not exist."
        )

    if eightball.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your EightBall."
        )

    await delete_eightball(eightball_id)
    return "", HTTPStatus.NO_CONTENT


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@eightball_ext.post(
    "/api/v1/myex/payment/{eightball_id}", status_code=HTTPStatus.CREATED
)
async def api_tpos_create_invoice(
    eightball_id: str, amount: int = Query(..., ge=1), memo: str = ""
) -> dict:
    eightball = await get_eightball(eightball_id)

    if not eightball:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="EightBall does not exist."
        )

    # we create a payment and add some tags, so tasks.py can grab the payment once its paid

    try:
        payment_hash, payment_request = await create_invoice(
            wallet_id=eightball.wallet,
            amount=amount,
            memo=f"{memo} to {eightball.name}" if memo else f"{eightball.name}",
            extra={
                "tag": "eightball",
                "amount": amount,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    return {"payment_hash": payment_hash, "payment_request": payment_request}
