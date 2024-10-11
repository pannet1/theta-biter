from traceback import print_exc
import pendulum as pdlm
from symbols import dct_sym
from api import Helper
from toolkit.kokoo import timer
from constants import send_messages, F_SWITCH, logging, O_SETG


"""
Web or windows based UI In python for Shoonya broker
Straddle trigger button on a button click
5.  If SL order is triggered, print a notification message that sl has been triggered  
6.  Monitor the PNL if this has reached to X amount close half positions
"""


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
            message = f"{e} while is ce pe closes"
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
            message = f"{e} while is ce pe closes"
            send_messages(message)
            print_exc()

    def entry(self):
        try:
            """open file to read file"""
            with open(F_SWITCH, "r") as f:
                if int(f.read()) == 1:
                    base = self._symbols._base
                    quantity = O_SETG[base]["quantity"]
                    stop = O_SETG[base]["stop"]
                    self._ce["sl"], self._ce["bargs"] = Helper.one_side(
                        self._ce["symbol"],
                        self._ce["last_price"],
                        quantity,
                        stop,
                    )
                    self._pe["sl"], self._pe["bargs"] = Helper.one_side(
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
            FLAG = False
            if self._ce["last_price"] > self._ce["bargs"]["trigger_price"]:
                message = "stop loss hit for ce"
                send_messages(message)
                FLAG = True
            elif self._pe["last_price"] > self._pe["bargs"]["trigger_price"]:
                message = "stop loss hit for pe"
                send_messages(message)
                FLAG = True
        except Exception as e:
            message = f"{e} while is stop hit"
            send_messages(message)
            print_exc()
        finally:
            return FLAG

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

            elif self.state == 1:
                # update prices
                self.on_tick()
                self.is_stop_hit()

                mtm = Helper.mtm
                if mtm > self.exit_value:
                    Helper.close_positions(half=True)
                    self.state = 2
                elif mtm < self.exit_value * -1:
                    Helper.close_positions()
                    self.state = 3

        except Exception as e:
            message = f"{e} while run"
            logging.error(message)
            send_messages(message)
            print_exc()
