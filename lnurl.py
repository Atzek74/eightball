# Maybe your extension needs some LNURL stuff.
# Here is a very simple example of how to do it.
# Feel free to delete this file if you don't need it.

from http import HTTPStatus
from fastapi import Depends, Query, Request
from . import eightball_ext
from .crud import get_eightball
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger
from typing import Optional
from .crud import update_eightball
from .models import EightBall
import shortuuid

#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################


@eightball_ext.get(
    "/api/v1/lnurl/pay/{eightball_id}",
    status_code=HTTPStatus.OK,
    name="eightball.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    eightball_id: str,
):
    eightball = await get_eightball(eightball_id)
    if not eightball:
        return {"status": "ERROR", "reason": "No eightball found"}
    return {
        "callback": str(
            request.url_for(
                "eightball.api_lnurl_pay_callback", eightball_id=eightball_id
            )
        ),
        "maxSendable": eightball.lnurlpayamount * 1000,
        "minSendable": eightball.lnurlpayamount * 1000,
        "metadata": '[["text/plain", "' + eightball.name + '"]]',
        "tag": "payRequest",
    }


@eightball_ext.get(
    "/api/v1/lnurl/paycb/{eightball_id}",
    status_code=HTTPStatus.OK,
    name="eightball.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    eightball_id: str,
    amount: int = Query(...),
):
    eightball = await get_eightball(eightball_id)
    logger.debug(eightball)
    if not eightball:
        return {"status": "ERROR", "reason": "No eightball found"}

    payment_hash, payment_request = await create_invoice(
        wallet_id=eightball.wallet,
        amount=int(amount / 1000),
        memo=eightball.name,
        unhashed_description=f'[["text/plain", "{eightball.name}"]]'.encode(),
        extra={
            "tag": "EightBall",
            "eightballId": eightball_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return {
        "pr": payment_request,
        "routes": [],
        "successAction": {"tag": "message", "message": f"Paid {eightball.name}"},
    }


#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
## withdraws are unique, removing 'tickerhash' ##
## here and crud.py will allow muliple pulls ####
#################################################


@eightball_ext.get(
    "/api/v1/lnurl/withdraw/{eightball_id}/{tickerhash}",
    status_code=HTTPStatus.OK,
    name="eightball.api_lnurl_withdraw",
)
async def api_lnurl_withdraw(
    request: Request,
    eightball_id: str,
    tickerhash: str,
):
    eightball = await get_eightball(eightball_id)
    if not eightball:
        return {"status": "ERROR", "reason": "No eightball found"}
    k1 = shortuuid.uuid(name=eightball.id + str(eightball.ticker))
    if k1 != tickerhash:
        return {"status": "ERROR", "reason": "LNURLw already used"}

    return {
        "tag": "withdrawRequest",
        "callback": str(
            request.url_for(
                "eightball.api_lnurl_withdraw_callback", eightball_id=eightball_id
            )
        ),
        "k1": k1,
        "defaultDescription": eightball.name,
        "maxWithdrawable": eightball.lnurlwithdrawamount * 1000,
        "minWithdrawable": eightball.lnurlwithdrawamount * 1000,
    }


@eightball_ext.get(
    "/api/v1/lnurl/withdrawcb/{eightball_id}",
    status_code=HTTPStatus.OK,
    name="eightball.api_lnurl_withdraw_callback",
)
async def api_lnurl_withdraw_cb(
    request: Request,
    eightball_id: str,
    pr: Optional[str] = None,
    k1: Optional[str] = None,
):
    assert k1, "k1 is required"
    assert pr, "pr is required"
    eightball = await get_eightball(eightball_id)
    if not eightball:
        return {"status": "ERROR", "reason": "No eightball found"}

    k1Check = shortuuid.uuid(name=eightball.id + str(eightball.ticker))
    if k1Check != k1:
        return {"status": "ERROR", "reason": "Wrong k1 check provided"}

    await update_eightball(
        eightball_id=eightball_id, ticker=eightball.ticker + 1
    )
    await pay_invoice(
        wallet_id=eightball.wallet,
        payment_request=pr,
        max_sat=int(eightball.lnurlwithdrawamount * 1000),
        extra={
            "tag": "EightBall",
            "eightballId": eightball_id,
            "lnurlwithdraw": True,
        },
    )
    return {"status": "OK"}
