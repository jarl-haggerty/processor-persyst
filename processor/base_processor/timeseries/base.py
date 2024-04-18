import os
import datetime
import numpy as np

# internal
from base_processor import BaseProcessor
from base_processor.timeseries import utils
from math import ceil

class TimeSeriesChannel(object):
    def __init__(self, name, rate, index, unit, type, group='default'):
        self.id       = None
        # representation
        self.name     = name
        self.rate     = rate
        self.start    = None
        self.end      = None
        self.unit     = unit
        self.type     = type
        self.group    = group
        self.last_annot = 0
        self.properties = []

        # metadata
        self.index      = index
        self.num_values = 0

        # when processor.publish_outputs is called, if output is a single object
        # there is no filename suffix, and thus, we should match that logic here
        # to pair metadata files w/ data files appropriately.
        file_suffix = '-{index:05d}'.format(index=index) if index > 0 else ''
        self.data_file = 'channel{}.ts.bin'.format(file_suffix)

        assert self.type in ['CONTINUOUS', 'UNIT'], "Type must be CONTINUOUS or UNIT"

    def as_dict(self):
        resp = {
            # representation
            'name':  self.name,
            'start': self.start,
            'end':   self.end,
            'unit':  self.unit,
            'rate':  self.rate,
            'type':  self.type,
            'group': self.group,
            'lastAnnotation': self.last_annot,
            'properties': self.properties
        }
        if self.id is not None:
            resp['id'] = self.id
        return resp

    @classmethod
    def from_dict(cls, d, index):
        ch = cls(
            name  = d['name'],
            rate  = d['rate'],
            unit  = d['unit'],
            type  = d['type'].upper(),
            group = d['group'],
            index = index)

        ch.id         = d['id']
        ch.start      = d['start']
        ch.end        = d['end']
        ch.last_annot = d['lastAnnotation']
        ch.properties = d['properties']

        return ch


class TimeSeriesSpike(object):
    '''
    Attributes:
        timestamp: timestamp the spike occurred at
        waveforms: 1xN numpy array of waveforms associated with the spike
        unit (int, optional): unit classification of the spike
    '''
    def __init__(self, timestamp, waveforms=None, unit=0):
        self.timestamp = timestamp
        self.waveforms = waveforms
        self.unit = unit

    def as_dict(self):
        return {
        'timestamp':    self.timestamp,
        'waveforms':    self.waveforms,
        'unit':         self.unit,
        'properties':   []
        }

    def as_json(self):
        return json.dumps(self.as_dict())

