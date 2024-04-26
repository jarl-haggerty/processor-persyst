#!/usr/bin/env python3.12

import os
import pathlib
import itertools

from persyst_processor import PersystProcessor

input_dir = pathlib.Path(os.environ.get('INPUT_DIR'))
stem, files = next(itertools.groupby(input_dir.glob('*'), lambda p: p.stem))

if len(input_files) != 1:
    raise Exception("Persyst processor only supports a single file as input")

task = PersystProcessor(inputs = { 'file': list(files) })

task.run()
