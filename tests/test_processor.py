import os
import pytest

from edf_processor import EdfProcessor
from base_processor.timeseries.tests import timeseries_test
from tests.params import params_global

@pytest.mark.parametrize("ts_expected", params_global)
def test_success(ts_expected):
    task = EdfProcessor(inputs=ts_expected.inputs)

    # Test EDF Processor
    timeseries_test(task, ts_expected)
