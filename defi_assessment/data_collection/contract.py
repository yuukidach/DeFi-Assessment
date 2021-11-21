import sys
import pandas as pd
from pathlib import Path
from functools import reduce
from tqdm.auto import tqdm
from loguru import logger
from defi_assessment.git_tool.gitcmd import GitCommit
from defi_assessment.git_tool.parser import get_subsys, get_dir

fmt = ('<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | '
       '<lvl>{message}</lvl>')
logger.remove()
logger.add(sys.stdout, format=fmt)


def _do_all_data_exist(paths: list) -> bool:
    """ Chekc if all csv files are existing

    Args:
        paths (list): list of csv files

    Returns:
        bool: true or false
    """
    return reduce(lambda x, y: x & y.exists(), paths, True)


def _get_all_simple_commits(gc: GitCommit):
    """Get all commits except merge and initial commits
    """
    all_commits = gc.get_commits()
    merge_commits = gc.get_commits('merge')
    # remove merge commits which contain too many changes
    all_commits = set(all_commits) - set(merge_commits)
    return [c for c in all_commits if not gc.is_in_1st_commits(c)]


def create_fix_commit_csv(gc: GitCommit, csv: Path):
    """ Create datastes for commits releated to bug fix.

    Args:
        gc (GitCommit): git commit class
        csv (Path): file to save the result data
    """
    data = {
        'fix_commit': [],
        'fname': [],
        'changed_lines': [],
        'bug_commits': []
    }

    fix_commits = gc.get_fix_commits()
    tbar = tqdm(fix_commits)
    for fc in tbar:
        tbar.set_description(f'Fetching bug fix data for {fc}')
        files = gc.get_changed_filenames(fc)
        fname_lines = gc.get_changed_lines(fc, files)
        bug_commits = gc.blame_old_lines(fc, fname_lines)
        for fname, commits in bug_commits.items():
            data['fix_commit'].append(fc)
            data['fname'].append(fname)
            data['changed_lines'].append(fname_lines[fname])
            data['bug_commits'].append(commits)

    df = pd.DataFrame(data)
    df.to_csv(csv, index=False)


def get_buggy_commits_from_fix_csv(csv: Path) -> list:
    """Get buggy commits from xxxx_fix_commit.csv

    Args:
        csv (Path): path of the csv file

    Returns:
        list: list of buggy commits
    """
    buggy_strs = pd.read_csv(csv, index_col=False)['bug_commits']\
                   .to_list()
    buggy_commits = set()
    for commits in buggy_strs:
        commits = GitCommit.standardize_commit_id(commits.split(','))
        buggy_commits.update(commits)

    return list(buggy_commits)


def create_bug_commit_json(gc: GitCommit, src_csv: Path, tgt_json: Path):
    all_commits = _get_all_simple_commits(gc)
    bug_commits = get_buggy_commits_from_fix_csv(src_csv)

    logger.info(f'Number of total commits: {len(all_commits)}')
    logger.info(f'Number of buggy commits: {len(bug_commits)}')

    data = {
        'commit': [],
        'msg': [],
        'changes': [],
        'buggy': []
    }

    tbar = tqdm(all_commits)
    for commit in tbar:
        tbar.set_description(f'Fetching detailed info for {commit}')
        data['commit'].append(commit)
        data['msg'].append(gc.get_msg(commit))
        data['changes'].append(gc.get_diff(commit))
        data['buggy'].append(commit in bug_commits)

    df = pd.DataFrame(data)
    df.to_json(tgt_json, orient='table')


def create_git_matrix_csv(gc: GitCommit, src_csv: Path, tgt_csv: Path):
    if tgt_csv.exists():
        logger.info(f'Incremental sync of {tgt_csv}')
        data = pd.read_csv(tgt_csv)
    else:
        data = pd.DataFrame(columns=['commit', 'la', 'ld', 'ns', 'nd', 'nf',
                                     'ent', 'nuc', 'ndev', 'inter', 'exp',
                                     'rexp', 'sexp', 'pod', 'fix', 'buggy',
                                     'time'])

    all_commits = _get_all_simple_commits(gc)
    fix_commits = gc.get_fix_commits()
    bug_commits = get_buggy_commits_from_fix_csv(src_csv)

    tbar = tqdm(all_commits)
    rows = []
    for commit in tbar:
        tbar.set_description(f'Create matrix for {commit}')
        row = data.query(f'commit == "{commit}"').to_dict(orient='records')
        if len(row) == 0:
            row = {}
        else:
            row = row[0]

        row['commit'] = commit if not row.get('commit') else row['commit']
        if not row.get('la') or not row.get('ld'):
            la, ld = gc.get_numstat(commit)
            row['la'] = la
            row['ld'] = ld
        if not row.get('ns') or not row.get('nd') or not row.get('nf'):
            fnames = gc.get_changed_filenames(commit)
            if not row.get('ns'):
                row['ns'] = len(get_subsys(fnames))
            if not row.get('nd'):
                row['nd'] = len(get_dir(fnames))
            if not row.get('nf'):
                row['nf'] = len(fnames)
        if not row.get('nuc') or not row.get('ndev'):
            hset, anset = gc.get_former_commits(commit)
            row['nuc'] = len(hset)
            row['ndev'] = len(anset)
        if not row.get('inter'):
            row['inter'] = gc.get_aver_interval(commit)
        if not row.get('ent'):
            row['ent'] = gc.get_entropy(commit)
        if not row.get('exp'):
            row['exp'] = len(gc.get_author_exp(commit))
        if not row.get('rexp'):
            row['rexp'] = gc.get_author_recent_exp(commit)
        if not row.get('sexp'):
            row['sexp'] = gc.get_author_subssys_exp(commit)
        if not row.get('pod'):
            row['pod'] = gc.get_author_proportion(commit)
        if not row.get('fix'):
            row['fix'] = commit in fix_commits
        if not row.get('buggy'):
            row['buggy'] = commit in bug_commits
        if not row.get('time'):
            row['time'] = gc.get_author_time(commit)

        rows.append(row)

    new_df = pd.DataFrame(rows)
    new_df.to_csv(tgt_csv, index=False)


def create_contract_datasets(platform_csv: Path,
                             saved_dir: Path,
                             inc: bool):
    """ Create csv datasets for smart contracts.

    Args:
        platform_csv (Path): path to `platform.csv`
        saved_dir (Path): where to put newly created csv files
        inc (bool): run in incremental mode
    """
    df = pd.read_csv(platform_csv, index_col=False)
    for _, row in df.iterrows():
        plat = row['platform']
        git_addr = row['github_addr']
        plat_dir = saved_dir / plat
        plat_dir.mkdir(parents=True, exist_ok=True)
        fcsv = plat_dir / f'{plat}_fix_commits.csv'
        bjson = plat_dir / f'{plat}_buggy_commits.json'
        mcsv = plat_dir / f'{plat}_matrix.csv'

        if _do_all_data_exist([fcsv, bjson, mcsv]) and not inc:
            logger.info(f'All files related to {plat} smart contract exist.')
            continue

        with GitCommit(git_addr) as gc:
            if not fcsv.exists():
                logger.info(f'Get bug-fixed commit data from {plat}')
                create_fix_commit_csv(gc, fcsv)
            else:
                logger.info(f'Data exists. Skip collect data {fcsv}')

            if not bjson.exists():
                logger.info(f'Get buggy commits data from {plat}')
                create_bug_commit_json(gc, fcsv, bjson)
            else:
                logger.info(f'Data exists. Skip collect data {bjson}')

            logger.info(f'Get git matrixes from {plat}')
            create_git_matrix_csv(gc, fcsv, mcsv)
