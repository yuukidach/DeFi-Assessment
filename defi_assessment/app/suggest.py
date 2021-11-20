import pandas as pd


def identify_user_level(level: int) -> str:
    if level < 4:
        return 'low'
    if level < 8:
        return 'medium'
    return 'high'


def match_platform(plats: list, profit_lv: str, risk_lv: str) -> dict:
    df = pd.DataFrame(plats)
    df = df[df['total'] != '-']
    df['total'] = df['total'].apply(lambda x: float(x[:-1]))
    df['fin'] = df['fin'].apply(lambda x: float(x[:-1]))
    n = df.shape[0]

    df.sort_values(by='total', inplace=True, ascending=False)
    if risk_lv == 'low':
        n = n//3
    elif risk_lv == 'medium':
        n == n // 3 * 2

    df = df.iloc[0:n, :]
    df.sort_values(by='fin', inplace=True, ascending=False)
    return df.iloc[0]['name']


def get_suggestion(plats, profit_lv, risk_lv):
    profit_lv = identify_user_level(profit_lv)
    risk_lv = identify_user_level(risk_lv)
    plat = match_platform(plats, profit_lv, risk_lv)
    return (profit_lv, risk_lv, plat)
