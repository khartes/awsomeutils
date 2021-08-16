import boto3
import json
import os
from string import Template
from .safe_kwargs import safe_kwargs

PATH_REGEX = r'^[a-zA-Z0-9_/-]*[^/]$'
FILE_KEY_REGEX = r'^([a-zA-Z0-9_-]+[a-zA-Z0-9_-]*/)*([a-zA-Z0-9_-]*\.[a-zA-Z0-9_]+)$'

#######################################################################################################
#
#  list_files
#
#######################################################################################################
@safe_kwargs({
    'bucket_name': {'required': True, 'type': 'string'},
    'path': {'required': True, 'type': 'string', 'regex': PATH_REGEX}
})
def list_files(**kwargs):
    try:
        s3 = boto3.client('s3')
        files = []
        path = kwargs['path'] + '/'
        path_depth = len(path.split('/'))

        response = s3.list_objects_v2(Bucket=kwargs['bucket_name'], Prefix=path)

        for content in response['Contents']:
            content_depth = len(content['Key'].split('/'))
            if content_depth - path_depth > 0: continue
            
            file_name = os.path.basename(content['Key'])
            if not file_name: continue
            
            files.append(content['Key'])

        files.sort()

        return [ { 'file_name': file } for file in files ]

    except Exception as e:
        raise e

#######################################################################################################
#
#  populate_template
#
#######################################################################################################
@safe_kwargs({
    'input_type': {'required': True, 'type': 'string', 'oneof': [{'allowed': ['file']}, {'allowed': ['text'], 'dependencies': {'output_type': 'text'}}, {'allowed': ['text'], 'dependencies': 'output_file'}]},
    'input_file': {'required': True, 'type': 'string', 'regex': FILE_KEY_REGEX, 'allof':[{'dependencies': {'input_type': 'file'}}, {'dependencies': 'bucket_name'}], 'excludes': 'input_text'},
    'input_text': {'required': True, 'type': 'string', 'dependencies': {'input_type': 'text'}, 'excludes': 'input_file'},
    'substitutions': {'required': True, 'type': 'dict', 'keysrules': {'type': 'string'}, 'valuesrules': {'type': 'string'}},
    'output_type': {'required': True, 'type': 'string', 'oneof': [{'allowed': ['text']}, {'allowed': ['file'], 'dependencies': 'output_file'}, {'allowed': ['file'], 'dependencies': 'output_path'}]},
    'output_file': {'type': 'string', 'regex': FILE_KEY_REGEX, 'dependencies': 'bucket_name', 'excludes': 'output_path'},
    'output_path': {'type': 'string', 'regex': PATH_REGEX, 'dependencies': 'bucket_name', 'excludes': 'output_file'},
    'bucket_name': {'type': 'string'}
})
def populate_template(**kwargs):
    try:
        s3 = boto3.resource('s3')

        input = ''
        if kwargs['input_type'] == 'file':
            obj = s3.Object(kwargs['bucket_name'], kwargs['input_file'])
            input = obj.get()['Body'].read().decode('utf-8')
        else:
            input = kwargs['input_text']

        output = Template(input).safe_substitute(**kwargs['substitutions'])

        if kwargs['output_type'] == 'text':
            return output
        else:
            if input == output:
                return kwargs['input_file']
            else:
                output_file = kwargs.get('output_file', '')
                if not output_file:
                    output_file = kwargs['output_path'] + '/' + os.path.basename(kwargs['input_file'])
                obj = s3.Object(kwargs['bucket_name'], output_file)
                obj.put(Body=output)
                return output_file

    except Exception as e:
        raise e

#######################################################################################################
#
#  read_json_file
#
#######################################################################################################
@safe_kwargs({
    'bucket_name': {'required': True, 'type': 'string'},
    'file_key': {'required': True, 'type': 'string', 'regex': FILE_KEY_REGEX}
})
def read_json_file(**kwargs):
    try:
        s3 = boto3.resource('s3')
        obj = s3.Object(kwargs['bucket_name'], kwargs['file_key'])
        body = obj.get()['Body'].read().decode('utf-8')      
        
        return json.loads(body)

    except Exception as e:
        raise e
