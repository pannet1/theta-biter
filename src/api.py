from traceback import print_exc
from omspy_brokers.finvasia import Finvasia
from constants import logging, O_CNFG, send_messages


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
    def one_side(cls, symbol):
        try:
            args = dict(
                symbol=symbol,
                quantity=15,
                product="M",
                side="S",
                price=0,
                trigger_price=0,
                order_type="MKT",
                exchange="NFO",
                tag="enter",
            )
            send_messages(str(args))
            resp = cls._api.order_place(**args)
            send_messages(f"api responded with {resp}")
        except Exception as e:
            logging.error(f"helper error {e} while placing order")
            print(e)


if __name__ == "__main__":
    Helper.api
    resp = Helper._api.finvasia.get_order_book()
    print(resp)
