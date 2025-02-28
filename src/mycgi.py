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

__version__ = '0.0.7'

import os
import sys
import json
from urllib.parse import parse_qs, unquote_plus
import io
from functools import partial

import python_multipart

__all__ = ['Form', 'Field']

class Field:
    """A Field represents a form value"""

    def __init__(self, name, filename, value, file=None):
        """An instance has the following
        attributes:
            1. name:     The form field name.
            2. filename: If this field is for a file, then the
                         file's filename, else None.
            3. value:    The form field value (or a file's contents) as bytes.
            4. file:     If this field is for a file, then a stream
                         that can be read to get the uploaded file's value, else None.
        """
        self.name = name
        self.filename = filename
        self.file = file
        self._value = value

    @property
    def value(self):
        if self.file:
            # An uploaded file (self._value is None)
            self.file.seek(0, 0) # Ensure we are at start of stream
            v = self.file.read()
            self.file.seek(0, 0) # So a subsequent explicit call to read can be done
            return v
        else:
            return self._value

    def __repr__(self):
        return f'Field({repr(self.name)}, {repr(self.filename)}, {repr(self.value)})'

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
                encoding = fp.encoding if hasattr(fp, 'encoding') else 'latin-1'
                rdr = (
                    partial(fp.read, int(environ['CONTENT_LENGTH']))
                    if 'CONTENT_LENGTH' in environ else fp.read
                )
                d = json.loads(rdr().decode(encoding))
                for k, v in d.items():
                    self[k] = [Field(k, None, value) for value in v] if isinstance(v, list) else Field(k, None, v)
            else:
                headers = {'Content-Type': environ.get('CONTENT_TYPE')}
                if 'CONTENT_LENGTH' in environ:
                    headers['Content-Length'] = environ['CONTENT_LENGTH']
                python_multipart.parse_form(headers, fp, self._on_field, self._on_file)
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
        # Called by python_multipart.parse_form for each non-file form field.
        name = unquote_plus(field.field_name.decode())
        value = '' if field.value is None else unquote_plus(field.value.decode())
        self._add_field(name, None, value, None)

    def _on_file(self, file):
        # Called by python_multipart.parse_form for each file form field.
        name = unquote_plus(file.field_name.decode())
        file_name = file.file_name
        if file_name is not None:
            file_name = file_name.decode()
        file_object = file.file_object
        # So user can do an explicit read on the file
        # and get data:
        file_object.seek(0, 0)
        # The value will always be obtained by reading the stream:
        self._add_field(name, file_name, None, file_object)

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
