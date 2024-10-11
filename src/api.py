from traceback import print_exc
from omspy_brokers.finvasia import Finvasia
from constants import logging, O_CNFG, send_messages, O_SETG


def login():
    api = Finvasia(**O_CNFG)
    if api.authenticate():
        message = "api connected"
        send_messages(message)
        return api
    else:
        send_messages("Failed to authenticate. .. exiting")
        __import__("sys").exit(1)


class Helper:
    _api = None

    @classmethod
    @property
    def api(cls):
        if cls._api is None:
            cls._api = login()
        return cls._api

    @classmethod
    def ltp(cls, exchange, token):
        try:
            resp = cls._api.scriptinfo(exchange, token)
            if resp is not None:
                return float(resp["lp"])
            else:
                raise ValueError("ltp is none")
        except Exception as e:
            message = f"{e} while ltp"
            send_messages(message)
            print_exc()

    @classmethod
    def one_side(cls, symbol, ltp, quantity, stop):
        try:
            bargs = dict(
                symbol=symbol,
                quantity=int(quantity / 2),
                product="M",
                side="B",
                price=0,
                trigger_price=ltp + stop,
                order_type="SLM",
                exchange="NFO",
                tag="stop",
            )
            send_messages(str(bargs))
            sl1 = cls._api.order_place(**bargs)
            send_messages(f"api responded with {sl1}")

            if sl1:
                sl2 = cls._api.order_place(**bargs)
                send_messages(f"api responded with {sl2}")
                if sl2:
                    sargs = dict(
                        symbol=symbol,
                        quantity=quantity,
                        product="M",
                        side="S",
                        price=0,
                        trigger_price=0,
                        order_type="MKT",
                        exchange="NFO",
                        tag="enter",
                    )
                    send_messages(str(sargs))
                    resp = cls._api.order_place(**sargs)
                    send_messages(f"api responded with {resp}")
                    return [sl1, sl2], bargs
        except Exception as e:
            message = f"helper error {e} while placing order"
            send_messages(message)
            print_exc()

    @classmethod
    def close_positions(cls, half=False):
        for pos in cls._api.positions:
            if pos["quantity"] == 0:
                continue
            else:
                quantity = abs(pos["quantity"])
                quantity = int(quantity / 2) if half else quantity

            send_messages(f"trying to close {pos['symbol']}")
            if pos["quantity"] < 0:
                args = dict(
                    symbol=pos["symbol"],
                    quantity=quantity,
                    disclosed_quantity=quantity,
                    product="M",
                    side="B",
                    order_type="MKT",
                    exchange="NFO",
                    tag="close",
                )
                resp = cls._api.order_place(**args)
                send_messages(f"api responded with {resp}")
            elif quantity > 0:
                args = dict(
                    symbol=pos["symbol"],
                    quantity=quantity,
                    disclosed_quantity=quantity,
                    product="M",
                    side="S",
                    order_type="MKT",
                    exchange="NFO",
                    tag="close",
                )
                resp = cls._api.order_place(**args)
                send_messages(f"api responded with {resp}")

    @classmethod
    def mtm(cls):
        try:
            pnl = 0
            positions = [{}]
            positions = cls._api.positions
            """
            keys = [
                "symbol",
                "quantity",
                "last_price",
                "urmtom",
                "rpnl",
            ]
            """
            if any(positions):
                # calc value
                for pos in positions:
                    pnl += pos["urmtom"]
        except Exception as e:
            message = f"while calculating {e}"
            send_messages(f"api responded with {message}")
        finally:
            return pnl


if __name__ == "__main__":
    Helper.api
    resp = Helper._api.finvasia.get_order_book()
    print(resp)
