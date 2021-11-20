import re
import pandas as pd
from pathlib import Path
from typing import List
from loguru import logger
from sklearn.feature_extraction.text import CountVectorizer

INGNORE_FILES = [
    '.json', '.md', '.yaml', '.yml', '.gitignore', '.log', '.pdf', 'LICENSE',
]


def cnt_lines(lines):
    lines = [line for line in lines.split('\n') if line]
    return len(lines)


def find_data_file(fdir: Path, suffix: str) -> list:
    """Find all files named as xxxx_matrix.csv

    Parameters
    ----------
    fdir : Path
        path of the root data folder

    Returns
    -------
    list
        list of required files
    """
    fnames = []
    for dir in [d for d in fdir.iterdir() if d.is_dir()]:
        fnames.extend(dir.iterdir())

    pat = re.compile(rf'^.+{suffix}$')
    return [f for f in fnames if pat.match(f.name)]


def read_data(fnames: List[Path], type: str = 'csv') -> pd.DataFrame:
    """Read all data files and concatenate them

    Parameters
    ----------
    fnames : List[Path]
        List of file names

    Returns
    -------
    pd.DataFrame
        Over all dataframe
    """
    if type == 'json':
        df = pd.read_json(fnames[0], orient='table')
    else:
        df = pd.read_csv(fnames[0])
    df['plat'] = fnames[0].stem
    for fname in fnames[1:]:
        if type == 'json':
            sub_df = pd.read_json(fname, orient='table')
        else:
            sub_df = pd.read_csv(fname)
        sub_df['plat'] = fname.stem
        df = df.append(sub_df, ignore_index=True)
    return df


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
    if start > -1:
        lines = lines[0:start] + lines[end:]
    return '\n'.join(lines)


def del_multiple_files(fname: str, lines: str):
    pre_len = -1
    cur_len = cnt_lines(lines)
    while cur_len != pre_len:
        pre_len = cur_len
        lines = del_changes_of_file(fname, lines)
        cur_len = cnt_lines(lines)
    return lines


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


def get_valid_log_content(lines: str, type: str = 'add'):
    for fname in INGNORE_FILES:
        lines = del_multiple_files(fname, lines)
    lines = clean_lines(lines)
    d, a = split_changes(lines)
    if type == 'del':
        return d
    return a


def rm_special_words(txt: str) -> str:
    """Remove special words

    Parameters
    ----------
    txt : str
        text

    Returns
    -------
    str
        processed text
    """
    # remove special charaecters
    txt = re.sub(
        r'[\!\#\$\%\&\(\)\*+\,\-\.\/\;\:\<\=\>\?\@\[\]\\\^\_\`\{\}\|\~\n]',
        ' ',
        txt
    )
    # replace number and string literals with sepcial tokens
    txt = re.sub(r"([\d ]+)", " <NUM> ", txt)
    txt = re.sub(r"(\".*?\")", " <STR> ", txt)
    txt = re.sub(r"(\'.*?\')", " <STR> ", txt)
    return txt


def pre_process(p: Path):
    logger.info("Start reading matrix.csv...")
    fnames = find_data_file(p, '_matrix.csv')
    matrix_df = read_data(fnames)
    matrix_df.dropna(inplace=True)
    matrix_df.drop(['plat'], axis=1, inplace=True)

    logger.info('Start reading commits.json...')
    fnames = find_data_file(p, 'commits.json')
    commit_df = read_data(fnames, 'json')
    commit_df.dropna(inplace=True)
    commit_df['text'] = commit_df['changes'].apply(
        lambda x: rm_special_words(x)
    )
    commit_df.drop(['msg', 'plat', 'changes'], axis=1, inplace=True)

    logger.info('Data pre-processing...')
    cv = CountVectorizer()
    cv_fit = cv.fit_transform(commit_df['text'].tolist())
    commit_df['nw'] = cv_fit.toarray().sum(axis=1)

    idx = cv.get_feature_names().index('function')
    commit_df['nfunc'] = cv_fit.toarray()[:, idx]

    df = pd.merge(matrix_df, commit_df, on=['commit', 'buggy'])
    df.drop(['text'], axis=1, inplace=True)

    return df
