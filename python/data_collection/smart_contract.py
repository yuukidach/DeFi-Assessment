import logging
from typing import ByteString
import pandas as pd
from pathlib import Path
from functools import reduce
from tqdm.auto import tqdm
from .gitcmd import GitCommit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _do_all_data_exist(paths: list) -> bool:
    """ Chekc if all csv files are existing

    Args:
        paths (list): list of csv files

    Returns:
        bool: true or false
    """
    return reduce(lambda x, y: x.exists() & y.exists(), paths)


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
    
    df =  pd.DataFrame(data)
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


def create_bug_commit_csv(gc: GitCommit, src_csv: Path, tgt_json: Path):
    all_commits = gc.get_commits()
    merge_commits = gc.get_commits('merge')
    # remove merge commits which contain too many changes
    all_commits = set(all_commits) - set(merge_commits) - set(gc.init_commit)
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


def create_contract_datasets(platform_csv: Path, 
                              saved_dir: Path, 
                              force: bool):
    """ Create csv datasets for smart contracts.

    Args:
        platform_csv (Path): path to `platform.csv`
        saved_dir (Path): where to put newly created csv files
        force (bool): force to re-collect or not
    """
    df = pd.read_csv(platform_csv, index_col=False)
    for _, row in df.iterrows():
        plat = row['platform']
        git_addr = row['github_addr']
        plat_dir = saved_dir / plat
        plat_dir.mkdir(parents=True, exist_ok=True)
        fcsv = plat_dir / f'{plat}_fix_commits.csv'
        bjson = plat_dir / f'{plat}_buggy_commits.json'

        if _do_all_data_exist([fcsv, bjson]) and not force:
            logger.info(f'All files related to {plat} smart contract exist.')
            continue
        
        with GitCommit(git_addr) as gc:
            if force or not fcsv.exists():
                logger.info(f'Get bug-fixed commit data from {plat}')
                create_fix_commit_csv(gc, fcsv)
            else:
                logger.info(f'Data exists. Skip collect data {fcsv}.')
            
            if force or not bjson.exists():
                logger.info(f'Get buggy commits data from {plat}')
                create_bug_commit_csv(gc, fcsv, bjson)
            else:
                logger.info(f'Data exists. Skip collect data {bjson}')
