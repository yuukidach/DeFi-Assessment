import json
import plotly
import pandas as pd
import plotly.graph_objs as go
from pathlib import Path
from flask import Flask, render_template, flash, request
from wtforms import Form, validators, StringField
from .app.data import COLUMNS, get_table_data
from .app.suggest import get_suggestion

app = Flask(__name__, template_folder='app/templates')
app.config['SECRET_KEY'] = 'some_random_secret'

INDEX_DATA = get_table_data(Path('docs/platforms.csv'),
                            Path('data/contract/contract_overview.csv'),
                            Path('models/random_forest.joblib'))


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'index.html',
        data=INDEX_DATA,
        columns=COLUMNS,
        title='DeFi Lending Platform Assessment'
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


@app.route("/suggest", methods=['GET', 'POST'])
def suggest():
    form = ReusableForm(request.form)

    if request.method == 'POST':
        # name = request.form.get('name')
        # phone = request.form.get('phone')
        profit_lv = int(request.form['profit'])
        loss_lv = int(request.form['loss'])

        profit_lv, loss_lv, plat = get_suggestion(INDEX_DATA,
                                                  profit_lv,
                                                  loss_lv)

        flash((f'Your are type of {loss_lv}-risk, {profit_lv}-yield.'
               f'You are suggested to consider {plat}.'))

    return render_template('form.html', form=form)


if __name__ == '__main__':
    app.run(port=8080, debug=False)
