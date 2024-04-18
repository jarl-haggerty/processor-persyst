#!/usr/bin/env python

import os
import sys
import time
import json
import logging
import shutil
from collections import namedtuple

# internal
from base_processor.settings import Logging
from base_processor.settings import Settings

class BaseProcessor(object):
    required_inputs = []

    def __init__(self, inputs=None, cli=False):
        '''
        Args:
            files_key : The input field aligned to "input files", if relevant
        '''
        self.settings      = Settings()
        self.LOGGER        = Logging(job_id=self.settings.job_id).logger
        self.inputs        = {} if inputs is None else inputs
        self._use_cmd_args = cli

        self._load_inputs()

    def task(self):
        '''
        Primary task. Must be defined in child class.

        Executed when .run() is called. 

        Method must return all outputs to be published.
        '''
        
        raise Exception("Processor's task method not defined.")

        # return [{output1}, {output2}, etc.]

    def run(self):
        '''
        Executes task defined by specific processor.
        '''
        _start = time.time()

        # Run Task ~~~~~~~~~~~~~~~~
        self.LOGGER.info('Processor started')
        self.task()
        self.LOGGER.info('Processor completed')
        # ~~~~~~~~~~~~~~~~~~~~~~~~~

        _dt = int((time.time() - _start) * 1000)
        self.LOGGER.info('Job complete. Total duration of job in milliseconds: {}'.format(_dt))

    def _load_inputs(self):
        self.LOGGER.info('Loading inputs (from file and/or cmd line)...')
        if self.settings.input_file is not None:
            self.inputs = self._load_inputs_file(self.settings.input_file)
        if self._use_cmd_args:
            self._load_inputs_cmd_line()
        for key in self.required_inputs:
            assert key in self.inputs, "Input key '{}' required.".format(key)

    def _load_inputs_file(self, file):
        '''
        Load processor input values as stored in JSON file.
        '''
        if os.path.exists(file) and file.endswith('.json'):
            try:
                self.LOGGER.info('Loading contents of file as input: {}'.format(file))
                with open(file, 'r') as f:
                    value = json.load(f)
                return value
            except:
                self.LOGGER.info('Error loading file contents: {}'.format(file))
        return file

    def _load_inputs_cmd_line(self, args=sys.argv):
        '''
        Load processor input values from command line. Looks for all
        arguments of the form:

            command --variable=value --variable2=value2

        Notes:
          - If value is valid .json file, will read contents of file
            and assign to variable.
          - If multiple variables of same name are detected, an array
            of  values are created. 
        '''
        args = [arg.split('=',1) for arg in args if '=' in arg]
        for key, value in args:
            self.LOGGER.info('Parsing cmd line arg, {}={}'.format(key, value))
            # remove string literals
            value = value.replace('"','').replace('\'','')
            # proper variable naming
            key = key.replace('--', '').replace('-','_')

            # if contents valid json, use contents as value
            value = self._load_inputs_file(value)

            # assign value to variable
            if key in self.inputs:
                if isinstance(self.inputs[key], list):
                    self.inputs[key].append(value)
                else:
                    self.inputs[key] = [self.inputs[key], value]
            else:
                self.inputs[key] = value

    def publish_outputs(self, key, outputs):
        '''
        Write processor output(s) to file(s) with prefix defined by 'key'.
        For a single output (with key='output'), this will be 'output.json'.
        However, a processor may have multiple outputs which will result in

            'output.json', 'output2.json', etc.

        NOTE: output file(s) are located in the same directory as execution context.

        '''
        if isinstance(outputs, dict): outputs = [outputs]

        for i, output in enumerate(outputs):
            suffix  = '-{index:05d}'.format(index=i) if i > 0 else ''
            outfile = '{}{}.json'.format(key, suffix)
            json.dump(output, open(outfile,'w'))
