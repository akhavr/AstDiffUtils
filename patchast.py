# -*- coding: utf-8 -*-
import argparse
import ast
import astor
import json
import os.path
import re
import shutil
import sys

name_idx_re = re.compile('(\S+)\[(\d+)\]')
name_re = re.compile('(\S+)')

parser = argparse.ArgumentParser()
parser.add_argument('src')
parser.add_argument('patch')
parser.add_argument('dst')


def parse_name_idx(name_idx):
    m = name_idx_re.search(name_idx)
    if m is not None:
        g = m.groups()
        return g[0], int(g[1])
    m = name_re.search(name_idx)
    g = m.groups()
    return g[0], None


def navigate(tree, route):
    route = route.split('.')
    assert route[0] == 'root'
    for r in route[1:]:
        name, idx = parse_name_idx(r)
        if idx is not None:
            tree = getattr(tree, name)[idx]
        else:
            tree = getattr(tree, name)
    return tree


def apply_file_patch(src, patch):
    # make sure we don't have dictionary_item_added or dictionary_item_removed
    if 'dictionary_item_added' in patch.keys() \
           or 'dictionary_item_removed' in patch.keys():
        raise KeyError

    src_ast = ast.parse(src)

    if 'values_changed' in patch.keys():
        for route, change in patch['values_changed'].items():
            route_less_1 = route.split('.')[:-1]
            route_last = route.split('.')[-1]
            obj = navigate(src_ast, '.'.join(route_less_1))
            setattr(obj, route_last, str(change['new_value']))

    if 'type_changes' in patch.keys():
        for route, change in patch['type_changes'].items():
            route_less_1 = route.split('.')[:-1]
            route_last = route.split('.')[-1]
            obj = navigate(src_ast, '.'.join(route_less_1))
            name, idx = parse_name_idx(route_last)
            if idx is not None:
                lst = getattr(obj, name)
                lst[idx] = ast.parse(change['new_value']).body[0]
            else:
                # This is attribute assignment
                try:
                    # maybe we can use the value as is
                    new_val = change['new_value']
                    if type(change['new_value']) in (type(''), type(u'')):
                        new_val = ast.parse(change['new_value']).body[0].value
                        pass
                    setattr(obj, name, new_val)
                except KeyError:
                    # no `new_value`, op change
                    # not nice
                    classname = change['new_type'].split('.')[1][:-2]
                    setattr(obj, name, getattr(ast, classname)())

    if 'iterable_item_removed' in patch.keys():
        items = sorted(patch['iterable_item_removed'].items(),
                       key=lambda x: x[0])
        for route, change in items:
            m = name_idx_re.search(route)
            assert m is not None, route
            route_wo_index, index = m.groups()
            obj = navigate(src_ast, route_wo_index)
            for e in obj:
                if type(e) is ast.keyword:
                    if e.arg == change:
                        # this is a kwarg list and we already removed an item
                        obj.remove(e)
                elif type(e) is ast.Name:
                    if e.id == change:
                        # this is an arg list and we've already removed an item
                        obj.remove(e)
                elif change == astor.to_source(e):
                    # this is plain line of code to be removed
                    obj.remove(e)

    if 'iterable_item_added' in patch.keys():
        def sorting_key(entry):
            route = entry[0]
            m = name_idx_re.search(route)
            assert m is not None, route
            _, index = m.groups()
            return int(index)

        items = sorted(patch['iterable_item_added'].items(), key=sorting_key)
        for route, change in items:
            m = name_idx_re.search(route)
            assert m is not None, route
            route_wo_index, index = m.groups()
            obj = navigate(src_ast, route_wo_index)
            try:
                assert len(obj) == int(index)
            except Exception:
                print route, change[:50], '...'
                print len(obj), index
                pass
            if type(change) in (type(''), type(u'')):
                change_ast = ast.parse(change)
                obj.append(change_ast.body[0])
            else:
                # this is ast.keyword
                change_ast_kw = ast.parse(change[0]).body[0].value
                change_ast_value = ast.parse(change[1]).body[0].value
                obj.append(ast.keyword(arg=change_ast_kw,
                                       value=change_ast_value))

    return astor.to_source(src_ast)


def apply_patch(src, dst, patch):
    def remove_files_cb(dirpath, filenames, src=src, patch=patch):
        ignore = []
        local_path = dirpath.replace(src, '')
        for fname in filenames:
            if 'remove_files' in patch.keys() \
               and os.path.join(local_path, fname) in patch['remove_files']:
                ignore.append(fname)
        return ignore

    shutil.copytree(src, dst, ignore=remove_files_cb)

    if 'change_files' in patch.keys():
        changes = patch['change_files']
        for src_file, file_patch in changes:
            try:
                old_src = open(os.path.join(src, src_file)).read()
            except IOError:  # no such file
                old_src = ''
            new_src = apply_file_patch(old_src, file_patch)
            dst_path = os.path.join(dst, src_file)
            open(dst_path, 'w').write(new_src)
    return src


if __name__ == '__main__':
    args = parser.parse_args()
    if os.path.exists(args.dst):
        print args.dst, 'already exists, not overwriting it'
        sys.exit(1)
    print 'Apply', args.patch, 'to', args.src, 'and put result to', args.dst
    apply_patch(args.src, args.dst, json.load(open(args.patch)))
