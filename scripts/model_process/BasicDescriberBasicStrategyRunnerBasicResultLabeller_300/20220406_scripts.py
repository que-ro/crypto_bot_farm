import tensorflow as tf
import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.utils import class_weight
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from utilities.utils_classifier import UtilsClassifier


###
# Get data
###

#Read data from tsv file
DATA_FOLDER_PATH = os.path.join(os.getcwd(), '..', 'data')
filename = 'BasicDescriberBasicStrategyRunnerBasicResultLabeller_300_dataframe.tsv'
df = df = pd.read_csv(os.path.join(DATA_FOLDER_PATH, filename), sep='\t', index_col=[0])

#Remove duplicates
df.drop_duplicates(subset=['currency_pair_id', 'date_start_process'])

#Filter features not used (from strat runner or labeller)
df = df.drop(['date_start_process',
              'nb_sold_order',
              'nb_bought_order',
              'gain_loss_percentage',
              'gain_loss',
              'currency_pair_id'], axis=1)
df = df.reset_index(drop=True)

#Separate features and label
y = df['result_label']
X = df.drop(['result_label'], axis=1)

#Delete: test to check what happens if
#X = X.drop(['raw_diff_highestlowest', 'raw_diff_Q3Q1', 'Q1', 'lowest_price', 'median', 'highest_price', 'Q3', 'quote_increment'
#            ,'power_ratio_highestlowest', 'power_ratio_Q3Q1'], axis=1)

#Get train and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42, stratify=y)

#Get train and validation set
X_train, X_valid, y_train, y_valid = train_test_split(X_train, y_train, test_size=0.1, random_state=42, stratify=y_train)

#Columns features
features = X_train.columns.to_numpy()

#Standardization of value
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_valid = scaler.transform(X_valid)
X_test = scaler.transform(X_test)

#Get dataframe again
X_train = pd.DataFrame(X_train)
X_valid = pd.DataFrame(X_valid)
X_test = pd.DataFrame(X_test)

#Set columns
X_train = X_train.set_axis(features, axis=1, inplace=False)
X_valid = X_valid.set_axis(features, axis=1, inplace=False)
X_test = X_test.set_axis(features, axis=1, inplace=False)

###
# Init Multi layer perceptron
###

#To install cuda -> conda install cuda
#To install cudnn -> conda install cdnn


#Get model
input = keras.layers.Input(shape=X_train.shape[1:])
hidden1 = keras.layers.Dense(100, activation='relu')(input)
hidden2 = keras.layers.Dense(100, activation='relu')(hidden1)
output = keras.layers.Dense(1, activation='sigmoid')(hidden1)
model = keras.Model(inputs=[input], outputs=[output])

#Get class weight
class_weights = class_weight.compute_class_weight(class_weight='balanced',
                                                 classes=np.unique(y_train),
                                                 y=y_train)

#Compile model
model.compile(loss='binary_crossentropy',
              optimizer='sgd',
              metrics=["accuracy"])

#Train the model
early_stopping = tf.keras.callbacks.EarlyStopping(monitor='accuracy', patience=15)
history_training = model.fit(X_train, y_train,
                             epochs = 10000,
                             class_weight={i : class_weights[i] for i in range(0,2)},
                             callbacks=[early_stopping])

#Plot history of training
pd.DataFrame(history_training.history).plot(figsize=(8,5))
plt.grid(True)
plt.gca().set_ylim(0,1)
plt.show()

#Pred y
y_pred_proba = model.predict(X_test)
y_pred = y_pred_proba > 0.87

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
# Pas ouf non plus, autant de faux positifs que de vrais positifs. Mais c'est déjà mieux.
# On tente en connectant le output avec le hidden2, totalement fait une erreur dans ce premier test
#


#Get model
input = keras.layers.Input(shape=X_train.shape[1:])
hidden1 = keras.layers.Dense(100, activation='relu')(input)
hidden2 = keras.layers.Dense(100, activation='relu')(hidden1)
output = keras.layers.Dense(1, activation='sigmoid')(hidden2)
model = keras.Model(inputs=[input], outputs=[output])

#Get class weight
class_weights = class_weight.compute_class_weight(class_weight='balanced',
                                                 classes=np.unique(y_train),
                                                 y=y_train)

#Compile model
model.compile(loss='binary_crossentropy',
              optimizer='sgd',
              metrics=["accuracy"])

#Train the model
early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=15)
history_training = model.fit(X_train, y_train,
                             epochs = 10000,
                             class_weight={i : class_weights[i] for i in range(0,2)},
                             callbacks=[early_stopping])

#Plot history of training
pd.DataFrame(history_training.history).plot(figsize=(8,5))
plt.grid(True)
plt.gca().set_ylim(0,1)
plt.show()

#Pred y
y_pred_proba = model.predict(X_test)
y_pred = y_pred_proba > 0.99

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
# Et bien pour une fois moins dégueu 18FN, 25TP et 7FP
# Peut être qu'avec plus de données et un describer plus complet (volume, volatilité etc.. on aura quelque
# chose de potable
#
