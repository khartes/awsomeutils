from cerberus import Validator, schema_registry
from functools import wraps

DOC_PLACEHOLDER = '${safe_kwargs}'
DOC_TYPE_MAP = {
    'string': 'str',
    'bytes': 'bytes',
    'integer': 'int',
    'float': 'float',
    'number': 'int or float',
    'boolean': 'bool',
    'datetime': 'datetime.datetime',
    'date': 'datetime.date',
    'dict': 'dict',
    'list': 'list',
    'set': 'set'
}

#######################################################################################################
#
#  @safe_kwargs
#
#######################################################################################################
def safe_kwargs(schema):
    def wrapper(func):
        @wraps(func)
        def validate_kwargs(*args, **kwargs):
            schema_name = f"{args[0].__class__.__name__}.{func.__name__}" if len(args) else func.__name__
            schema_registry.add(schema_name, schema)
            v = SafeKwargsValidator(schema, allow_unknown=True)
            if not v.validate(kwargs, schema_registry.get(schema_name)):
                raise ValueError(v.errors)
            return func(*args, **kwargs)
        validate_kwargs.__doc__ = _expand_docstring(func.__doc__, schema)
        return validate_kwargs
    return wrapper

#------------------------------------------------------------------------------------------------------
#  SafeKwargsValidator
#------------------------------------------------------------------------------------------------------
class SafeKwargsValidator(Validator):
    def _validate_doc(self, constraint, field, value):
        "{'type': 'string'}"
        pass

#------------------------------------------------------------------------------------------------------
#  _expand_docstring
#------------------------------------------------------------------------------------------------------
def _expand_docstring(docstring, schema):
    if not docstring: return

    pos = docstring.find(DOC_PLACEHOLDER)
    if pos == -1: return docstring

    offset = pos - docstring.rfind('\n', 0, pos) - 1

    return docstring.replace(DOC_PLACEHOLDER, _generate_kwargs_doc(schema, offset))

#------------------------------------------------------------------------------------------------------
#  _generate_kwargs_doc
#------------------------------------------------------------------------------------------------------
def _generate_kwargs_doc(schema, offset):
    doc = ''
    linebreak = f"\n{' ' * offset}"
    indent = ' ' * 4

    for key, value in schema.items():
        type = DOC_TYPE_MAP[value['type']]
        if value['type'] == 'list' and value.get('schema', ''):
            type += f" of {DOC_TYPE_MAP[value['schema']['type']]}"
        type += ', optional' if not value.get('required', False) else ''
        doc += f"{key} ({type}): {value.get('doc', key)}{linebreak}"
        if value['type'] == 'dict' and value.get('schema', ''):
            doc += indent + _generate_kwargs_doc(value['schema'], offset + 4) + linebreak

    return doc[0:doc.rfind('\n')]
