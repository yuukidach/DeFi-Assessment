'''
This file is to build model for esg factors.
'''

from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.callbacks import Callback
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

dir = '../data_collection/token_history/'


# read values from csv and keep time and price
def readTokens(token):
    data = pd.read_csv(dir + token)
    data['time'] = data['snapped_at'].str[0:10]
    values = data[['time', 'price']]
    return values


def data_process(name):
    data = pd.read_csv(dir + name)
    scaler = MinMaxScaler()
    data_scaler = scaler.fit_transform(data[['price']])

    x = []
    y = []
    for i in range(7, len(data_scaler)):
        x.append(data_scaler[i - 7:i, 0])
        y.append(data_scaler[i, 0])

    x, y = np.array(x), np.array(y)
    x = np.reshape(x, (x.shape[0], x.shape[1], 1))

    Ntrain = int(0.8 * data_scaler.shape[0])
    x_train = x[:Ntrain]
    y_train = y[:Ntrain]
    x_test = x[Ntrain:]
    y_test = y[Ntrain:]

    return x_train, y_train, x_test, y_test


def train(name):
    x_train, y_train, x_test, y_test = data_process(name=name)

    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    history = LossHistory()
    model.fit(x_train, y_train, batch_size=1, epochs=10, validation_data=(x_test, y_test), callbacks=[history])
    # history.loss_plot('epoch')
    return model


class LossHistory(Callback):  # 继承自Callback类

    '''
    在模型开始的时候定义四个属性，每一个属性都是字典类型，存储相对应的值和epoch
    '''

    def on_train_begin(self, logs={}):
        self.losses = {'batch': [], 'epoch': []}
        self.accuracy = {'batch': [], 'epoch': []}
        self.val_loss = {'batch': [], 'epoch': []}
        self.val_acc = {'batch': [], 'epoch': []}

    # 在每一个batch结束后记录相应的值
    def on_batch_end(self, batch, logs={}):
        self.losses['batch'].append(logs.get('loss'))
        self.accuracy['batch'].append(logs.get('accuracy'))
        self.val_loss['batch'].append(logs.get('val_loss'))
        self.val_acc['batch'].append(logs.get('val_accuracy'))

    # 在每一个epoch之后记录相应的值
    def on_epoch_end(self, batch, logs={}):
        self.losses['epoch'].append(logs.get('loss'))
        self.accuracy['epoch'].append(logs.get('accuracy'))
        self.val_loss['epoch'].append(logs.get('val_loss'))
        self.val_acc['epoch'].append(logs.get('val_accuracy'))

    def loss_plot(self, loss_type):
        '''
        loss_type：指的是 'epoch'或者是'batch'，分别表示是一个batch之后记录还是一个epoch之后记录
        '''
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


if __name__ == '__main__':
    suffix = '-usd-max.csv'
    aaveModel = train('aave' + suffix)
