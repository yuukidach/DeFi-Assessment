'''
This file is to build model for finance factors.
'''

from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.callbacks import Callback
from keras.models import load_model
from textblob import TextBlob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

dir_token = 'data/token_history/'
dir_esg = 'data/social/'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/87.0.4280.66 Safari/537.36 '
}
scaler = MinMaxScaler()


# read values from csv and keep time and price
def read_tokens(token):
    data = pd.read_csv(dir_token + token)
    values = data[['price']]
    return values


# get the link or data of the current url
def get_response(url):
    response = requests.get(url, headers=headers)
    return response.json()


# process the data with the shape of LSTM
def data_process(name):
    data = pd.read_csv(dir_token + name)
    data_scaler = scaler.fit_transform(data[['price']])

    length = 10
    x = []
    y = []
    for i in range(length, len(data_scaler) - length):
        x.append(data_scaler[i - length:i, 0])
        y.append(data_scaler[i, 0])

    x, y = np.array(x), np.array(y)
    x = np.reshape(x, (x.shape[0], x.shape[1], 1))

    Ntrain = int(0.8 * data_scaler.shape[0])
    x_train = x[:Ntrain]
    y_train = y[:Ntrain]
    x_test = x[Ntrain:]
    y_test = y[Ntrain:]

    return x_train, y_train, x_test, y_test


# get all the Cryptocurrency data
def get_data():
    suffix = '-usd-max.csv'
    aave_x_train, aave_y_train, aave_x_test, aave_y_test = data_process(name='aave' + suffix)
    comp_x_train, comp_y_train, comp_x_test, comp_y_test = data_process(name='comp' + suffix)
    cream_x_train, cream_y_train, cream_x_test, cream_y_test = data_process(name='cream' + suffix)
    tru_x_train, tru_y_train, tru_x_test, tru_y_test = data_process(name='tru' + suffix)

    x_train = np.concatenate((aave_x_train, comp_x_train, cream_x_train, tru_x_train), axis=0)
    y_train = np.concatenate((aave_y_train, comp_y_train, cream_y_train, tru_y_train), axis=0)
    x_test = np.concatenate((aave_x_test, comp_x_test, cream_x_test, tru_x_test), axis=0)
    y_test = np.concatenate((aave_y_test, comp_y_test, cream_y_test, tru_y_test), axis=0)

    return x_train, x_test, y_train, y_test


# train the model
def train(x_train, y_train, x_test, y_test):
    model = Sequential()
    model.add(LSTM(units=32, return_sequences=True, input_shape=(x_train.shape[1], 1), dropout=0.2))
    model.add(LSTM(units=32, return_sequences=True, dropout=0.2))
    model.add(LSTM(units=32, dropout=0.2))
    model.add(Dense(units=1))

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    history = LossHistory()
    model.fit(x_train, y_train, batch_size=16, epochs=30, validation_data=(x_test, y_test), callbacks=[history])
    # history.loss_plot('epoch')
    return model


# inherit from Callback
class LossHistory(Callback):
    def on_train_begin(self, logs={}):
        self.losses = {'batch': [], 'epoch': []}
        self.accuracy = {'batch': [], 'epoch': []}
        self.val_loss = {'batch': [], 'epoch': []}
        self.val_acc = {'batch': [], 'epoch': []}

    # record every epoch
    def on_batch_end(self, batch, logs={}):
        self.losses['batch'].append(logs.get('loss'))
        self.accuracy['batch'].append(logs.get('accuracy'))
        self.val_loss['batch'].append(logs.get('val_loss'))
        self.val_acc['batch'].append(logs.get('val_accuracy'))

    # record every epoch
    def on_epoch_end(self, batch, logs={}):
        self.losses['epoch'].append(logs.get('loss'))
        self.accuracy['epoch'].append(logs.get('accuracy'))
        self.val_loss['epoch'].append(logs.get('val_loss'))
        self.val_acc['epoch'].append(logs.get('val_accuracy'))

    def loss_plot(self, loss_type):
        iters = range(len(self.losses[loss_type]))
        plt.figure()
        # acc
        plt.plot(iters, self.accuracy[loss_type], 'r', label='train acc')
        # loss
        plt.plot(iters, self.losses[loss_type], 'g', label='train loss')
        if loss_type == 'epoch':
            # val_acc
            plt.plot(iters, self.val_acc[loss_type], 'b', label='val acc')
            # val_loss
            plt.plot(iters, self.val_loss[loss_type], 'k', label='val loss')
        plt.grid(True)
        plt.xlabel(loss_type)
        plt.ylabel('acc-loss')
        plt.legend(loc="upper right")
        plt.savefig("mnist_keras.png")
        plt.show()


