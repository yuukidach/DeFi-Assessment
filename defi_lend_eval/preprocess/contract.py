from pathlib import Path
import re
import pandas as pd
from pathlib import Path


# def (lines: str):
#     # print(lines)
#     clean_lines=[]
#     for line in lines.split('\n'):
#         print(line)
#         if re.match(r'^@@.*@@$', line) \
#            or re.match(r'^diff --git.*$') \
#            or re.match(r'^inedx'):
#             continue

def del_changes_of_file(fname: str, lines: str):
    """Remove changes brought by a certain file

    Greedy algotithm. Only the first file met the requirment will be removed.

    Parameters
    ----------
    fname : str
        file name
    lines : str
        changed lines
    """
    lines = lines.split('\n')
    start, end = -1, len(lines)
    for idx, line in enumerate(lines):
        if start < 0 and re.match(fr'^diff --git .*{fname}$', line):
            start = idx
            continue
        if start >= 0 and re.match(r'^diff --git .*$', line):
            end = idx
            break
    lines = lines[0:start] + lines[end:]
    return '\n'.join(lines)


def clean_lines(lines: str):
    """Only keep deleted and added lines

    Parameters
    ----------
    lines : str
        full git log

    Returns
    -------
    git log with only deleted and added lines in it
    """
    lines = lines.split('\n')
    l2rm = []
    for idx, line in enumerate(lines):
        if (re.match(r'^(?!\+).*', line) and re.match(r'^(?!-).*', line)) \
           or re.match(r'^\+\+\+ .*', line) \
           or re.match(r'^--- .*', line):
            l2rm.append(idx)
            
    l2rm = sorted(l2rm, reverse=True)
    for idx in l2rm:
        if idx < len(lines):
            lines.pop(idx)
    return '\n'.join(lines)


def split_changes(lines: str):
    """Split changes as deletions and addition

    Parameters
    ----------
    lines : str
        lines only contains deletion and addtion

    Returns
    -------
    deletion, addition
    """
    lines = lines.split('\n')
    del_lines, add_lines = [], []
    for line in lines:
        if re.match(r'^-.*', line):
            del_lines.append(line)
        elif re.match(r'^\+.*', line):
            add_lines.append(line)

    del_lines = '\n'.join(del_lines)
    add_lines = '\n'.join(add_lines)
    return del_lines, add_lines


def pre_process_data(fname: Path):
    df = pd.read_json(fname, orient='table')
    lines = df['changes'][0]
    lines = del_changes_of_file('package-lock.json', lines)
    lines = clean_lines(lines)
    print(lines[:1000])
    d, a = split_changes(lines)
    print(a[:500])
    print(d[:500])


if __name__ == '__main__':
    pre_process_data('/mnt/d/Projects/DeFi-Lending-Evaluation/data/88mph/88mph_buggy_commits.json') 