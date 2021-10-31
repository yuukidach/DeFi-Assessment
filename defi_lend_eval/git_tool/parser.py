from pathlib import Path

from numpy import arctan

__all__ = ['get_num_of_subsys', 'get_num_of_dir']


def get_num_of_subsys(fnames: list) -> int:
    ss = set()
    for fname in fnames:
        p = Path(fname)
        parts = p.parts
        if (len(parts) == 1):
            ss.add('/')
        else:
            ss.add(parts[0])
    return len(ss)


def get_num_of_dir(fnames: list) -> int:
    dir = set()
    for fname in fnames:
        p = Path(fname)
        dir.add(p.parent)
    return len(dir)
