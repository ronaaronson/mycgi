# mycgi - A Python3 Replacement for the Deprecated `cgi` Module

Other than using different class names (`mycgi.Form` instead of `cgi.FieldStorage` and `mycgi.Field` instead of `cgi.FieldStorage`) this module should be quite backward-compatible with the `mycgi` module. Additionally, JSON-encoded PUT and POST requests are supported.

Note that this module depends on the `python-multipart` package for handling POST and PUT requests that are not JSON-encoded.

## Some Usage Examples

```
# Instead of:
#from cgi import FieldStorage
# Use:
from mycgi import Form

form = Form()

# name is a text input field:
name = form.getvalue('name') # this will be a list if the form has multiple 'name' fields
# or: name = form.getfirst('name')
# or: names = form.getlist('name')

# spreadsheet is a file input field:
fileitem = form['spreadsheet']
# The name of the uploaded file:
filename = fileitem.filename
# Get the file contents as bytes 3 different ways:
contents = fileitem.file.read()
contents = fileitem.value
contents = form.getvalue('spreadsheet')
```

## Documentation

The initializer for the `mycgi.Form` class is:

```
    def __init__(self,
                 environ: Mapping=os.environ,
                 fp: BinaryIO | None=None,
                 keep_blank_values: bool=False
        ) -> None:
        """
        Initialize a Form instance.

        Arguments (all are optional):

        environ: environment dictionary
                 default: os.environ

        fp: stream containing encoded POST and PUT data used
            for PUT and POST requests.
            default: None (in which case if environ['wsgi.input'] exists it
                     will be used else sys.stdin.buffer will be used)

        keep_blank_values: flag indicating whether blank values in
                           percent-encoded forms should be treated as blank
                           strings.
                           default: False
        """
```

A `mycgi.Form` instance is a specialized dictionary whose keys are the field names and whose values are either a `mycgi.Field`
instance or a list of these instances. A `mycgi.Field` instance has the following attributes:

<pre>
1. <b>name</b>:     The form field name.
2. <b>filename</b>: If this field is for a file, then the file's filename, else None.
3. <b>value</b>:    The form field value (or a file's contents as bytes).
4. <b>file</b>:     If this field is for a file, then a stream that can be read to get the uploaded file's value, else None.
</pre>

The `mycgi.Form` class supports the `getvalue`, `getlist` and `getfirst` methods that behave identically to the like-named methods of the deprecated `cgi.FieldStorage` class and which make it unnecessary to access the `mycgi.Field` instances, although doing so can be useful for processing file uploads.

### JSON-encoded PUT and POST requests

Also supported are POST and PUT requests where the data is a JSON-encoded dictionary.

### WSGI Application Usage

To use `mycgi.Form` with a WSGI application:

```
from mycgi import Form

def wsgiApp(environ, start_response):
    form = Form(environ=environ)
    ...
```

## Tests To Demonstrate `mycgi` Usage

```
from mycgi import Form
import io

# Test a GET request:
form = Form(environ={'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'x=1&x=2&y=3'})
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
    'REQUEST_METHOD': 'POST',
    'CONTENT_LENGTH': '431',
    'CONTENT_TYPE': 'multipart/form-data; boundary=----WebKitFormBoundarytQ0DkMXsDqxwxBlp',
    }
form = Form(environ=environ, fp=fp)

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
    'REQUEST_METHOD': 'POST',
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