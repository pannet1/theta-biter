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
        self.is_trade = False

        Helper().api

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
    def strikes(self):
        """
        1.  Straddle strike will be ATM at the time of button click
        """
        try:
            atm = self.atm
            self._ce = self._symbols.find_option_by_distance(atm, 0, "C", self._tokens)
            self._pe = self._symbols.find_option_by_distance(atm, 0, "P", self._tokens)
            message = f'current strikes:  {self._pe["symbol"]} {self._ce["symbol"]}'
            logging.info(message)
            send_messages(message)
        except Exception as e:
            message = f"{e} while info"
            logging.error(message)
            send_messages(message)
            print_exc()

    @property
    def is_timeout(self):
        """
        3.  Check for the ATM strikes at every 1 min, if this has changed update the strikes and repeat step 2
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
    def is_ce_pe_closest(self):
        """
        2.  Check the price difference between CE and PE, if the difference is
        less than 10, initiate the straddle, if the difference is more that wait for the price to come closer
        """
        try:

            base = self._symbols._base
            distance = O_SETG[base]["distance"]
            last_price = Helper.ltp(self._symbols._option_exchange, self._ce["token"])
            if last_price is not None:
                self._ce["last_price"] = last_price

            last_price = Helper.ltp(self._symbols._option_exchange, self._pe["token"])
            if last_price is not None:
                self._pe["last_price"] = last_price

            message = f'pe: {self._pe["last_price"]} ce: {self._ce["last_price"]}'
            logging.info(message)
            send_messages(message)
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

    @property
    def entry(self):
        try:
            """open file to read file"""
            with open(F_SWITCH, "r") as f:
                if (int(f.read()) == 1) and not self.is_trade:
                    Helper.one_side(self._ce["symbol"])
                    Helper.one_side(self._pe["symbol"])
                    self.is_trade = True
        except Exception as e:
            message = f"{e} while enter"
            logging.error(message)
            send_messages(message)
            print_exc()

    def run(self):
        try:
            self.atm

            if self.is_ce_pe_closest:
                self.entry

            if self.is_timeout:
                self.strikes
        except Exception as e:
            message = f"{e} while run"
            logging.error(message)
            send_messages(message)
            print_exc()
