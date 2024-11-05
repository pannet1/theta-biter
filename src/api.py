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
    def enter(cls, symbol, ltp, quantity, stop):
        try:
            bargs = None
            sl1 = {}

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
            resp = cls._api.order_place(**sargs)
            send_messages(str(sargs))
            send_messages(f"api responded with {resp} for sell order")
            if resp:
                tp = ltp + stop
                bargs = dict(
                    symbol=symbol,
                    quantity=quantity,
                    product="M",
                    side="B",
                    price=tp + 0.05,
                    trigger_price=tp,
                    order_type="SL",
                    exchange="NFO",
                    tag="stop",
                )
                sl1 = cls._api.order_place(**bargs)
                send_messages(str(bargs))
                send_messages(f"api responded with {sl1}")

        except Exception as e:
            message = f"helper error {e} while placing order"
            send_messages(message)
            print_exc()
        finally:
            return sl1, bargs

    @classmethod
    def close_positions(cls, half=False):
        try:
            for pos in cls._api.positions:
                if pos["quantity"] == 0:
                    continue
                else:
                    quantity = abs(pos["quantity"])
                    quantity = int(quantity / 2) if half else quantity

                send_messages(f"trying to close {pos['symbol']}")

                is_close = False
                if pos["quantity"] < 0:
                    side = "B"
                    is_close = True
                elif quantity > 0:
                    side = "S"
                    is_close = True

                if is_close:
                    args = dict(
                        symbol=pos["symbol"],
                        quantity=quantity,
                        disclosed_quantity=quantity,
                        product="M",
                        side=side,
                        order_type="MKT",
                        exchange="NFO",
                        tag="close",
                    )
                    resp = cls._api.order_place(**args)
                    send_messages(f"api responded with {resp}")
        except Exception as e:
            print(e)

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
                    pnl += pos["urmtom"] + pos["rpnl"]
        except Exception as e:
            message = f"while calculating {e}"
            send_messages(f"api responded with {message}")
        finally:
            return pnl


if __name__ == "__main__":
    import pandas as pd
    from constants import S_DATA

    Helper.api

    # Helper.close_positions()
    resp = Helper.mtm()
    print(resp)

    resp = Helper._api.finvasia.get_order_book()
    if any(resp):
        pd.DataFrame(resp).to_csv(S_DATA + "orders.csv")

    resp = Helper._api.positions
    print(resp)
    if any(resp):
        pd.DataFrame(resp).to_csv(S_DATA + "positions.csv")
