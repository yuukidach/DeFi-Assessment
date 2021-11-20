import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
from defi_assessment.modelling import contract, finance
from math import sqrt

COLUMNS = [
    {'field': 'name', 'title': 'name', 'sortable': True},
    {'field': 'ctx', 'title': 'Contract Score', 'sortable': True},
    {'field': 'fin', 'title': 'Finance Score', 'sortable': True},
    {'field': 'cen', 'title': 'Intermediary Score', 'sortable': True},
    {'field': 'total', 'title': 'Total score', 'sortable': True}
]


def get_contract_row_data(commit: str, df: pd.DataFrame) -> np.array:
    """Get a single row of dataframe based on commit id

    Parameters
    ----------
    commit  str
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


def format_score(score):
    score = round(score, 2)
    return str(score) + '%'


def get_contract_score(commit: str, df: pd.DataFrame, mpath: Path) -> float:
    x = get_contract_row_data(commit, df)
    prob = contract.predict_prob(x, mpath)
    score = (1 - prob[0]) * 100
    return format_score(score)


def get_intermediary_score(oracle: int, admin: int) -> float:
    if oracle == 4:
        oracle = 100.0
    else:
        oracle = (oracle * 30) * (oracle * 30) / 90
    admin = sqrt(admin * 20) * 10
    score = 0.5 * oracle + 0.5 * admin
    return format_score(score)


def get_total_score(ctx_score, cen_score, fin_score):
    ctx_score = float(ctx_score[:-1])
    cen_score = float(cen_score[:-1])
    fin_score = float(fin_score[:-1])
    if ctx_score >= 53:
        threshold = 0.2
    else:
        threshold = 0.05

    if fin_score == 0:
        total = '-'
    else:
        total = threshold * ctx_score + 0.6 * fin_score + 0.2 * cen_score
        total = format_score(total)
    return total


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
    fin_scores = finance.get_finance_scores()
    for _, row in df.iterrows():
        name = row['platform']
        commit = row['commit']
        ctx_score = get_contract_score(commit, ref_df, ctx_mpath)
        cen_score = get_intermediary_score(row['oracle'], row['admin'])
        fin_score = format_score(fin_scores.get(name, 0)*100)
        total_score = get_total_score(ctx_score, cen_score, fin_score)
        data.append({'name': name, 'ctx': ctx_score, 'fin': fin_score,
                     'cen': cen_score, 'total': total_score})
    return data
