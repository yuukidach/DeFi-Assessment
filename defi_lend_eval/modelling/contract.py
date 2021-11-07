'''contract.py

build model for smart contract
'''

import pandas as pd
import re
from pathlib import Path
from typing import List, Union
from loguru import logger


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


def read_data(fnames: List[Path], type: str='csv') -> pd.DataFrame:
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


def preprocess(df: pd.DataFrame):
    logger.info(f'Raw data size: {df.shape}')
    df = df.dropna()
    logger.info(f'After dropping NaN cells: {df.shape}')
    logger.info(df.describe())


if __name__ == '__main__':
    p = Path('/mnt/d/projects/Defi-Lending-Evaluation/data/')
    fnames = find_data_file(p)
    df = read_data(fnames)
    df = preprocess(df)
