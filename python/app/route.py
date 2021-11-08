from flask import Flask, render_template, flash, request
from wtforms import Form, validators, StringField

import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_random_secret'


@app.route('/graph')
def index():
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


data = [{
    "name": "aave",
    "contract score": "1",
    "finance score": "1",
    "total score": "1"
},
    {
        "name": "compound",
        "contract score": "2",
        "finance score": "2",
        "total score": "2"
    }, {
        "name": "cream finance",
        "contract score": "3",
        "finance score": "3",
        "total score": "3"
    }]
columns = [
    {
        "field": "name",
        "title": "name",
        "sortable": True,
    },
    {
        "field": "contract score",
        "title": "contract score",
        "sortable": True,
    },
    {
        "field": "finance score",
        "title": "finance score",
        "sortable": True,
    },
    {
        "field": "total score",
        "title": "total score",
        "sortable": True,
    }
]


@app.route('/')
def overview():
    return render_template("table.html",
                           data=data,
                           columns=columns,
                           title='Flask Bootstrap Table')


if __name__ == '__main__':
    app.run(port=8080)
