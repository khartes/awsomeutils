import boto3
import json
import os
import pytest
import sys
from moto import mock_s3

os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

test_dir = os.path.dirname(__file__)
package_dir = os.path.normpath(os.path.join(test_dir, '../'))
sys.path.append(package_dir)
from awsomeutils.s3 import list_files, populate_template, read_json_file

#######################################################################################################
#
#  TestListFiles
#
#######################################################################################################
files = [
    {
        'key': 'path/file1',
        'body': 'file 1'
    }, {
        'key': 'path/to/file2.1',
        'body': 'file 2.1'
    }, {
        'key': 'path/to/file2.2',
        'body': 'file 2.2'
    }, {
        'key': 'path/to/files/file3.1',
        'body': 'file 3.1'
    }, {
        'key': 'path/to/files/file3.2',
        'body': 'file 3.2'
    }, {
        'key': 'path/to/files/file3.3',
        'body': 'file 3.3'
    } 
]

@mock_s3
class TestListFiles:
    def test_list_files(self):
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test')
        for file in files:
            s3.put_object(Bucket='test', Key=file['key'], Body=file['body'])

        list_1 = list_files(bucket_name='test', path='path')
        assert len(list_1) == 1
        assert list_1[0]['file_name'] == files[0]['key']

        list_2 = list_files(bucket_name='test', path='path/to')
        assert len(list_2) == 2
        assert list_2[0]['file_name'] == files[1]['key']
        assert list_2[1]['file_name'] == files[2]['key']
        
        list_3 = list_files(bucket_name='test', path='path/to/files')
        assert len(list_3) == 3
        assert list_3[0]['file_name'] == files[3]['key']
        assert list_3[1]['file_name'] == files[4]['key']
        assert list_3[2]['file_name'] == files[5]['key']

#######################################################################################################
#
#  TestPopulateTemplate
#
#######################################################################################################
input = '${foo} ${bar} dolor sit amet, consectetur adipiscing elit.'
substitutions = {'foo': 'Lorem', 'bar': 'ipsum'}
output = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'

@mock_s3
class TestPopulateTemplate:
    def test_input_text_output_text(self):
        with pytest.raises(ValueError):
            populate_template(input_type='text', output_type='text')
        with pytest.raises(ValueError):
            populate_template(input_type='text', input_text=input, output_type='text')

        event = {
            'input_type': 'text',
            'input_text': input,
            'substitutions': substitutions,
            'output_type': 'text'    
        }
        assert populate_template(**event) == output

    def test_input_text_output_file(self):
        with pytest.raises(ValueError):
            populate_template(input_type='text', input_text=input, substitutions=substitutions, output_type='file')
        with pytest.raises(ValueError):
            populate_template(input_type='text', input_text=input, substitutions=substitutions, output_type='file', output_file='file.txt')

        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test')
        event = {
            'input_type': 'text',
            'input_text': input,
            'substitutions': substitutions,
            'output_type': 'file',
            'output_file': 'output.txt',
            'bucket_name': 'test'    
        }
        assert populate_template(**event) == 'output.txt'

        s3 = boto3.resource('s3')
        assert s3.Object('test', 'output.txt').get()['Body'].read().decode('utf-8') == output      

    def test_input_file_output_text(self):
        with pytest.raises(ValueError):
            populate_template(input_type='file', substitutions=substitutions, output_type='text')
        with pytest.raises(ValueError):
            populate_template(input_type='file', input_file='file.txt', substitutions=substitutions, output_type='text')

        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test')
        s3.put_object(Bucket='test', Key='input.txt', Body=input)
        event = {
            'input_type': 'file',
            'input_file': 'input.txt',
            'substitutions': substitutions,
            'output_type': 'text',
            'bucket_name': 'test'    
        }
        assert populate_template(**event) == output

    def test_input_file_output_file(self):
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test')
        s3.put_object(Bucket='test', Key='input.txt', Body=input)
        event = {
            'input_type': 'file',
            'input_file': 'input.txt',
            'substitutions': substitutions,
            'output_type': 'file',
            'output_file': 'output.txt',
            'output_path': 'tmp',
            'bucket_name': 'test'    
        }

        with pytest.raises(ValueError):
            populate_template(**event)

        s3 = boto3.resource('s3')
        del event['output_path']
        assert populate_template(**event) == 'output.txt'
        assert s3.Object('test', 'output.txt').get()['Body'].read().decode('utf-8') == output      

        del event['output_file']
        event['output_path'] = 'tmp'
        assert populate_template(**event) == 'tmp/input.txt'
        assert s3.Object('test', 'tmp/input.txt').get()['Body'].read().decode('utf-8') == output      

#######################################################################################################
#
#  TestReadJsonFile
#
#######################################################################################################
some_data = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3'
}

@mock_s3
class TestReadJsonFile:
    def test_read_json_file(self):
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test')
        s3.put_object(Bucket='test', Key='test_data.json', Body=json.dumps(some_data))
        assert some_data == read_json_file(bucket_name='test', file_key='test_data.json')
