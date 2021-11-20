from pathlib import Path

__all__ = ['get_subsys', 'get_dir']


def get_subsys(fnames: list) -> int:
    ss = set()
    for fname in fnames:
        if fname == '':
            continue

        p = Path(fname)
        parts = p.parts
        if (len(parts) == 1):
            ss.add('/')
        else:
            ss.add(parts[0])
    return ss


def get_dir(fnames: list) -> int:
    dir = set()
    for fname in fnames:
        p = Path(fname)
        dir.add(p.parent)
    return dir
