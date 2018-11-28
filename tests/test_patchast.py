from nose.tools import *
import shutil
import tempfile

from patchast import *

@raises(KeyError)
def test_dictionary_item_added():
    s = ''
    p = {'dictionary_item_added': None}
    apply_file_patch(s, p)

@raises(KeyError)
def test_dictionary_item_removed():
    s = ''
    p = {'dictionary_item_removed': None}
    apply_file_patch(s, p)

def test_values_changed():
    s = 'import numpy'
    p = {'values_changed': {'root.body[0].names[0].name': {'new_value' :'argparse',
                                                           'old_value': 'numpy'}}}
    r = apply_file_patch(s, p)
    assert r=='import argparse\n', repr(r)

def test_navigate_1stlvl():
    tree = ast.parse('import numpy')
    o = navigate(tree, 'root.body[0]')
    assert o == tree.body[0], o

def test_navigate_2stlvl():
    tree = ast.parse('import numpy')
    o = navigate(tree, 'root.body[0].names[0]')
    assert o == tree.body[0].names[0], o

def test_parse_name_idx():
    n, idx = parse_name_idx('body[0]')
    assert n=='body', n
    assert idx == 0, idx

def test_parse_name_no_idx():
    n, idx = parse_name_idx('name')
    assert n=='name', n
    assert idx is None, idx

def test_type_changes():
    s = 'v = 1\n'
    p = {'type_changes' : {'root.body[0]': {"new_type": "<class '_ast.Import'>",
                                            "old_type": "<class '_ast.Assign'>",
                                            "old_value": "v = 1\n",
                                            "new_value": "import os.path\n",}}}
    r = apply_file_patch(s, p)
    assert r=='import os.path\n', repr(r)

def test_type_changes_attr_added():
    s = 'assert 0 == 1\n'
    p = {'type_changes' : {'root.body[0].msg': {'old_type': "<type 'NoneType'>",
                                                'old_value': None,
                                                'new_type' : "<class '_ast.Str'>",
                                                'new_value': '"Strange, right?"',}}}
    r = apply_file_patch(s, p)
    assert r=='assert 0 == 1, \'Strange, right?\'\n', repr(r)

def test_type_changes_import_as_added():
    s = 'import numpy\n'
    p = {'type_changes': {'root.body[0].names[0].asname': {'new_type': "<type 'str'>",
                                                           'new_value': 'np',
                                                           'old_type': "<type 'NoneType'>",
                                                           'old_value': None}}}
    r = apply_file_patch(s, p)
    assert r=='import numpy as np\n', repr(r)

def test_type_changes_import_as_removed():
    s = 'import numpy as np\n'
    p = {'type_changes': {'root.body[0].names[0].asname': {'old_type': "<type 'str'>",
                                                           'old_value': 'np',
                                                           'new_type': "<type 'NoneType'>",
                                                           'new_value': None}}}
    r = apply_file_patch(s, p)
    assert r=='import numpy\n', repr(r)

def test_type_changes_keyparam_changed():
    s = 'foo(bar=0.0)\n'
    p = {'type_changes': {'root.body[0].value.keywords[0].value.n' : {'new_type': "<type 'int'>",
                                                                      'new_value': 10,
                                                                      'old_type': "<type 'float'>",
                                                                      'old_value': 0.0}}}
    r = apply_file_patch(s, p)
    assert r=='foo(bar=10)\n', repr(r)

def test_type_changes_op_type():
    s = 'foo = bar%2'
    p = {'type_changes': {'root.body[0].value.op': {'new_type': "<class '_ast.Sub'>",
                                                    'old_type': "<class '_ast.Mod'>"}}}
    r = apply_file_patch(s, p)
    assert r=='foo = bar - 2\n', repr(r)

def test_iterable_item_added():
    s = 'foo = 1\n'
    p = {'iterable_item_added': {'root.body[1]': 'bar = 2\n',}}
    r = apply_file_patch(s, p)
    assert r=='foo = 1\nbar = 2\n', repr(r)

def test_iterable_item_added_keyword():
    s = 'foo()'
    p = {'iterable_item_added': {'root.body[0].value.keywords[0]': ('bar',
                                                                    '[1, 10]\n')}}
    r = apply_file_patch(s, p)
    assert r=='foo(bar=[1, 10])\n', repr(r)

