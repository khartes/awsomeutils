from cerberus import Validator, schema_registry

VALIDATOR = Validator(allow_unknown=True)

#######################################################################################################
#
#  mark_as_failed
#
#######################################################################################################
schema_registry.add('mark_as_failed', {
    'jobs': {'required': True, 'type': 'list'},
    'failed_jobs': {'type': 'list'},
    'processed_jobs': {'type': 'list'}
})
def mark_as_failed(**kwargs):
    try:
        if not VALIDATOR.validate(kwargs, schema_registry.get('mark_as_failed')): raise ValueError(VALIDATOR.errors)

        jobs = kwargs['jobs']
        failed_jobs = kwargs.get('failed_jobs', [])
        
        failed_jobs.append(jobs.pop(0))

        kwargs['failed_jobs'] = failed_jobs

        return kwargs

    except Exception as e:
        raise e

#######################################################################################################
#
#  mark_as_processed
#
#######################################################################################################
schema_registry.add('mark_as_processed', {
    'jobs': {'required': True, 'type': 'list'},
    'failed_jobs': {'type': 'list'},
    'processed_jobs': {'type': 'list'}
})
def mark_as_processed(**kwargs):
    try:
        if not VALIDATOR.validate(kwargs, schema_registry.get('mark_as_processed')): raise ValueError(VALIDATOR.errors)

        jobs = kwargs['jobs']
        processed_jobs = kwargs.get('processed_jobs', [])
        
        processed_jobs.append(jobs.pop(0))

        kwargs['processed_jobs'] = processed_jobs

        return kwargs

    except Exception as e:
        raise e
