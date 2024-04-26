import re
import sys
import struct
import pathlib
import datetime
import configparser
import numpy as np
from datetime import datetime

SECOND_TO_USECOND = 1000000

def twos_comp(val, bits):
    """Compute the 2's complement of int value val."""
    if (val & (1 << (bits - 1))) != 0:  # If sign bit is set, e.g., 8bit: 128-255
        val = val - (1 << bits)         # Compute negative value
    return val                          # Return positive value as is

def transform_value(val, phys_min, phys_max, dig_min, dig_max, bits):
    two_comped_val = twos_comp(val, bits)
    bit_value = (phys_max - phys_min) / (dig_max - dig_min)
    offset = (phys_max / bit_value) - dig_max
    return bit_value * (offset + float(two_comped_val))

class PersystReader:
    """
    Simple interface for EDF, EDF+C, and EDF+D files.
    """

    def __init__ (self, lay_path: pathlib.Path, dat_path: pathlib.Path):
        self.open(lay_path, dat_path)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return

    def open(self, lay_path: pathlib.Path, dat_path: pathlib.Path):
        assert lay_path is not None, 'No .lay file provided'
        assert dat_path is not None, 'No .dat file provided'
        
        config = configparser.ConfigParser(strict=False)
        config.read(lay_path)
        
        with open(dat_path, 'rb'):

            # Parse layout file for header properties
            header_name = config.get('FileInfo', 'file')
            header_rate = config.getfloat('FileInfo', 'samplingrate')
            header_datatype = config.getint('FileInfo', 'datatype')
            header_calibration = config.getfloat('FileInfo', 'calibration')

            try:
                header_date = config.get('FileInfo', 'testdate')
                header_time = config.get('FileInfo', 'testtime')

                # Compute epoch seconds from given header_date (midnight UTC)
                header_epoch = (datetime.datetime.strptime(header_date, "%m/%d/%y") - datetime.datetime.fromtimestamp(0)).total_seconds()
            except:
                header_epoch = 0

            # Get channels and channel info
            channel_rows = config['ChannelMap']
            num_channels = len(channel_rows)

            # Parse EEG binary, a .dat file, into numpy
            if header_datatype == 7:
                precision = 'int32'
                BYTE_SIZE = 4
            else:
                precision = 'int16'
                BYTE_SIZE = 2

            data_size = dat_path.stat().st_size  # size of EEG binary in bytes
            num_samples = (data_size // num_channels) // BYTE_SIZE
            data = np.memmap(dat_path,
                             dtype=precision,
                             mode='r',
                             shape=(num_channels, num_samples),
                             order='f')

            # Write all channel info (layout + binary data)
            for i, channel_name in enumerate(channel_rows.values()):

                self.LOGGER.debug('Writing Channel: ' + str(i))

                # Get EEG data of channel
                channel_data = header_calibration*data[i]

                # Get segments
                segments = config.get('SampleTimes', {'0': header_epoch})

                unit = 'uV'

                # create channel
                channel = self.get_or_create_channel(
                    name=channel_name.strip(),
                    unit=unit,
                    rate=header_rate,
                    type='continuous')

                # Go through segments and write data to channel
                for j, segment in enumerate(segments.items()):
                    # Compute segment start and end times (see Note)
                    segment_start_epoch = int(1e6*float(segment[1]))

                    first_sample_for_segment = int(segment[0])

                    first_sample_next_segment = num_samples if j == (
                            len(segments) - 1) else int(segments[j + 1][0])

                    # get data segment
                    segment_data = channel_data[first_sample_for_segment:first_sample_next_segment]

                    timestamps = (1e6 * (np.arange(0, len(segment_data))/header_rate)) + segment_start_epoch

                    self.LOGGER.debug('Header Rate: ' + str(header_rate) + ' Sampling rate: ' +
                                      str( 1000000/((timestamps[10]-timestamps[0])/10) ))
                    self.LOGGER.debug('Length data: ' + str(len(segment_data)) + " Length timestamp: "
                                      + str(len(timestamps)))
                    self.LOGGER.debug('Writing Segment: ' + str(j) + 'timestamp 1: '
                                      + str(timestamps[0])+", " + str(timestamps[1]))

                    self.write_channel_data(
                        channel=channel,
                        timestamps=timestamps,
                        values=segment_data)

                self.finalize()
