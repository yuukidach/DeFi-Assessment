import logging
import pandas as pd
from pathlib import Path
from tqdm.auto import tqdm
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
        

def create_bug_commit_csv():
    pass


def create_contract_datasets(platform_csv: Path, saved_dir: Path):
    df = pd.read_csv(platform_csv, index_col=False)
    for _, row in df.iterrows():
        plat = row['platform']
        git_addr = row['github_addr']
        plat_dir = saved_dir / plat
        plat_dir.mkdir(parents=True, exist_ok=True)
        fcsv = plat_dir / f'{plat}_fix_commits.csv'

        if fcsv.exists():
            logging.info(f'Data exists. Skip collect data {fcsv}.')
            continue
        else:
            create_fix_commit_csv(git_addr, fcsv)

    

if __name__ == '__main__':
    create_contract_datasets(Path('/mnt/d/Projects/DeFi-Lending-Evaluation/datasets/platforms.csv'),
                              Path('/mnt/d/Projects/DeFi-Lending-Evaluation/datasets'))
    