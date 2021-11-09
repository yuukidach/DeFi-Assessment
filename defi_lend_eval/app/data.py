import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
from modelling import contract, finance

COLUMNS = [
    { 'field': 'name', 'title': 'name', 'sortable': True },
    { 'field': 'ctx', 'title': 'Contract Score', 'sortable': True },
    { 'field': 'fin', 'title': 'Finance Score', 'sortable': True },
    { 'field': 'cen', 'title': 'Centralization Score', 'sortable': True },
    { 'field': 'total', 'title': 'Total score', 'sortable': True }
]


def get_contract_row_data(commit: str, df: pd.DataFrame) -> np.array:
    """Get a single row of dataframe based on commit id

    Parameters
    ----------
    commit : str
        commit id
    df : pd.DataFrame
        full dataframe

    Returns
    -------
    np.array
        shape:(1, 16)
    """
    df1 = df.loc[df['commit'] == commit]
    df1 = df1.drop(['commit', 'buggy'], axis=1)
    a = df1.iloc[0].to_numpy().reshape((1, -1))
    return a


def get_contract_score(commit: str, df: pd.DataFrame, mpath: Path) -> float:
    x = get_contract_row_data(commit, df)
    prob = contract.predict_prob(x, mpath)
    return str(round((1-prob[0])*100, 2))+'%'


def get_finance_score(name):
    scores = finance.get_finance_scores()
    if name in scores.keys():
        return str(round(scores[name]*100, 2))+'%'
    else:
        return 0


def get_table_data(src: Path, ref: Path, ctx_mpath: Path) -> List[Dict]:
    """Get data to display in table

    Parameters
    ----------
    src : Path
        path of the platform csv file

    ref : Path
        path of the referenced csv file which provide detailed data of smart
        contract code commit

    ctx_mpath : Path
        path of the contract model

    Returns
    -------
    List[Dict]
        [{name, contract-score, finance-score, centralization-score}]
    """
    df = pd.read_csv(src)
    ref_df = pd.read_csv(ref)
    data = []
    for _, row in df.iterrows():
        name = row['platform']
        commit = row['commit']
        ctx_score = get_contract_score(commit, ref_df, ctx_mpath)
        fin_score = get_finance_score(name)
        data.append({'name': name, 'ctx': ctx_score, 
                     'fin': fin_score, 'cen': 3,'total': 4})
    return data
