from base_processor.timeseries.tests import TimeSeriesTest

# -----------------------------
# parameters for global tests
# -----------------------------

params_global = [
    TimeSeriesTest(
        name      = 'persyst-test-HUP',
        nchannels = 4,
        template  = False,
        nsamples  = 325438,
        result    = 'pass',
        rate      = 250,
        inputs    = {
            'file': [
                'sample_data/HUP1234_2000_02.dat',
                'sample_data/HUP1234_2000_02.lay'
            ]
        }),
  TimeSeriesTest(
    name      = 'persyst-test-3',
    nchannels = 2,
    template  = True,
    nsamples  = 12000,
    result    = 'pass',
    rate      = 800,
    inputs    = {
        'file': [
            'sample_data/wave_sin.dat',
            'sample_data/wave_sin.lay'
        ]
    }),
  TimeSeriesTest(
    name      = 'persyst-test-2',
    nchannels = 4,
    nsamples  = 7587,
    result    = 'pass',
    rate      = 250,
    inputs    = {
        'file': [
            'sample_data/130998627754330000.DAT',
            'sample_data/130998627754330000.lay'
        ]
    }),
  TimeSeriesTest(
    name      = 'persyst-test',
    nchannels = 35,
    nsamples  = 930749,
    result    = 'pass',
    rate      = 256,
    inputs    = {
        'file': [
            'sample_data/test-persyst.dat',
            'sample_data/test-persyst.lay'
        ]
    }),
]