# draw the predict plot with the test data
def predict_plot(model, x_test, y_test):
    pred = model.predict(x_test)
    plt.figure(figsize=(12, 8))
    plt.plot(y_test, color='blue', label='Real')
    plt.plot(pred, color='red', label='Prediction')
    plt.title('Litecoin Price Prediction')
    plt.legend()
    plt.show()


# train the model
def model_train():
    x_train, x_test, y_train, y_test = get_data()
    token_model = train(x_train, y_train, x_test, y_test)
    token_model.save('token_model.h5')
    predict_plot(token_model, x_test, y_test)


# predict with one of the currency and return the binary result
def token_factor(model, currency):
    suffix = '-usd-max.csv'
    data = read_tokens(currency + suffix)
    data = data.tail(10)
    last = data.tail(1).values[0, 0]

    data = scaler.fit_transform(data)
    data = np.array(data, ndmin=10)
    data = np.reshape(data, (1, 10, 1))

    predict = model.predict(data)
    predict = scaler.inverse_transform(predict)[0, 0]
    return predict / last - 1


# use textblob to determine the esg value from comments of each Cryptocurrency
def esg_factor(currency):
    data = pd.read_csv(dir_esg + currency + '.csv')
    comments = data[['comment']].tail(10)
    esg = 0
    for i in range(0, 10):
        sentence = comments.values[i, 0]
        blob = TextBlob(sentence)
        esg = esg + blob.sentiment.polarity
    return esg


# calculate var of one day 5% for each Cryptocurrency
def var_factor(currency):
    suffix = '-usd-max.csv'
    data = read_tokens(currency + suffix)
    data['d_return'] = data['price'].pct_change()
    var = np.percentile(data.d_return.dropna(), 5)
    return var


def liquidity_factor(currency):
    url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=AAVE,COMP,CREAM,ALCX,DYDX,TRU&tsyms=USD"
    response = get_response(url)
    liquidity_factor_value = {'aave': response['RAW']['AAVE']['USD']['VOLUME24HOUR'],
                              'compound': response['RAW']['COMP']['USD']['VOLUME24HOUR'],
                              'cream': response['RAW']['CREAM']['USD']['VOLUME24HOUR'],
                              'alchemix': response['RAW']['ALCX']['USD']['VOLUME24HOUR'],
                              'dydx': response['RAW']['DYDX']['USD']['VOLUME24HOUR'],
                              'truefi': response['RAW']['TRU']['USD']['VOLUME24HOUR']}
    return liquidity_factor_value[currency]


def calculate_factors(currency):
    token_model = load_model("models/token_model.h5")
    token_factor_value = token_factor(token_model, currency)
    esg_factor_value = esg_factor(currency)
    var_factor_value = var_factor(currency)
    liquidity_factor_value = liquidity_factor(currency)
    return token_factor_value, esg_factor_value, var_factor_value, liquidity_factor_value


def get_finance_scores():
    finance_scores = []
    aave_finance_score = calculate_factors('aave')
    compound_finance_score = calculate_factors('compound')
    cream_finance_score = calculate_factors('cream')
    alchemix_finance_score = calculate_factors('alchemix')
    dydx_finance_score = calculate_factors('dydx')
    truefi_finance_score = calculate_factors('truefi')
    finance_scores.append(aave_finance_score)
    finance_scores.append(compound_finance_score)
    finance_scores.append(cream_finance_score)
    finance_scores.append(alchemix_finance_score)
    finance_scores.append(dydx_finance_score)
    finance_scores.append(truefi_finance_score)
    df = pd.DataFrame(finance_scores)
    df_finance_scores = pd.DataFrame(scaler.fit_transform(df))
    weights = [0.2, 0.3, 0.3, 0.2]
    df_finance_scores['sum'] = df_finance_scores.dot(weights)
    scores = {'Aave': df_finance_scores['sum'][0],
              'Compound': df_finance_scores['sum'][1],
              'CreamFinance': df_finance_scores['sum'][2],
              'Alchemix': df_finance_scores['sum'][3],
              'dydx': df_finance_scores['sum'][4],
              'TrueFi': df_finance_scores['sum'][5]}
    return scores


if __name__ == '__main__':
    # get_finance_scores()
    print('done')