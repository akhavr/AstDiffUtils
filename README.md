# AstDiffUtils

Utility scripts to compute diff between two file trees in AST terms

## Dependencies

Listed in `requirements.txt`:

* astor
* deepdiff

## Usage

```
$ python deltaast.py oldpath newpath > ast.diff

$ python patchast.py -src oldpath -patch ast.diff -dst newpath
```

Note that if you're using `patchast.py`, `newpath` should not exist.

## Patch format

It's a json file with dictionary on the top.  The dictionary has two keys:

* `remove_files`: list of files to be removed in `newpath` relative to the `oldpath`
* `change_files`: list of changes to files to be added or changed in `newpath` relative to the `oldpath`

Each file change is an output of `deepdiff` between AST trees of respective files.

