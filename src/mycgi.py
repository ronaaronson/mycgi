#!/usr/bin/env python

"""A Python 3 replacement for the deprecated cgi module.

Copyright 2023, Ronald Aaronson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__version__ = '0.0.2'

import multipart
import os
import sys
import json
from urllib.parse import parse_qs, unquote_plus
import io

__all__ = ['Form', 'Field']

class Field:

    """A Field represents a form value"""

    def __init__(self, name, filename, value, file=None):
        """An instance has the following
        attributes:
            1. name:     The form field name.
            2. filename: If this field is for an uploaded file, then the
                         uploaded filename, else None.
            3. value:    The form field value (or an uploaded
                         file's contents as bytes).
            4. file:     If the field value is a string or byte string,
                         then a stream that can be read to get the field's
                         value, else None.
        """
        self.name = name
        self.filename = filename
        if file is None:
            if isinstance(value, str):
                file = io.StringIO(value)
            elif isinstance(value, bytes):
                file = io.BytesIO(value)
        self.file = file
        self.value = value

    def __repr__(self):
        return 'Field({0}, {1}, {2})'.format(repr(self.name), repr(self.filename), repr(self.value))


class Form(dict):

    """A replacement for the deprecated cgi.FieldStorage class.
    Class mycgi.Form implements the important methods of the
    cgi.FieldStorage class as a dictionary whose keys are the form
    field names and whose values are either instances of the Field
    class or a list of these instances.

    Class Form also supports JSON-encoded requests when the data
    being posted is a JSON-encoded dictionary.
    """

    def __init__(self, environ=os.environ, fp=None, keep_blank_values=False):
        """
        Initialize a Form instance.

        Arguments (all are optional):

        environ: environment dictionary
                 default: os.environ

        fp: stream containing encoded POST and PUT data
            default: None (in which case sys.stdin.buffer will be used for
                     POST and PUT requests)

        keep_blank_values: flag indicating whether blank values in
                           percent-encoded forms should be treated as blank
                           strings.
                           default: False
        """
        if 'CONTENT_TYPE' in environ:
            # POST or PUT request:
            if fp is None:
                fp = sys.stdin.buffer
            if environ['CONTENT_TYPE'][0:16] == 'application/json':
                # The assumption is that a dictionary is being passed.
                d = json.loads(fp.read(int(environ['CONTENT_LENGTH'])))
                for k, v in d.items():
                    self[k] = [Field(k, None, value) for value in v] if isinstance(v, list) else Field(k, None, v)
            else:
                headers = {}
                headers['Content-Type'] = environ.get('CONTENT_TYPE')
                multipart.parse_form(headers, fp, self._on_field, self._on_file)
        else:
            # GET or HEAD request
            for k, v in parse_qs(environ['QUERY_STRING'], keep_blank_values=keep_blank_values).items():
                for value in v:
                    self._add_field(k, None, value, None)

    def _add_field(self, name, filename, value, file):
        # Adds new field value to the form.
        # If a value already exists for this field name, then
        # if necessary a list is created from the existing value
        # and the new value is appended to the list.
        form_value = Field(name, filename, value, file)
        l = self.setdefault(name, form_value)
        if l is not form_value:
            # Already a value for this key:
            if isinstance(l, list):
                l.append(form_value)
            else:
                self[name] = [l, form_value]

    def _on_field(self, field):
        # Called by multipart.parse_form for each non-file form field.
        name = unquote_plus(field.field_name.decode())
        value = '' if field.value is None else unquote_plus(field.value.decode())
        self._add_field(name, None, value, None)

    def _on_file(self, file):
        # Called by multipart.parse_form for each file form field.
        if not file.field_name:
            return
        name = unquote_plus(file.field_name.decode())
        filename = file.file_name.decode()
        file_object = file.file_object
        if file_object is not None:
            value = file_object.getvalue()
            file_object.seek(0, 0)
        else:
            value = b''
        self._add_field(name, filename, value, file_object)

    def getvalue(self, name, default=None):
        """Get the value of this field, which could be either
        a single value (i.e. the value attribute of the underlying
        Field instance) or a list of such values. Returns the default
        argument if the name does not exist in the form.
        """
        if name not in self:
            return default
        value = self[name]
        return [v.value for v in value] if isinstance(value, list) else value.value

    def getlist(self, name):
        """Get a list of values for this field. If the name
        does not exist in the form, then an empty list is returned.
        """
        value = self.getvalue(name, [])
        return value if isinstance(value, list) else [value]

    def getfirst(self, name, default=None):
        """Get the first value of this field. Returns default argument
        if the name does not exist in the form
        """
        if name not in self:
            return default
        value = self.getvalue(name)
        return value[0] if isinstance(value, list) else value

if __name__ == '__main__':
    # Perform tests of this module:

    # Test a GET request:
    form = Form(environ={'QUERY_STRING': 'x=1&x=2&y=3'})
    assert repr(form) == "{'x': [Field('x', None, '1'), Field('x', None, '2')], 'y': Field('y', None, '3')}"

    assert form.getvalue('x') == ['1', '2']
    assert form.getlist('x') == ['1', '2']
    assert form.getfirst('x') == '1'
    assert [field.filename for field in form['x']] == [None, None]
    assert [field.value for field in form['x']] == ['1', '2']
    assert [field.file.read() for field in form['x']] == ['1', '2']

    assert form.getvalue('y') == '3'
    assert form.getlist('y') == ['3']
    assert form.getfirst('y') == '3'
    assert form['y'].name == 'y'
    assert form['y'].filename is None
    assert form['y'].value == '3'
    assert form['y'].file.read() == '3'

    # Test a multipart POST request:
    # We have here a text input field named 'act' whose value is 'abc' and two
    # file input fields named 'the_file' where a file has been selected for only the
    # first occurence:
    fp = io.BytesIO(b'------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="act"\r\n\r\nTest\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nabc\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename=""\r\nContent-Type: application/octet-stream\r\n\r\n\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp--\r\n')
    environ = {
        'CONTENT_LENGTH': '431',
        'CONTENT_TYPE': 'multipart/form-data; boundary=----WebKitFormBoundarytQ0DkMXsDqxwxBlp',
        }
    form = Form(environ=environ, fp=fp)
    assert repr(form) == "{'act': Field('act', None, 'Test'), 'the_file': [Field('the_file', 'test.txt', b'abc'), Field('the_file', '', b'')]}"

    assert form['act'].name == 'act'
    assert form['act'].filename is None
    assert form['act'].value == 'Test'
    assert form['act'].file.read() == 'Test'

    assert form['the_file'][0].name == 'the_file'
    assert form['the_file'][0].filename == 'test.txt'
    assert form['the_file'][0].value == b'abc'
    assert form['the_file'][0].file.read() == b'abc'

    assert form['the_file'][1].name == 'the_file'
    assert form['the_file'][1].filename == ''
    assert form['the_file'][1].value == b''
    assert form['the_file'][1].file.read() == b''

    assert form.getvalue('the_file') == [b'abc', b'']

    # Test a JSON-encoded POST request:
    fp = io.BytesIO(b'{"x": [1,2], "y": 3}')
    environ = {
        'CONTENT_LENGTH': '20',
        'CONTENT_TYPE': 'application/json',
        }
    form = Form(environ=environ, fp=fp)
    assert repr(form) == "{'x': [Field('x', None, 1), Field('x', None, 2)], 'y': Field('y', None, 3)}"

    assert form.getvalue('x') == [1, 2]
    assert form.getlist('x') == [1, 2]
    assert form.getfirst('x') == 1
    assert [field.filename for field in form['x']] == [None, None]
    assert [field.value for field in form['x']] == [1, 2]
    assert [field.file for field in form['x']] == [None, None]

    assert form.getvalue('y') == 3
    assert form.getlist('y') == [3]
    assert form.getfirst('y') == 3
    assert form['y'].name == 'y'
    assert form['y'].filename is None
    assert form['y'].value == 3
    assert form['y'].file is None

    print('All tests passed!')