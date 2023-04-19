mycgi - A Python3 Replacement for the Deprecated `cgi` Module
=============================================================

This module uses the `python-multipart` package for handling non-JSON-encoded POST and PUT requests.

Some Usage Examples
-------------------

```
# Instead of:
#from cgi import FieldStorage
# Use:
from mycgi import Form

form = Form()

# name is a text input field:
name = form.getvalue('name')
# or: name = form.getfirst('name')
# or: names = form.getlist('name')

# spreadsheet is a file input field:
fileitem = form['spreadsheet']
# The name of the uploaded file:
filename = fileitem.filename
# Get the file contents as a bytestring:
spreadsheet_data = fileitem.file.read()
# or: spreadsheet_data = fileitem.value
# or: spreadsheet data = form.getvalue('spreadsheet')
```

Documentation
-------------

The `mycgi.Form` class's initializer is:

```
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

```

A `mycgi.Form` instance is a specialized dictionary whose keys are the field names and whose values are either a `mycgi.Field` instance or a list of these instances. A `cgi.Field` instance has the following attributes:

1. `name`:     The form field name.
2. `filename`: If this field is for an uploaded file, then the uploaded filename, else None.
3. `value`:    The form field value (or an uploaded file's contents as bytes).
4. `file`:     If the field value is a string or byte string,then a stream that can be read to get the field's value, else None.

**Also supported are POST and PUT requests where the data is a JSON-encoded dictionary.**

To use `mycgi.Form` with WSGI applications:

```
from mycgi import Form

def wsgiApp(environ, start_response):
    form = Form(environ=environ, fp=environ['wsgi.input'])
    ...
```

Tests to Further Demonstrate `mycgi` Usage
----------------------------------------

```
from mycgi import Form
import io

# Test a GET request:
form = Form(environ={'QUERY_STRING': 'x=1&x=2&y=3'})

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

# The following definition of fp is on a single line:
fp = io.BytesIO(b'------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="act"\r\n\r\nTest\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nabc\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename=""\r\nContent-Type: application/octet-stream\r\n\r\n\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp--\r\n')

environ = {
    'CONTENT_LENGTH': '431',
    'CONTENT_TYPE': 'multipart/form-data; boundary=----WebKitFormBoundarytQ0DkMXsDqxwxBlp',
}

form = Form(environ=environ, fp=fp)

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
```