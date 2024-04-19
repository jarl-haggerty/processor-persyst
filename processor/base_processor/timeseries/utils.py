import datetime
import pandas as pd
import numpy as np
import quantities as pq

from numpy.compat import long, basestring

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Time-series: helper classes (dirs)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Time-related helpers
#
def infer_sample_rate(index):
    dt_like = False
    if isinstance(index, pd.core.indexes.datetimes.DatetimeIndex):
        ind = index.to_series()
        dt_like = True
    elif isinstance(index, pd.core.indexes.numeric.NumericIndex):
        ind = index.to_series()
    elif isinstance(index, np.ndarray):
        ind = pd.Series(data=index)
    else:
        raise Exception("Cannot infer sample rate; unsupported index type: {}".format(type(index)))

    period = ind.diff().mode()[0]
    if dt_like:
        period = period.total_seconds()*1.0e6
    if period <= 0:
        raise TimeSeriesImportError('Inferred sampling period was 0 or negative.', period=period)
    sample_rate = 1.0e6/period
    return sample_rate, period

def infer_epoch_msecs(thing):
    if isinstance(thing, datetime.datetime):
        return msecs_since_epoch(thing)
    elif isinstance(thingm (int, long,float)):
        # assume milliseconds
        return long(thing)
    elif isinstance(thing, basestring):
        # attempt to convert to msec integer
        return long(thing)
    else:
        raise Exception("Cannot parse date")

def infer_epoch(thing):
    if isinstance(thing, datetime.datetime):
        return usecs_since_epoch(thing)
    elif isinstance(thing, (int, long, float)):
        # assume microseconds
        return long(thing)
    else:
        raise Exception("Cannot parse date")

def secs_since_epoch(the_time):
    the_time = the_time.replace(tzinfo=None)
    # seconds from epoch (float)
    return (the_time-datetime.datetime.utcfromtimestamp(0)).total_seconds()

def msecs_since_epoch(the_time):
    # milliseconds from epoch (integer)
    return long(secs_since_epoch(the_time)*1000)

def usecs_since_epoch(the_time):
    # microseconds from epoch (integer)
    return long(secs_since_epoch(the_time)*1e6)

def usecs_to_datetime(us):
    # convert usecs since epoch to proper datetime object
    return datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(microseconds=long(us))

def secs_to_usecs(seconds):
    # seconds to usecs
    return seconds * 1e6

def convert_to_long(thing):
    if isinstance(thing, pq.Quantity):
        return long(thing.magnitude)
    elif isinstance(thing, (int, long, float)):
        return long(thing)
