import ast
import astor
from deepdiff import DeepDiff
import json
import os.path
import sys


def str_ast_diff(old_content, new_content):
    d = DeepDiff(ast.parse(old_content), ast.parse(new_content))

    try:
        for k, v in d['iterable_item_added'].items():
            if isinstance(v, ast.keyword):
                d['iterable_item_added'][k] = (v.arg, astor.to_source(v.value))
            else:
                # regular code
                d['iterable_item_added'][k] = astor.to_source(v)
    except KeyError:
        pass  # No additions

    try:
        for k, v in d['iterable_item_removed'].items():
            if isinstance(v, ast.keyword):
                d['iterable_item_removed'][k] = v.arg
            else:
                # regular code
                d['iterable_item_removed'][k] = astor.to_source(v)
    except KeyError:
        pass  # No removals

    for change_type, change in d.items():
        if change_type in ('iterable_item_added', 'iterable_item_removed'):
            continue

        for k, v in change.items():
            if k.endswith('.lineno') or k.endswith('.col_offset'):
                # we're not iterested in line or column number changes
                del d[change_type][k]
                continue

            try:
                for kk in ('new_type', 'old_type'):
                    d[change_type][k][kk] = repr(v[kk])
            except KeyError:
                pass  # This is not a `type_changes` key
            for kk in ('new_value', 'old_value'):
                try:
                    fmap = {ast.In: 'in',
                            ast.Is: 'is',
                            ast.IsNot: 'is not',
                            ast.Gt: '>',
                            ast.Lt: '<',
                            ast.Eq: '==',
                            ast.FloorDiv: '//',
                            ast.Add: '+',
                            }
                    if v[kk] is None:
                        pass
                    elif type(v[kk]) in (type(''), type(0), type(0.0)):
                        pass
                    elif isinstance(v[kk], (ast.Mod, ast.Sub)):
                        # ignore new_value for op changes
                        del d[change_type][k][kk]
                    elif isinstance(v[kk], (ast.Mod, ast.Sub, ast.In, ast.Is,
                                            ast.IsNot, ast.Gt, ast.Lt, ast.Eq,
                                            ast.FloorDiv, ast.Add)):
                        d[change_type][k][kk] = fmap[type(v[kk])]
                    else:
                        # this works only for `type_changes`
                        d[change_type][k][kk] = astor.to_source(v[kk])
                except KeyError:
                    pass  # there's no `new_value` in this change_type
    return d


def tree_diff(path_old, path_new):
    find_py_files = astor.code_to_ast.find_py_files
    old = [(v[0].replace(path_old, ''), v[1]) for v in find_py_files(
        path_old, ignore='.env')]
    new = [(v[0].replace(path_new, ''), v[1]) for v in find_py_files(
        path_new, ignore='.env')]

    remove_files = set(os.path.join(*v) for v in old).difference(
        os.path.join(*v) for v in new)
    add_files = set(os.path.join(*v) for v in new).difference(
        os.path.join(*v) for v in old)
    maybechange_files = set(os.path.join(*v) for v in new).difference(
        add_files)
    change_files = []

    # process files in `maybechange_files` actions
    for f in maybechange_files:
        d = str_ast_diff(open(os.path.join(path_old, f)).read(),
                         open(os.path.join(path_new, f)).read())
        if len(d) == 0:
            continue
        change_files.append((f, d))

    # process files in `add_files` action
    for f in add_files:
        d = str_ast_diff('', open(os.path.join(path_new, f)).read())
        if len(d) == 0:
            continue
        change_files.append((f, d))

    actions = {
        'remove_files': list(remove_files),
        'change_files': change_files,
    }

    return actions


if __name__ == '__main__':
    path_old = sys.argv[1]
    path_new = sys.argv[2]
    actions = tree_diff(path_old, path_new)

    print json.dumps(actions, indent=2)
