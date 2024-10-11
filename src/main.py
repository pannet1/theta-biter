from symbols import Symbols
from strategy import Strategy
from constants import O_SETG


def main():
    try:
        base = O_SETG["trade"]["base"]
        symbols = Symbols(
            option_exchange=O_SETG[base]["exchange"],
            base=base,
            expiry=O_SETG[base]["expiry"],
        )
        symbols.get_exchange_token_map_finvasia()
        sgy = Strategy(quantity=O_SETG[base]["quantity"], symbols=symbols)

        while True:
            sgy.run()
    except KeyboardInterrupt as k:
        print(f"{k} due to keyboardInterrupt")
    except Exception as e:
        print(f"{e} in run")


if __name__ == "__main__":
    main()
