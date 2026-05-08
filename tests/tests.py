#!/usr/bin/env python

import io
import sys
from unittest import TestCase, main

sys.path.insert(0, "../src")
from mycgi import Form, __version__

print(f"Testing mycgi {__version__}")


class TestGetRequest(TestCase):
    """
    Verify that GET requests are handled correctly.
    """

    def test(self):
        form = Form(environ={"REQUEST_METHOD": "GET", "QUERY_STRING": "x=1&x=2&y=3"})

        self.assertEqual(
            repr(form),
            "{'x': [Field('x', None, '1'), Field('x', None, '2')], 'y': Field('y', None, '3')}",
        )
        self.assertEqual(form.getvalue("x"), ["1", "2"])
        self.assertEqual(form.getlist("x"), ["1", "2"])
        self.assertEqual(form.getfirst("x"), "1")
        self.assertEqual([field.filename for field in form["x"]], [None, None])
        self.assertEqual([field.value for field in form["x"]], ["1", "2"])
        self.assertEqual(form.getvalue("y"), "3")
        self.assertEqual(form.getlist("y"), ["3"])
        self.assertEqual(form.getfirst("y"), "3")
        self.assertEqual(form["y"].name, "y")
        self.assertEqual(form["y"].filename, None)
        self.assertEqual(form["y"].value, "3")


class TestPostRequest(TestCase):
    """
    Verify that POST requests are handled correctly.
    """

    def test(self):
        fp = io.BytesIO(b"x=1&x=2&y=3")
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": "11",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        }
        form = Form(environ=environ, fp=fp)

        self.assertEqual(
            repr(form),
            "{'x': [Field('x', None, '1'), Field('x', None, '2')], 'y': Field('y', None, '3')}",
        )
        self.assertEqual(form.getvalue("x"), ["1", "2"])
        self.assertEqual(form.getlist("x"), ["1", "2"])
        self.assertEqual(form.getfirst("x"), "1")
        self.assertEqual([field.filename for field in form["x"]], [None, None])
        self.assertEqual([field.value for field in form["x"]], ["1", "2"])
        self.assertEqual(form.getvalue("y"), "3")
        self.assertEqual(form.getlist("y"), ["3"])
        self.assertEqual(form.getfirst("y"), "3")
        self.assertEqual(form["y"].name, "y")
        self.assertEqual(form["y"].filename, None)
        self.assertEqual(form["y"].value, "3")


class TestJsonEncodedPostRequest(TestCase):
    """
    Test a JSON-encoded POST request.
    """

    def test(self):
        fp = io.BytesIO(b'{"x": [1,2], "y": 3}')
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": "20",
            "CONTENT_TYPE": "application/json",
        }
        form = Form(environ=environ, fp=fp)

        self.assertEqual(
            repr(form),
            "{'x': [Field('x', None, 1), Field('x', None, 2)], 'y': Field('y', None, 3)}",
        )
        self.assertEqual(form.getvalue("x"), [1, 2])
        self.assertEqual(form.getlist("x"), [1, 2])
        self.assertEqual(form.getfirst("x"), 1)
        self.assertEqual([field.filename for field in form["x"]], [None, None])
        self.assertEqual([field.value for field in form["x"]], [1, 2])
        self.assertEqual([field.file for field in form["x"]], [None, None])
        self.assertEqual(form.getvalue("y"), 3)
        self.assertEqual(form.getlist("y"), [3])
        self.assertEqual(form.getfirst("y"), 3)
        self.assertEqual(form["y"].name, "y")
        self.assertEqual(form["y"].filename, None)
        self.assertEqual(form["y"].value, 3)
        self.assertEqual(form["y"].file, None)


class TestMultiPartPostRequest(TestCase):
    """
    Test a multipart POST request:
    We have here a text input field named 'act' whose value is 'abc' and two
    file input fields named 'the_file' where a file has been selected for only the
    first occurence.
    """

    def test(self):
        fp = io.BytesIO(
            b'------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="act"\r\n\r\nTest\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nabc\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp\r\nContent-Disposition: form-data; name="the_file"; filename=""\r\nContent-Type: application/octet-stream\r\n\r\n\r\n------WebKitFormBoundarytQ0DkMXsDqxwxBlp--\r\n'
        )
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": "431",
            "CONTENT_TYPE": "multipart/form-data; boundary=----WebKitFormBoundarytQ0DkMXsDqxwxBlp",
        }
        form = Form(environ=environ, fp=fp)

        self.assertEqual(
            repr(form),
            "{'act': Field('act', None, 'Test'), 'the_file': [Field('the_file', 'test.txt', b'abc'), Field('the_file', '', b'')]}",
        )

        self.assertEqual(form["act"].name, "act")
        self.assertEqual(form["act"].filename, None)
        self.assertEqual(form["act"].value, "Test")
        self.assertEqual(form["the_file"][0].name, "the_file")
        self.assertEqual(form["the_file"][0].filename, "test.txt")
        self.assertEqual(form["the_file"][0].value, b"abc")
        self.assertEqual(form["the_file"][1].name, "the_file")
        self.assertEqual(form["the_file"][1].filename, "")
        self.assertEqual(form["the_file"][1].value, b"")
        self.assertEqual(form.getvalue("the_file"), [b"abc", b""])


if __name__ == "__main__":
    main()
