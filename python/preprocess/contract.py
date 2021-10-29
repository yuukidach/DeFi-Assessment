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
    lines = lines.split('\n')
    l2rm = []
    for idx, line in enumerate(lines):
        if re.match(r'^(?!\+).*') and re.match(r'^(?!-).*'):
           l2rm.append(idx)



def pre_process_data(fname: Path):
    df = pd.read_json(fname, orient='table')
    lines = del_changes_of_file('package-lock.json', lines)
    print(lines)


if __name__ == '__main__':
    pre_process_data('/mnt/d/Projects/DeFi-Lending-Evaluation/data/88mph/88mph_buggy_commits.json') 