from cerberus import Validator, schema_registry

VALIDATOR = Validator(allow_unknown=True)

#######################################################################################################
#
#  @safe_kwargs
#
#######################################################################################################
def safe_kwargs(schema):
    def wrapper(f):
        def validate_kwargs(*args, **kwargs):
            schema_name = f"{args[0].__class__.__name__}.{f.__name__}" if len(args) else f.__name__
            schema_registry.add(schema_name, schema)
            if not VALIDATOR.validate(kwargs, schema_registry.get(schema_name)):
                raise ValueError(VALIDATOR.errors)
            return f(*args, **kwargs)
        return validate_kwargs
    return wrapper
