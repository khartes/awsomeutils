import os
import pytest
import sys

test_dir = os.path.dirname(__file__)
package_dir = os.path.normpath(os.path.join(test_dir, '../'))
sys.path.append(package_dir)
from awsomeutils.safe_kwargs import safe_kwargs

#######################################################################################################
#
#  TestFunc
#
#######################################################################################################
@safe_kwargs({
    'input_string': {'required': True, 'type': 'string', 'allowed': ['foo', 'bar']},
    'input_int': {'required': True, 'type': 'integer'}
})
def func(**kwargs):
    return kwargs

class TestFunc:
    def test_required_kwargs(self):
        with pytest.raises(ValueError):
            func()

        with pytest.raises(ValueError):
            func(input_int=123)

        with pytest.raises(ValueError):
            func(input_string='foo')

    def test_wrong_kwargs(self):
        with pytest.raises(ValueError):
            func(input_string='bla', input_int=123)

        with pytest.raises(ValueError):
            func(input_string='foo', input_int='bar')

    def test_correct_kwargs(self):
        kwargs = {'input_string': 'foo', 'input_int': 123}
        assert kwargs == func(**kwargs)

#######################################################################################################
#
#  TestClass
#
#######################################################################################################
class Class:
    @safe_kwargs({
        'input_bool': {'required': True, 'type': 'boolean'},
        'input_list': {'required': True, 'type': 'list', 'schema': {'type': 'string'}}
    })
    def exec(self, **kwargs):
        return kwargs

c = Class()

class TestClass:
    def test_required_kwargs(self):
        with pytest.raises(ValueError):
            c.exec()

        with pytest.raises(ValueError):
            c.exec(input_list=['a', 'b', 'c'])

        with pytest.raises(ValueError):
            c.exec(input_bool=True)

    def test_wrong_kwargs(self):
        with pytest.raises(ValueError):
            c.exec(input_bool='foo', input_list=['a', 'b', 'c'])

        with pytest.raises(ValueError):
            c.exec(input_bool=False, input_list=[1, 2, 3])

    def test_correct_kwargs(self):
        kwargs = {'input_bool': True, 'input_list': ['a', 'b', 'c']}
        assert kwargs == c.exec(**kwargs)