class BaseTimeSeriesProcessor(BaseProcessor):
    required_inputs = ['file']

    def __init__(self, *args, **kwargs):
        super(BaseTimeSeriesProcessor, self).__init__(*args, **kwargs)

        self.channels = []

    @property
    def mode(self):
        return self.inputs.get('mode', 'upload').lower()

    @property
    def existing_channels(self):
        return self.inputs.get('channels', None)

    def finalize(self):
        self.publish_outputs('channel', [ch.as_dict() for ch in self.channels])

    def create_spike(self, timestamp, waveforms=None, unit=0):
        return TimeSeriesSpike(
            timestamp  = timestamp,
            waveforms  = waveforms,
            unit       = unit)

    def get_or_create_channel(self, name, rate, unit='uV', type='continuous'):
        """
        Creating a channel means creating a (channel,output-file) pair,
        each of which will be placed into the OUTPUT table.
        """
        index = len(self.channels)
        channel = None # initialize

        # first, check if the channel already  exists in the platform
        if self.mode == 'append':
            channel = self._get_platform_channel(name,rate,type.upper(), index)

        # if remote channel was not found, and there are channel creation
        # requests, check if creation request already exists.
        if channel is None and len(self.channels) > 0:
            channel = self._get_channel_object(name,rate,type.upper())

        # if channel does not exist, create it
        if channel is None:
            # creating new channel
            channel = TimeSeriesChannel(
                name  = name,
                rate  = rate,
                index = index,
                type  = type.upper(),
                unit  = unit)
            self.channels.append(channel)

        # return channel object
        return channel

    def _get_platform_channel(self, name, rate, type, index):
        """
        Find channel existing in the platform. Match using name, rate and
        channel type.
        """
        if self.existing_channels is None:
            self.LOGGER.warning("No channels found. Will create new channel(s), despite append mode")
            return None

        elif self.existing_channels is not None:
            for ch in self.existing_channels:

                # if match exists, return channel
                if (name.lower().strip() == ch['name'].lower().strip()
                    and type.lower().strip() == ch['type'].lower().strip()
                    and abs(1 - (rate/ch['rate'])) < 0.02):

                    self.LOGGER.info('Using existing channel, id={}'.format(ch['id']))
                    channel = TimeSeriesChannel.from_dict(ch, index)
                    self.channels.append(channel)
                    return channel

            self.LOGGER.warning(
                "Could not find matching channel with name='{}' rate={} type={}".format(name, rate, type))


        # no channel match found
        return None

    def _get_channel_object(self, name, rate, type):
        '''
        Find if channel creation request already exists. Match using name,
        rate and channel type.
        '''
        if len(self.channels) > 0:
            for ch in self.channels:
                if ch.name.lower().strip() == name.lower().strip() \
                    and ch.type.lower().strip() == type.lower().strip() \
                    and abs(1 - (float(ch.rate) / rate) < 0.02):
                    # match found
                    return ch

        # no match found
        return None

    def write_spike_data(self, channel, spikes, nsamples, start=0, end=0):
        '''
        write channel spike data to file in this format:
        header:    len_spike_bytes (uint64) | number_spikes (uint64) | number_samples (uint64)
        spikes:    timestamp (uint64) | unit (uint8) ...
        waveforms: [[ waveform_point (float64), waveform_point, ... ]
                    [ waveform_point (float64), waveform_point, ... ]]
            ...
        '''
        num_spikes   = np.int64(len(spikes)).tobytes()
        num_samples  = np.int64(nsamples).tobytes()

        spike_bytes = ''.join([
            spike.timestamp.astype(long).tobytes() + str(bytearray([spike.unit]))
            for spike in spikes
        ])

        # define waveform offset
        waveform_offset = np.array(len(spike_bytes)).astype(np.int64).tobytes()

        wf = None
        start = utils.convert_to_long(spikes[0].timestamp)
        end   = utils.convert_to_long(spikes[-1].timestamp)

        for spike in spikes:
            wf = spike.waveforms if wf is None else np.vstack((spike.waveforms,wf))
        wf_bytes = np.array(wf).astype(np.float64).tobytes()

        # write serialized data to file
        with open(channel.data_file,'ab') as f:
            f.write(waveform_offset + num_spikes + num_samples + spike_bytes + wf_bytes)

        start_time = int(utils.infer_epoch(start))
        end_time   = int(utils.infer_epoch(end))

        if channel.end is None or end_time > channel.end:
            channel.end = end_time
        if channel.start is None or start_time < channel.start:
            channel.start = start_time

        self.channels[channel.index] = channel

    def write_channel_data(self, channel, timestamps, values):
        """
        Write channel data. Updates start/end times of channel object as necessary.

        NOTE: timestamps/values are assumed to be in chronological order!
        """
        # save as ts/value pairs: [ts1, val1, ts2, val2, ...]
        interleaved = np.empty((timestamps.size + values.size), dtype=np.float64)
        interleaved[0::2] = timestamps
        interleaved[1::2] = values

        # append serialized interleaved data to file
        with open(channel.data_file,'ab') as f:
            f.write(interleaved.tobytes())

        # update start/end times
        start_time = int(utils.infer_epoch(timestamps[0]))
        end_time   = int(utils.infer_epoch(timestamps[-1]))

        if channel.end is None or end_time > channel.end:
            channel.end = end_time
        if channel.start is None or start_time < channel.start:
            channel.start = start_time

        channel.num_values += values.size

        # replace with updated
        self.channels[channel.index] = channel

class TimeSeriesChunk:
    '''
    Attributes:
        start_index: index at which the chunk starts
        end_index: index at which the chunk ends
        timestamps: the timestamps of each data point in the series
    '''
    def __init__(self, start_index, end_index, timestamps):
        self.start_index = start_index
        self.end_index = end_index
        self.timestamps = timestamps

def chunks(start_time, end_time, nsamples, chunk_size=30000000):
    time_step = (end_time - start_time) / float(nsamples)
    nb_segments = int(ceil(float(nsamples) / chunk_size))

    for cnt in range(0,nb_segments):
        # compute the number of samples in the new chunk, we is either the chunk_size or whatever is left when it is the last chunk
        current_chunk_size = min((nsamples - cnt * chunk_size), chunk_size)
        #compute the start time as the overall start time + the time passed in each previous chunk
        current_start_time = start_time + cnt * chunk_size * time_step
        #compute end time as start time plus the overall time of the chunk
        current_end_time = current_start_time + (current_chunk_size - 1) * time_step
        #create an array of timestamps regularly spaced within the bounds of the chunk
        timestamps = np.linspace(current_start_time, current_end_time, num=current_chunk_size)

        #return the chunk start index, end index and timestamps array
        yield TimeSeriesChunk(cnt * chunk_size, cnt * chunk_size + current_chunk_size, timestamps)
