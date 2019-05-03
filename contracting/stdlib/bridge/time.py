from datetime import datetime as dt
from datetime import timedelta as td
import decimal

# Redefine a controlled datetime object that feels like a regular Python datetime object but is restricted so that we
# can regulate the user interaction with it to prevent security attack vectors. It may seem redundant, but it guarantees
# security.


class Datetime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        self._datetime = dt(year=year, month=month, day=day, hour=hour,
                            minute=minute, second=second, microsecond=microsecond)

        self.year = self._datetime.year
        self.month = self._datetime.month
        self.day = self._datetime.day
        self.hour = self._datetime.hour
        self.minute = self._datetime.minute
        self.second = self._datetime.second
        self.microsecond = self._datetime.microsecond

    def __lt__(self, other):
        return self._datetime < other._datetime

    def __le__(self, other):
        return self._datetime <= other._datetime

    def __eq__(self, other):
        return self._datetime == other._datetime

    def __ge__(self, other):
        return self._datetime >= other._datetime

    def __gt__(self, other):
        return self._datetime > other._datetime

    def __ne__(self, other):
        return self._datetime != other._datetime


class Timedelta:
    def __init__(self, weeks=0,
                       days=0,
                       hours=0,
                       minutes=0,
                       seconds=0):

        self._timedelta = td(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)

    def __lt__(self, other):
        return self._timedelta < other._timedelta

    def __le__(self, other):
        return self._timedelta <= other._timedelta

    def __eq__(self, other):
        return self._timedelta == other._timedelta

    def __ge__(self, other):
        return self._timedelta >= other._timedelta

    def __gt__(self, other):
        return self._timedelta > other._timedelta

    def __ne__(self, other):
        return self._timedelta != other._timedelta

    # Operator implementations inspired by CPython implementations
    def __add__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days + other._timedelta.days,
                             seconds=self._timedelta.seconds + other._timedelta.seconds)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days - other._timedelta.days,
                             seconds=self._timedelta.seconds - other._timedelta.seconds,)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days * other._timedelta.days,
                             seconds=self._timedelta.seconds * other._timedelta.seconds)
        elif isinstance(other, int):
            return Timedelta(days=self._timedelta.days * other,
                             seconds=self._timedelta.seconds * other)
        elif isinstance(other, float) or isinstance(other, decimal.Decimal):
            raise NotImplementedError('Decimal division on timedeltas not currently supported.')
        return NotImplemented

    def __div__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days * other._timedelta.days,
                             seconds=self._timedelta.seconds * other._timedelta.seconds)
        elif isinstance(other, int):
            return Timedelta(days=self._timedelta.days * other,
                             seconds=self._timedelta.seconds * other)
        elif isinstance(other, float) or isinstance(other, decimal.Decimal):
            raise NotImplementedError('Decimal division on timedeltas not currently supported.')
        return NotImplemented


WEEKS = Timedelta(weeks=1)
DAYS = Timedelta(days=1)
HOURS = Timedelta(hours=1)
MINUTES = Timedelta(minutes=1)
SECONDS = Timedelta(seconds=1)

exports = {
    'datetime': Datetime,
    'timedelta': Timedelta,
    'WEEKS': WEEKS,
    'DAYS': DAYS,
    'HOURS': HOURS,
    'MINUTES': MINUTES,
    'SECONDS': SECONDS
}