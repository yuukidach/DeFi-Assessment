import logging
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from gitcmd import GitCommit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_fix_commit_csv(url: str, csv: Path):
    data = {
        'fix_commit': [], 
        'fname': [], 
        'changed_lines': [], 
        'bug_commits': []
    }

    logger.info(f'Get bug-fixed commit data from {url}')

    with GitCommit(url) as gc:
        fix_commits = gc.get_fix_commits()
        for fc in tqdm(fix_commits):
            logger.debug(f'fectching bug-fixed data for {fc}...')
            files = gc.get_changed_filenames(fc)
            fname_lines = gc.get_changed_lines(fc, files)
            bug_commits = gc.blame_old_lines(fc, fname_lines)
            for fname, commits in bug_commits.items():
                data['fix_commit'].append(fc)
                data['fname'].append(fname)
                data['changed_lines'].append(fname_lines[fname])
                data['bug_commits'].append(commits)
    
    df =  pd.DataFrame(data)
    print(df.head(5))
        

def create_bug_commit_csv():
    pass


if __name__ == '__main__':
    create_fix_commit_csv('https://github.com/Synthetixio/synthetix', 'test')
    