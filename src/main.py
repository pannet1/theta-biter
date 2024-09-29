from symbols import Symbols
from strategy import Strategy
from constants import O_SETG


def run():
    try:
        base = O_SETG["trade"]["base"]
        symbols = Symbols(
            option_exchange=O_SETG[base]["exchange"],
            base=base,
            expiry=O_SETG[base]["expiry"],
        )
        symbols.get_exchange_token_map_finvasia()
        strategy = Strategy(quantity=O_SETG[base]["quantity"], symbols=symbols)

        while True:
            strategy.run()
    except KeyboardInterrupt as k:
        print(f"{k} due to keyboardInterrupt")
    except Exception as e:
        print(f"{e} in run")


run()
