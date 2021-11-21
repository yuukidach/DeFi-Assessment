'''contract.py

build model for smart contract
'''

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from imblearn.over_sampling import SMOTE


def get_dataset(src: Path):
    df = pd.read_csv(src)
    df.drop(['time', 'plat'], axis=1, inplace=True)
    train, test = train_test_split(df, test_size=0.3)
    print(f'Status of train set:\n{train["buggy"].value_counts()}')
    print(f'Status of test set:\n{test["buggy"].value_counts()}')

    train_x = train.drop(['commit', 'buggy'], axis=1)
    train_y = train['buggy']

    sampled_x, sampled_y = SMOTE().fit_resample(train_x, train_y)
    logger.info(f'After over sampling, size of test set: {sampled_x.shape}')

    test_x = test.drop(['commit', 'buggy'], axis=1)
    test_y = test['buggy']

    return sampled_x, sampled_y, test_x, test_y


def evaluate_model(model, test_x, test_y):
    pred = model.predict(test_x)
    report = classification_report(test_y, pred)
    unique_label = np.unique([test_y, pred])
    cmtx = pd.DataFrame(confusion_matrix(test_y, pred, labels=unique_label),
                        index=['true:{:}'.format(x) for x in unique_label],
                        columns=['pred:{:}'.format(x) for x in unique_label])
    logger.info('Predicting with default threshold...')
    print(report)
    print(cmtx)

    pred_prob = model.predict_proba(test_x)

    max_score = 0
    th = 0
    for i in range(1, 100):
        pred = (pred_prob[:, 1] >= i/100)
        score = f1_score(test_y, pred)
        if score > max_score:
            max_score = score
            th = i/100

    logger.info(f'Threshhold: {th}; Max-Score: {max_score}')
    pred = (pred_prob[:, 1] >= th)
    report = classification_report(test_y, pred)
    logger.info('Predicting with best threshold about f1-score')
    print(report)
    print(confusion_matrix(test_y, pred))

    return th


def train(src: Path, dir: Path):
    dir.mkdir(parents=True, exist_ok=True)
    train_x, train_y, test_x, test_y = get_dataset(src)
    rf = RandomForestClassifier(
        n_estimators=300,
        criterion='entropy',
        max_features=6
    )
    logger.info('Fitting model...')
    rf.fit(train_x, train_y)
    evaluate_model(rf, test_x, test_y)
    p = dir / 'random_forest.joblib'
    joblib.dump(rf, p)
    logger.info(f'Model savd in {p}')


def predict_prob(x, mpath: Path, th: float = 0.5):
    model = joblib.load(mpath)
    pred = model.predict_proba(x)
    return pred[:, 1]
