import pathlib
import datetime
import traceback
import configparser

import numpy

from base_processor.timeseries import BaseTimeSeriesProcessor
from base_processor.timeseries.base import chunks
import base_processor.timeseries.utils as utils
from persyst_processor.persyst import PersystReader

class PersystProcessor(BaseTimeSeriesProcessor):

    def task(self):
        file_paths = (pathlib.Path(t) if isinstance(t, str) else t for t in self.inputs['file'])
        dat_path, lay_path = sorted(file_paths, key=lambda p: p.suffix)
        
        assert lay_path is not None, 'No .lay file provided'
        assert dat_path is not None, 'No .dat file provided'
        
        config = configparser.ConfigParser(strict=False,allow_no_value=True)
        config.read(lay_path)
        
        with open(dat_path, 'rb'):
            # Parse layout file for header properties
            header_rate = config.getfloat('FileInfo', 'samplingrate')
            header_datatype = config.getint('FileInfo', 'datatype')
            header_calibration = config.getfloat('FileInfo', 'calibration')

            try:
                header_date = config.get('FileInfo', 'testdate')
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
            data = numpy.memmap(dat_path,
                                dtype=precision,
                                mode='r',
                                shape=(num_channels, num_samples),
                                order='f')

            # Write all channel info (layout + binary data)
            for i, channel_name in enumerate(channel_rows.keys()):

                self.LOGGER.debug('Writing Channel: ' + str(i))

                # Get EEG data of channel
                channel_data = header_calibration*data[i]

                # Get segments
                segments = config.items('SampleTimes') if 'SampleTimes' in config else [('0', header_epoch)]

                unit = 'uV'

                # create channel
                channel = self.get_or_create_channel(
                    name=channel_name.strip(),
                    unit=unit,
                    rate=header_rate,
                    type='continuous')

                # Go through segments and write data to channel
                for j, segment in enumerate(segments):
                    # Compute segment start and end times (see Note)
                    segment_start_epoch = int(1e6*float(segment[1]))

                    first_sample_for_segment = int(segment[0])

                    first_sample_next_segment = num_samples if j == (
                            len(segments) - 1) else int(segments[j + 1][0])

                    # get data segment
                    segment_data = channel_data[first_sample_for_segment:first_sample_next_segment]

                    timestamps = (1e6 * (numpy.arange(0, len(segment_data))/header_rate)) + segment_start_epoch

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
