# パッケージ
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Activation, SimpleRNN, GRU
from keras import optimizers
from keras.callbacks import EarlyStopping

class FxBrain:
    # 学習モデルの定義
    def __init__(self, unitsRNN, activation="tanh",
                  recurrent_activation="sigmoid",
                  kernel_initializer="he_normal",
                  recurrent_initializer="orthogonal",) -> None:
        self.model = Sequential()
        self.model.add(GRU(unitsRNN, activation,
                  recurrent_activation,
                  kernel_initializer,
                  recurrent_initializer))
        self.model.add(Dense(1, activation="linear"))
        self.model.add(Activation("sigmoid"))
    
    # モデルを学習
    def learning(self,
                 x_train, x_val, t_train, t_val,
                 learning_rate=0.001,
                 patience=10,
                 epochs= 2000,
                 batch_size= 50,):
        optimizer = optimizers.Adam(learning_rate=learning_rate,
                              beta_1=0.9, beta_2=0.999, amsgrad=True)

        self.model.compile(optimizer=optimizer,
                        loss="mean_squared_error")

        es = EarlyStopping(monitor="val_loss",
                            patience=patience,
                            verbose=1)

        history = self.model.fit(x_train, t_train,
                        epochs=epochs, batch_size=batch_size,
                        verbose=2,
                        validation_data=(x_val, t_val),callbacks=[es])
        return history
    
    # モデル予測
    def predict(self, x):
        return self.model.predict(x)
        
    # 学習したモデルを保存
    def save_model(self) -> None:
        # 保存先がなければ作成
        dir_path = f"./models"
        dir = Path(dir_path)
        dir.mkdir(parents=True, exist_ok=True)
        # 現在の日時をつけて保存
        today = datetime.now()
        file_name = today.strftime("%T-%m-%d_%H:%M:%S")
        self.model(f"{dir_path}/model_{file_name}")