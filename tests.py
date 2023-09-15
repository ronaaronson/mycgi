#!/usr/bin/env python

######## Setup to get the project version #########
import sys
sys.path.insert(0, 'src')
from mycgi import __version__
print(f'Testing mycgi {__version__}')
###################################################

## Tests To Demonstrate `mycgi` Usage

from mycgi import Form
import io

# Perform tests of this module:

# Test a GET request:
form = Form(environ={'QUERY_STRING': 'x=1&x=2&y=3'})
assert repr(form) == "{'x': [Field('x', None, '1'), Field('x', None, '2')], 'y': Field('y', None, '3')}"

assert form.getvalue('x') == ['1', '2']
assert form.getlist('x') == ['1', '2']
assert form.getfirst('x') == '1'
assert [field.filename for field in form['x']] == [None, None]
assert [field.value for field in form['x']] == ['1', '2']

assert form.getvalue('y') == '3'
assert form.getlist('y') == ['3']
assert form.getfirst('y') == '3'
assert form['y'].name == 'y'
assert form['y'].filename is None
assert form['y'].value == '3'

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

assert form['the_file'][0].name == 'the_file'
assert form['the_file'][0].filename == 'test.txt'
assert form['the_file'][0].value == b'abc'

assert form['the_file'][1].name == 'the_file'
assert form['the_file'][1].filename == ''
assert form['the_file'][1].value == b''

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