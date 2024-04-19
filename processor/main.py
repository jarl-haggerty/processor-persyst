#!/usr/bin/env python3.12

from edf_processor import EdfProcessor

task = EdfProcessor(inputs = { 'file': '/data/input/test.edf' })
task.run()
