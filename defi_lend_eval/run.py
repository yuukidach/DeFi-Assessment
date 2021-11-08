import json
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


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'table.html',
        data=get_table_data(Path('docs/platforms.csv'),
                            Path('data/final.csv'), 
                            Path('models/random_forest.joblib')),
        columns=COLUMNS,
        title='DeFi Lending Platform Evaluation'
    )


@app.route('/graph')
def graph_page():
    feature = 'Bar'
    bar = create_plot(feature)
    return render_template('graph.html', plot=bar)


def create_plot(feature):
    if feature == 'Bar':
        N = 40
        x = np.linspace(0, 1, N)
        y = np.random.randn(N)
        df = pd.DataFrame({'x': x, 'y': y})  # creating a sample dataframe
        data = [
            go.Bar(
                x=df['x'],  # assign x as the dataframe column 'x'
                y=df['y']
            )
        ]
    else:
        N = 1000
        random_x = np.random.randn(N)
        random_y = np.random.randn(N)

        # Create a trace
        data = [go.Scatter(
            x=random_x,
            y=random_y,
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
        email = request.form['email']
        password = request.form['password']

        if form.validate():
            flash('Hello: {} {}'.format(name, surname))

        else:
            flash('Error: All Fields are Required')

    return render_template('form.html', form=form)


if __name__ == '__main__':
    app.run(port=8080)
    