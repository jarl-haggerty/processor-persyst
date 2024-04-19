import traceback
from base_processor.timeseries import BaseTimeSeriesProcessor
from base_processor.timeseries.base import chunks
import base_processor.timeseries.utils as utils
from edf_processor.edf import EdfReader

class EdfProcessor(BaseTimeSeriesProcessor):

    def task(self):
        file_path = self.inputs['file']

        try:
            with EdfReader(file_path) as edf_file:
                n_samples = edf_file.get_n_samples()

                for i, signal_name in enumerate(edf_file.get_signal_labels()):
                    if signal_name == 'EDF Annotations':
                        continue

                    sample_rate = edf_file.get_sample_frequency(i)
                    unit = edf_file.get_physical_dimension(i)

                    if edf_file.is_discontiguous():
                        for index in range(edf_file.get_number_of_data_records()):
                            record_timestamps = edf_file.get_timestamps(index, i, utils.usecs_since_epoch(edf_file.get_start_datetime()))

                            nb_samples_per_record = edf_file.get_nr_samples(i)

                            channel = self.get_or_create_channel(
                                name=str(signal_name).strip(),
                                unit=str(unit),
                                rate=sample_rate,
                                type='continuous'
                            )

                            vals = edf_file.read_signal(i, index * nb_samples_per_record, (index + 1) * nb_samples_per_record)

                            self.write_channel_data(
                                channel=channel,
                                timestamps=record_timestamps[:len(vals)],
                                values=vals
                            )
                    else:
                        start_time = utils.usecs_since_epoch(edf_file.get_start_datetime())
                        length = (n_samples[i] - 1) / sample_rate
                        end_time = int(start_time + length * 1e6)

                        for chunk in chunks(start_time, end_time, n_samples[i]):
                            channel = self.get_or_create_channel(
                                name=str(signal_name).strip(),
                                unit=str(unit),
                                rate=sample_rate,
                                type='continuous'
                            )

                            vals = edf_file.read_signal(i, chunk.start_index, chunk.end_index)

                            self.write_channel_data(
                                channel=channel,
                                timestamps=chunk.timestamps[:len(vals)],
                                values=vals
                            )
        except Exception as e:
            print(traceback.format_exc())

        self.finalize()
