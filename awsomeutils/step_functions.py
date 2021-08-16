from .safe_kwargs import safe_kwargs

#######################################################################################################
#
#  mark_as_failed
#
#######################################################################################################
@safe_kwargs({
    'jobs': {'required': True, 'type': 'list', 'minlength': 1},
    'failed_jobs': {'type': 'list'},
    'processed_jobs': {'type': 'list'}
})
def mark_as_failed(**kwargs):
    try:
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
@safe_kwargs({
    'jobs': {'required': True, 'type': 'list', 'minlength': 1},
    'failed_jobs': {'type': 'list'},
    'processed_jobs': {'type': 'list'}
})
def mark_as_processed(**kwargs):
    try:
        jobs = kwargs['jobs']
        processed_jobs = kwargs.get('processed_jobs', [])
        
        processed_jobs.append(jobs.pop(0))

        kwargs['processed_jobs'] = processed_jobs

        return kwargs

    except Exception as e:
        raise e
