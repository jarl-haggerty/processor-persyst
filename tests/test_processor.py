import os
import pytest

from persyst_processor import PersystProcessor
from base_processor.timeseries.tests import timeseries_test
from tests.params import params_global

@pytest.mark.parametrize("ts_expected", params_global)
def test_success(ts_expected):
    task = PersystProcessor(inputs=ts_expected.inputs)

    # Test Persyst Processor
    timeseries_test(task, ts_expected)
