from traceback import print_exc
import pendulum as pdlm
from symbols import dct_sym
from api import Helper
from toolkit.kokoo import timer
from constants import send_messages, F_SWITCH, logging, O_SETG


class Strategy:

    def __init__(
        self,
        quantity,
        symbols,
    ):
        self._quantity = quantity
        self._symbols = symbols
        self._atm = None
        self._tokens = None
        self._ce = None
        self._pe = None
        self._timer = pdlm.now()
        self.state = 0
        self.exit_value = O_SETG["trade"]["x_amount"]

        Helper.api

    @property
    def atm(self):
        try:
            base = self._symbols._base
            ltp = Helper.ltp(dct_sym[base]["exchange"], dct_sym[base]["token"])
            temp = self._symbols.get_atm(ltp)
            if temp is not None:
                self._atm = temp
            if self._tokens is None:
                self._tokens = self._symbols.get_tokens(self._atm)
        except Exception as e:
            message = f"{e} while atm"
            logging.warning(message)
            send_messages(message)
            print_exc()
        finally:
            return self._atm

    @property
    def is_timeout(self):
        """
        3.  Check for every 1 min, if this has changed update and repeat step 2
        """
        try:
            if pdlm.now() > self._timer:
                self._timer = self._timer.add(seconds=10)
                return True
            return False
        except Exception as e:
            message = f"{e} while is timeout"
            logging.error("message")
            send_messages(message)
            print_exc()

    @property
    def strikes(self):
        """
        1.  Straddle strike will be at the time of button click
        """
        try:
            if self.is_timeout:
                atm = self.atm
                self._ce = self._symbols.find_option_by_distance(
                    atm, 0, "C", self._tokens
                )
                self._pe = self._symbols.find_option_by_distance(
                    atm, 0, "P", self._tokens
                )
                message = f'current strikes:  {self._pe["symbol"]} {self._ce["symbol"]}'
                logging.info(message)
                send_messages(message)
        except Exception as e:
            message = f"{e} while info"
            logging.error(message)
            send_messages(message)
            print_exc()

    def on_tick(self):
        """
        2.  Check the price difference between CE and PE, if the difference is
        less than 10, initiate the straddle, if the difference is more that wait for the price to come closer
        """
        try:

            last_price = Helper.ltp(self._symbols._option_exchange, self._ce["token"])
            if last_price is not None:
                self._ce["last_price"] = last_price

            last_price = Helper.ltp(self._symbols._option_exchange, self._pe["token"])
            if last_price is not None:
                self._pe["last_price"] = last_price

            message = f'pe: {self._pe["last_price"]} ce: {self._ce["last_price"]}'
            logging.info(message)
            send_messages(message)
        except Exception as e:
            message = f"{e} while on tick"
            send_messages(message)
            print_exc()

    @property
    def is_ce_pe_closest(self):
        try:
            base = self._symbols._base
            distance = O_SETG[base]["distance"]
            if abs(self._pe["last_price"] - self._ce["last_price"]) <= distance:
                message = f"differance is lesser than equal to {distance}"
                logging.info(message)
                return True
            timer(1)
            return False
        except Exception as e:
            message = f"{e} while is ce pe closest"
            send_messages(message)
            print_exc()

    def entry(self):
        try:
            """open file to read file"""
            with open(F_SWITCH, "r") as f:
                if int(f.read()) == 1:
                    base = self._symbols._base
                    quantity = int(O_SETG[base]["quantity"])
                    stop = int(O_SETG[base]["stop"])
                    self._ce["sl"], self._ce["bargs"] = Helper.enter(
                        self._ce["symbol"],
                        self._ce["last_price"],
                        quantity,
                        stop,
                    )
                    self._pe["sl"], self._pe["bargs"] = Helper.enter(
                        self._pe["symbol"],
                        self._pe["last_price"],
                        quantity,
                        stop,
                    )
                    self.state = 1
        except Exception as e:
            message = f"{e} while enter"
            logging.error(message)
            send_messages(message)
            print_exc()

    def is_stop_hit(self):
        try:

            # Ensure `_ce` and `_pe` contain expected structure before accessing keys
            ce_last_price = self._ce.get("last_price", None)
            ce_bargs = self._ce.get("bargs", {})
            ce_trigger_price = ce_bargs.get("trigger_price", None)

            pe_last_price = self._pe.get("last_price", None)
            pe_bargs = self._pe.get("bargs", {})
            pe_trigger_price = pe_bargs.get("trigger_price", None)

            # Debug statements to log current values and structure
            if callable(ce_last_price) or callable(ce_trigger_price):
                raise TypeError(
                    f"Invalid type in CE: ce_last_price={ce_last_price}, ce_trigger_price={ce_trigger_price}"
                )
            if callable(pe_last_price) or callable(pe_trigger_price):
                raise TypeError(
                    f"Invalid type in PE: pe_last_price={pe_last_price}, pe_trigger_price={pe_trigger_price}"
                )

            # Perform stop loss checks
            if (
                ce_last_price is not None
                and ce_trigger_price is not None
                and ce_last_price > ce_trigger_price
            ):
                message = "CALL stop loss hit"
                send_messages(message, "important")
                self.state = 2
            elif (
                pe_last_price is not None
                and pe_trigger_price is not None
                and pe_last_price > pe_trigger_price
            ):
                message = "PUT stop loss hit"
                send_messages(message, "important")
                self.state = 2

        except Exception as e:
            # Improved logging to capture actual values and structure at error time
            message = (
                f"{e} while checking stop loss. "
                f"ce: last_price={ce_last_price}, trigger_price={ce_trigger_price}; "
                f"pe: last_price={pe_last_price}, trigger_price={pe_trigger_price}"
            )
            send_messages(message)
            print_exc()

    def run(self):
        try:
            if self.state == 0:
                # check atm and update strikes
                self.strikes
                # update prices
                self.on_tick()
                # check distance
                if self.is_ce_pe_closest:
                    self.entry()

            elif self.state >= 1:
                # update prices
                self.on_tick()

                if self.state == 1:
                    self.is_stop_hit()

                mtm = Helper.mtm()
                if mtm > self.exit_value:
                    Helper.close_positions(half=True)
                    send_messages("PROFIT !", "important")
                    self.state = 3
                elif mtm < self.exit_value * -1:
                    Helper.close_positions()
                    send_messages("PORTFOLIO STOP HIT", "important")
                    __import__("sys").exit()

        except Exception as e:
            message = f"{e} while run"
            logging.error(message)
            send_messages(message)
            print_exc()
