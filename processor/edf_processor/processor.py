from base_processor.timeseries import BaseTimeSeriesProcessor
from base_processor.timeseries.base import chunks
import base_processor.timeseries.utils as utils
from edf_processor.edf import EdfReader
import sys

class EdfProcessor(BaseTimeSeriesProcessor):

    def task(self):
        file = self.inputs['file']
        try:
            edf_file = EdfReader(file)
            # sample size for all signals
            n_samples = edf_file.getNSamples()

            # add channels/segments for each signal
            for i, signal_name in enumerate(edf_file.getSignalLabels()):
                samples   = n_samples[i]
                sample_rate = edf_file.getSampleFrequency(i)
                length = (samples - 1) / sample_rate
                start_time_date_obj = edf_file.getStartdatetime().replace(tzinfo=None)
                start_time = utils.usecs_since_epoch(start_time_date_obj)
                end_time = int(start_time + length * 1e6)

                unit = edf_file.getPhysicalDimension(i)

                if (signal_name == 'EDF Annotations'):
                    #ignore the annotation channel"
                    continue
                elif (edf_file.isDiscontiguous()):
                    #For EDF+D, we need to treat each "record" of *duration* seconds separately and use the time 
                    #stamp for each record from the Annotation Channel (wrt to EDF file format specification)
                    for index in range(edf_file.getNumberOfDataRecords()):

                        record_timestamps=edf_file.getTimestamps(index, i, start_time)
                        nb_samples_per_record = edf_file.getNrSamples(i)

                        channel = self.get_or_create_channel(
                            name = str(signal_name).strip(),
                            unit = str(unit),
                            rate = sample_rate,
                            type = 'continuous')
                       
                        vals = edf_file.readSignal(i, index * nb_samples_per_record, (index+1) * nb_samples_per_record )

                        self.write_channel_data(
                            channel = channel,
                            timestamps = record_timestamps[0:len(vals)],
                            values = edf_file.readSignal(i, index * nb_samples_per_record, (index+1) * nb_samples_per_record )
                        )
                else:                    
                    for chunk in chunks(start_time,end_time, samples):
                        # create channel object
                        channel = self.get_or_create_channel(
                            name = str(signal_name).strip(),
                            unit = str(unit),
                            rate = sample_rate,
                            type = 'continuous')

                        vals=edf_file.readSignal(i,chunk.start_index,chunk.end_index)
                        self.write_channel_data(
                            channel = channel,
                            timestamps = chunk.timestamps[0:len(vals)],
                            values = edf_file.readSignal(i,chunk.start_index,chunk.end_index)
                        )
        except Exception as e:
            print(traceback.format_exc())
        self.finalize()
