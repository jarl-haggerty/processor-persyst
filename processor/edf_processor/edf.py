import sys
import struct
import re
import numpy as np
from datetime import datetime

second_to_usecond = 1000000

def twosComp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

def transformValue(val, phys_min, phys_max, dig_min, dig_max, bits):
    two_comped_val = twosComp(val, bits)
    bit_value = (phys_max - phys_min) /(dig_max - dig_min)
    offset = (phys_max / bit_value) - dig_max
    return bit_value * (offset + float(two_comped_val))

class EdfReader():
    """
    Simple interface for EDF, EDF+C and EDF+D files
    """
    
    def __init__ (self,filename):
        self.open(filename)
    
    def __enter__(self):
        return self

    def __exit__(self,exception_type, exception_value, traceback):
        return

    def open(self,filename):
        with open(filename, "rb") as f:
            self.version = f.read(8).strip().decode('utf-8', 'ignore')
            self.patient_id = f.read(80).strip().decode('utf-8', 'ignore')
            self.record_id = f.read(80).strip().decode('utf-8', 'ignore')
            self.start_date = f.read(8).strip().decode('utf-8', 'ignore')
            self.start_time = f.read(8).strip().decode('utf-8', 'ignore')
            self.nb_bytes = int(f.read(8))
            self.reserved = f.read(44).strip()
            self.nb_data_rec = int(f.read(8))
            self.duration = float(f.read(8))
            self.nb_signal = int(f.read(4))
            self.labels = [y.strip().decode('utf-8', 'ignore') for y in re.findall(b'.{1,16}', f.read(16 * self.nb_signal))]
            self.transducer_type = [y.strip().decode('utf-8', 'ignore') for y in re.findall(b'.{1,80}', f.read(80 * self.nb_signal))]
            self.phy_dim = [y.strip().decode('utf-8', 'ignore') for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.phy_min = [float(y) for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.phy_max = [float(y) for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.dig_min = [float(y) for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.dig_max = [float(y) for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.prefiltering = [y.strip().decode('utf-8', 'ignore') for y in re.findall(b'.{1,80}', f.read(80 * self.nb_signal))]
            self.nr_samples = [int(y) for y in re.findall(b'.{1,8}', f.read(8 * self.nb_signal))]
            self.reserved_signal = [y.strip().decode('utf-8', 'ignore') for y in re.findall(b'.{1,32}', f.read(32 * self.nb_signal))]
            self.data_signal = []
            self.rec_start_time = []
            self.annotations = []
            for x in range(self.nb_signal):
                if self.labels[x] != "EDF Annotations":
                    self.data_signal.append(np.array([]))
            for y in range(self.nb_data_rec):
                self.rec_start_time.append([])
                for x in range(self.nb_signal):
                    if self.labels[x] == "EDF Annotations":
                        segment = f.read(2 * self.nr_samples[x])
                        self.annotations.append(segment)
                        if self.reserved == "EDF+D":
                            split_segment = segment.split(b"\x14\x14")
                            self.rec_start_time[y] = float(split_segment[0])
                    else:
                        block = f.read(2 * self.nr_samples[x])
                        segment = [block[i:i + 2] for i in range(0, len(block), 2)]
                        self.data_signal[x] = np.append(self.data_signal[x], [
                            transformValue(struct.unpack('<H', z)[0], self.phy_min[x], self.phy_max[x], self.dig_min[x],
                                            self.dig_max[x], 16) for z in segment])
    
    def getNSamples(self):
        return [x* self.nb_data_rec for x in self.nr_samples] 

    def getSignalLabels(self):
        return self.labels
   
    def getRecordStartTime(self,i):
        return self.rec_start_time[i]
    
    def getNumberOfDataRecords(self):
        return self.nb_data_rec

    def getNrSamples(self,i):
        return self.nr_samples[i]

    def getSampleFrequency(self, i):
        return float(self.nr_samples[i]) / self.duration

    def getPhysicalDimension(self,i):
        return self.phy_dim[i]

    def getStartdatetime(self):
        split_start_date=self.start_date.split(".")
        split_start_time=self.start_time.split(".")
        year=int(split_start_date[2])+1900
        if (year<1985):
            year=year+100
        month=int(split_start_date[1])
        day=int(split_start_date[0])
        hour=int(split_start_time[0])
        minute=int(split_start_time[1])
        second=int(split_start_time[2])
        return datetime(year, month, day, hour, minute, second)

    def getTimestamps(self, index, signal_number, start_time) :
        #start_time is in usecs sine epoch
        start_time_record = start_time + self.getRecordStartTime(index) * second_to_usecond  
        end_time_record = start_time_record + second_to_usecond * self.getDuration() 
        return np.linspace(start_time_record, end_time_record, num=self.getNrSamples(signal_number), endpoint=False) 
  
    def isDiscontiguous(self):
        return (self.reserved == "EDF+D")

    def getDuration(self):
        return self.duration
    
    def getAnnotations(self):
        return self.annotations

    def readSignal(self, i, start,end):
        return self.data_signal[i][start:end]
