import os
import json
import time
import logging
import logging.config

class Settings(object):
    def __init__(self):
        '''
        The Settings class enables processors to initiate settings
        within the scope of the processor itself. This is a beneficial approach
        since our settings load values dynamically from AWS SSM. By avoiding the
        singleton pattern of a flat settings module, we are able to effectively
        test settings in local development with mock SSM per test.
        '''

        self.job_id            = os.environ.get('IMPORT_ID')
        self.environment       = os.environ.get('ENVIRONMENT')
        self.aws_batch_job_id  = os.environ.get('AWS_BATCH_JOB_ID')
        self.aws_region_name   = os.environ.get('AWS_REGION_NAME', 'us-east-1')
        self.scratch_dir       = os.environ.get('SCRATCH_DIR', '/docker_scratch')
        self.encryption_key_id = os.environ.get('ENCRYPTION_KEY_ID')
        self.storage_directory = os.environ.get('STORAGE_DIRECTORY')

        # get inputs from JSON file (useful for testing)
        self.input_file       = os.environ.get('INPUT_FILE', None)

        # optional endpoints for local testing
        self.s3_endpoint      = os.environ.get('S3_ENDPOINT', None)
        self.ssm_endpoint     = os.environ.get('SSM_ENDPOINT', None)

        self.local_directory  = '{dir}/{base}'.format(
            dir   = self.scratch_dir,
            base  = self.aws_batch_job_id)

        # load
        env = self.environment

class UTCFormatter(logging.Formatter):
    '''Convert logging timestamp to UTC'''
    converter = time.gmtime

class Logging(object):
    def __init__(self, *args, **kwargs):
        '''Configure logging format'''

        log_level        = os.environ.get('LOG_LEVEL', 'INFO')
        log_level_sentry = os.environ.get('LOG_LEVEL_SENTRY', 'ERROR')
        sentry_address   = os.environ.get('SENTRY_ADDRESS', '')

        LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'utc': {
                    '()': UTCFormatter,
                    'format': '[%(levelname)s] [%(module)s] - %(message)s',
                    'datefmt': '%Y-%m-%dT%H:%M:%OS'
                }
            },
            'handlers': {
                'blackfynn': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'utc',
                }
            },
            'root': {
                'handlers': ['blackfynn'],
                'level': log_level,
           }
        }

        logging.config.dictConfig(LOGGING)
        self.logger = logging.getLogger()
