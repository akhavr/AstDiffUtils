from deltaast import str_ast_diff


def test_func_type_keyarg_added():
    d = str_ast_diff('f()', 'f(type=int)')
    assert d['iterable_item_added'] == {'root.body[0].value.keywords[0]':
                                        ('type', 'int\n')}


def test_func_str_keyarg_added():
    d = str_ast_diff('f()', 'f(type="int")')
    assert d['iterable_item_added'] == {'root.body[0].value.keywords[0]':
                                        ('type', '"""int"""\n')}


def test_func_str2_keyarg_added():
    d = str_ast_diff('f()', 'f(type="""int""")')
    assert d['iterable_item_added'] == {'root.body[0].value.keywords[0]':
                                        ('type', '"""int"""\n')}


def test_func_strarg_added():
    d = str_ast_diff('f()', 'f("str")')
    assert d['iterable_item_added'] == {'root.body[0].value.args[0]':
                                        '"""str"""\n'}, d


def test_empty_orig_source():
    d = str_ast_diff('', 'f()')
    assert d['iterable_item_added'] == {'root.body[0]': 'f()\n'}


def test_mod_for_sub():
    d = str_ast_diff('a - 2', 'a % 2')
    assert 'new_value' not in d['type_changes']['root.body[0].value.op'].keys()


def test_in():
    d = str_ast_diff('b is lst', 'b in lst')
    correct = {'root.body[0].value.ops[0]': {'new_value': 'in',
                                             'old_value': 'is',
                                             'new_type': "<class '_ast.In'>",
                                             'old_type': "<class '_ast.Is'>"
                                             }}
    assert d['type_changes'] == correct, repr(d)