def test_iterable_item_added_order():
    s = 'foo = 1\n'
    p = {'iterable_item_added': {'root.body[2]': 'bar = 2\n',
                                 'root.body[1]': 'foo = 3\n',
                                 'root.body[3]': 'f1 = 3\n',
                                 'root.body[4]': 'f1 = 4\n',
                                 'root.body[5]': 'f1 = 5\n',
                                 'root.body[6]': 'f1 = 6\n',
                                 'root.body[7]': 'f1 = 7\n',
                                 'root.body[8]': 'f1 = 8\n',
                                 'root.body[9]': 'f1 = 9\n',
                                 'root.body[10]': 'f1 = 10\n',
    }}
    r = apply_file_patch(s, p)
    correct = """\
foo = 1
foo = 3
bar = 2
f1 = 3
f1 = 4
f1 = 5
f1 = 6
f1 = 7
f1 = 8
f1 = 9
f1 = 10
"""
    assert r==correct, repr(r)

def test_iterable_item_removed():
    s = 'foo(bar=1)\n'
    p = {'iterable_item_removed': {'root.body[0].value.keywords[0]': 'bar'}}
    r = apply_file_patch(s, p)
    assert r=='foo()\n', repr(r)

def test_iterable_item_removed_twolines():
    s = 'foo()\nbar()'
    p = {'iterable_item_removed': {'root.body[0]': 'foo()\n',
                                   'root.body[1]': 'bar()\n'}}
    r = apply_file_patch(s, p)
    assert r=='', repr(r)

def test_iterable_item_removed_twoargs():
    s = 'foo(bar, baz)'
    p = {'iterable_item_removed': {'root.body[0].value.args[1]': 'baz',
                                   'root.body[0].value.args[0]': 'bar',}}
    r = apply_file_patch(s, p)
    assert r=='foo()\n', repr(r)

def test_iterable_item_removed_twokw():
    s = 'foo(baz=0, bar=1)'
    p = {'iterable_item_removed': {'root.body[0].value.keywords[1]': 'bar',
                                   'root.body[0].value.keywords[0]': 'baz',}}
    r = apply_file_patch(s, p)
    assert r=='foo()\n', repr(r)

def touch_file(fname, times=None):
    # borrowed from https://stackoverflow.com/questions/1158076/implement-touch-using-python
    with open(fname, 'a'):
        os.utime(fname, times)

def test_apply_patch_rmfiles():
    # with tempfile.TemporaryDirectory() as .. is not supported in python 2.7 :(
    try:
        srcdir = tempfile.mkdtemp()
        touch_file(os.path.join(srcdir, 'remove.me'))
        dstdir = '.'.join([srcdir, '.dst'])
        p = {'remove_files': ['remove.me']}
        apply_patch(srcdir, dstdir, p)
        assert not os.path.exists(os.path.join(dstdir, 'remove.me'))
    finally:
        shutil.rmtree(srcdir)
        shutil.rmtree(dstdir)

def test_apply_patch_rmfiles_within_dir():
    try:
        srcdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(srcdir, 'subdir'))
        touch_file(os.path.join(srcdir, 'subdir', 'leave.me'))
        touch_file(os.path.join(srcdir, 'subdir', 'remove.me'))
        dstdir = '.'.join([srcdir, 'dst'])
        p = {'remove_files': ['/subdir/remove.me']}
        apply_patch(srcdir, dstdir, p)
        assert os.path.exists(os.path.join(dstdir, 'subdir', 'leave.me'))
        assert not os.path.exists(os.path.join(dstdir, 'subdir', 'remove.me'))
    finally:
        shutil.rmtree(srcdir)
        shutil.rmtree(dstdir)

def test_apply_patch_complete():
    # with tempfile.TemporaryDirectory() as .. is not supported in python 2.7 :(
    try:
        srcdir = tempfile.mkdtemp()
        touch_file(os.path.join(srcdir, 'remove.me'))
        touch_file(os.path.join(srcdir, 'create.py'))
        dstdir = '.'.join([srcdir, 'dst'])
        code = 'print \'Hello!\'\n'
        p = {
            'remove_files': ['remove.me'],
            'change_files': [['create.py', {'iterable_item_added': {'root.body[0]': code}}]]
        }
        apply_patch(srcdir, dstdir, p)
        leave_path = os.path.join(dstdir, 'create.py')
        assert not os.path.exists(os.path.join(dstdir, 'remove.me'))
        assert os.path.exists(leave_path)
        content = open(leave_path).read()
        assert content == code, 'Expected %s got %s' % (repr(code), repr(content))
    finally:
        try: shutil.rmtree(srcdir)
        except OSError: pass
        try: shutil.rmtree(dstdir)
        except OSError: pass

