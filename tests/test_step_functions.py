import os
import pytest
import sys

test_dir = os.path.dirname(__file__)
package_dir = os.path.normpath(os.path.join(test_dir, '../'))
sys.path.append(package_dir)
from awsomeutils.step_functions import mark_as_failed, mark_as_processed

#######################################################################################################
#
#  TestMarkAsFailed
#
#######################################################################################################
class TestMarkAsFailed:
    def test_kwargs(self):
        with pytest.raises(ValueError):
            mark_as_failed()

        with pytest.raises(ValueError):
            mark_as_failed(jobs='foo')

        with pytest.raises(ValueError):
            mark_as_failed(jobs=[], failed_jobs='foo', processed_jobs=[])

        with pytest.raises(ValueError):
            mark_as_failed(jobs=[], failed_jobs=[], processed_jobs='bar')

        with pytest.raises(ValueError):
            mark_as_failed(jobs=[], failed_jobs=[], processed_jobs=[])

    def test_move_failed_job(self):
        kwargs = {"jobs": [{"job_#": 1}, {"job_#": 2}, {"job_#": 3}]}
        jobs_len = len(kwargs['jobs'])
        failed_job = kwargs['jobs'][0]
        result = mark_as_failed(**kwargs)
        assert result['failed_jobs'][-1] == failed_job
        assert len(result['jobs']) == jobs_len -1 

#######################################################################################################
#
#  TestMarkAsProcessed
#
#######################################################################################################
class TestMarkAsProcessed:
    def test_kwargs(self):
        with pytest.raises(ValueError):
            mark_as_processed()

        with pytest.raises(ValueError):
            mark_as_processed(jobs='foo')

        with pytest.raises(ValueError):
            mark_as_processed(jobs=[], failed_jobs='foo', processed_jobs=[])

        with pytest.raises(ValueError):
            mark_as_processed(jobs=[], failed_jobs=[], processed_jobs='bar')

        with pytest.raises(ValueError):
            mark_as_processed(jobs=[], failed_jobs=[], processed_jobs=[])

    def test_move_processed_job(self):
        kwargs = {"jobs": [{"job_#": 1}, {"job_#": 2}, {"job_#": 3}]}
        jobs_len = len(kwargs['jobs'])
        processed_job = kwargs['jobs'][0]
        result = mark_as_processed(**kwargs)
        assert result['processed_jobs'][-1] == processed_job
        assert len(result['jobs']) == jobs_len -1 
