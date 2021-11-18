import json
import csv
import plotly
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from pathlib import Path
from flask import Flask, render_template, flash, request
from wtforms import Form, validators, StringField
from app.data import COLUMNS, get_table_data

app = Flask(__name__, template_folder='app/templates')
app.config['SECRET_KEY'] = 'some_random_secret'

INDEX_DATA=get_table_data(Path('docs/platforms.csv'),
                          Path('data/contract/final.csv'),
                          Path('models/random_forest.joblib'))


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'table.html',
        data=INDEX_DATA,
        columns=COLUMNS,
        title='DeFi Lending Platform Evaluation'
    )


@app.route('/graph')
def graph_page():
    feature = 'Bar'
    bar = create_plot(feature)
    return render_template('graph.html', plot=bar)


def create_plot(feature):
    scores = pd.read_csv('defi_lend_eval/scores.csv')
    if feature == 'Bar':
        data = [
            go.Bar(
                x=scores['name'][:6],  # assign x as the dataframe column 'x'
                y=scores['total'][:6]
            )
        ]
    else:
        # Create a trace
        data = [go.Scatter(
            x=scores['name'][:6],
            y=scores['total'][:6],
            mode='markers'
        )]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route('/bar', methods=['GET', 'POST'])
def change_features():
    feature = request.args['selected']
    graphJSON = create_plot(feature)

    return graphJSON


class ReusableForm(Form):
    name = StringField('Name:', validators=[validators.DataRequired()])
    surname = StringField('Surname:', validators=[validators.DataRequired()])


@app.route("/form", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)

    # print(form.errors)
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        benefit = request.form['benefit']
        loss = request.form['loss']

        if form.validate():
            flash('Your are type of high-risk, high-yield. Suggest Compound!')

        else:
            flash('Error: All Fields are Required')

    return render_template('form.html', form=form)


if __name__ == '__main__':
    app.run(port=8080, debug=False)
    # data = get_table_data(Path('docs/platforms.csv'),
    #                       Path('data/final.csv'),
    #                       Path('models/random_forest.joblib'))
    # f_scores = open('defi_lend_eval/scores.csv', 'w', encoding='utf-8')
    # csv_scores = csv.writer(f_scores)
    # for i in range(len(data)):
    #     csv_scores.writerow([data[i]['name'], data[i]['ctx'], data[i]['fin'], data[i]['cen'], data[i]['total']])
    # f_scores.close()
    # get_table_data_from_csv()