from dateutil import parser
from datetime import datetime as dt
'''
Redefine a controlled datetime object that feels like a regular Python datetime object but is restricted so that we
can regulate the user interaction with it to prevent security attack vectors. It may seem redundant, but it guarantees
security.
'''


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


exports = {
    'time.datetime': Datetime
}