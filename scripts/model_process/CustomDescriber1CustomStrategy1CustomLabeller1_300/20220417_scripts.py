import os
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scripts.utilities.utils_classifier import UtilsClassifier
from tensorflow import keras
from sklearn.utils import class_weight
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np


#Read data from tsv file
DATA_FOLDER_PATH = os.path.join(os.getcwd(), 'data')
filename = 'CustomDescriber1CustomStrategy1CustomLabeller1_300_dataframe.tsv'
df = df = pd.read_csv(os.path.join(DATA_FOLDER_PATH, filename), sep='\t', index_col=[0])


#####
#Machine learning on classification
######

#Drop unused columns for training and labelling
df = df.drop(['currency_pair_id', 'date_start_process','nb_sold_order', 'nb_bought_order'
              , 'gain_loss_percentage'
              , 'gain_loss'
              , 'quote_increment'
              , 'y_resistance'
              , 'y_support'], axis=1)

df = df.reset_index(drop=True)

#Separate features and label
y = df['result_label']
X = df.drop(['result_label'], axis=1)

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

#Get model
input = keras.layers.Input(shape=X_train.shape[1:])
hidden1 = keras.layers.Dense(100, activation='relu')(input)
hidden2 = keras.layers.Dense(100, activation='relu')(hidden1)
hidden3 = keras.layers.Dense(100, activation='relu')(hidden2)
hidden4 = keras.layers.Dense(100, activation='relu')(hidden3)
output = keras.layers.Dense(1, activation='sigmoid')(hidden4)
model = keras.Model(inputs=[input], outputs=[output])

#Get class weight
class_weights = class_weight.compute_class_weight(class_weight='balanced',
                                                 classes=np.unique(y_train),
                                                 y=y_train)
class_weights = [10, 1]

#Compile model
model.compile(loss='binary_crossentropy',
              optimizer='sgd',
              metrics=["accuracy"])

#Train the model
early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
history_training = model.fit(X_train, y_train,
                             epochs = 2000,
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


#####
# Let's try the same thing without the one that obiously can't be profitable
#####

df = df = pd.read_csv(os.path.join(DATA_FOLDER_PATH, filename), sep='\t', index_col=[0])
df = df.drop(['currency_pair_id', 'date_start_process','nb_sold_order', 'nb_bought_order'
              , 'gain_loss_percentage'
              , 'gain_loss'
              , 'quote_increment'], axis=1)

df = df.reset_index(drop=True)

#Calcul the gain loss of a single trade
fees_rate = 0.006
quote_volume = 10
df['one_trade_gain_loss'] = ((((quote_volume - (fees_rate * quote_volume)) / df['y_support']) * (1 - fees_rate)) * df['y_resistance']) - quote_volume

#Drop the ones that can't be profitable
df = df[df['one_trade_gain_loss'] > 0]
df = df.reset_index(drop=True)

#Separate features and label
y = df['result_label']
X = df.drop(['result_label'], axis=1)

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

#Get model
input = keras.layers.Input(shape=X_train.shape[1:])
hidden1 = keras.layers.Dense(100, activation='relu')(input)
hidden2 = keras.layers.Dense(100, activation='relu')(hidden1)
hidden3 = keras.layers.Dense(100, activation='relu')(hidden2)
hidden4 = keras.layers.Dense(100, activation='relu')(hidden3)
output = keras.layers.Dense(1, activation='sigmoid')(hidden4)
model = keras.Model(inputs=[input], outputs=[output])

#Get class weight
class_weights = class_weight.compute_class_weight(class_weight='balanced',
                                                 classes=np.unique(y_train),
                                                 y=y_train)
class_weights = [10, 1]

#Compile model
model.compile(loss='binary_crossentropy',
              optimizer='sgd',
              metrics=["accuracy"])

#Train the model
early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
history_training = model.fit(X_train, y_train,
                             epochs = 300,
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

####
#Still better than usual, we have almost 60% success recognizing prices history on which you can apply this strategy
#We could try to backtest the model and see if would give good results.
#Let's first try to get the best model we can using a randomized grid search
###

def build_model_binary_classification(n_hidden=1, n_neurons=50, learning_rate=3e-3, input_shape=[8], activation_hid = 'relu'):
    model = keras.models.Sequential()
    model.add(keras.layers.InputLayer(input_shape=input_shape))
    for layer in range(n_hidden):
        model.add(keras.layers.Dense(n_neurons, activation=activation_hid))
    model.add(keras.layers.Dense(1, activation='sigmoid'))
    optimizer = keras.optimizers.SGD(learning_rate=learning_rate)
    model.compile(loss='binary_crossentropy',
                  optimizer=optimizer,
                  metrics=["accuracy"])
    return model

from scikeras.wrappers import KerasClassifier

keras_binary_classifier = KerasClassifier(
    build_fn=build_model_binary_classification,
    input_shape=X_train.shape[1:],
    n_hidden=1,
    n_neurons=100,
    learning_rate=3e-3
)

#Now we got our sickit_learn wrapper we can use the randomizedsearch
from scipy.stats import reciprocal
from sklearn.model_selection import RandomizedSearchCV

param_distribs = {
    'n_hidden' : [1,2,3,4,5],
    'n_neurons' : [50, 100, 150],
    'learning_rate' : reciprocal(3e-4, 3e-2),
    'input_shape' : X_train.shape[1:],
}

rnd_search_cv = RandomizedSearchCV(
    keras_binary_classifier,
    param_distribs,
    n_iter=10,
    cv=3
)

rnd_search_cv.fit(
    X_train,
    y_train,
    epochs=200,
    validation_data=(X_valid, y_valid),
    callbacks=tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
)

y_pred_proba = rnd_search_cv.best_estimator_.predict(X_test)

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

####
# Best params 3e-3 n_hidden = 4, n_neurons=150
# Let's improve a bit more our model using different class weights
####

list_class_weights = [
    [1, 1],
    [10, 1],
    [100, 1],
    [1, 10],
    [1, 100]
]

dic_weight_models = {}
for class_weights in list_class_weights:
    model = build_model_binary_classification(
        n_hidden=4,
        n_neurons=150,
        learning_rate=3e-3,
        input_shape=X_train.shape[1:]
    )
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
    history_training = model.fit(X_train, y_train,
                                 epochs = 200,
                                 class_weight={i : class_weights[i] for i in range(0,2)},
                                 callbacks=[early_stopping],
                                 validation_data=(X_valid, y_valid))



    key_dict = str(class_weights[0]) + '_' + str(class_weights[1])
    list_value = [model, history_training.history]
    dic_weight_models[key_dict] = list_value

for key_weight, list_value in dic_weight_models.items():
    print(key_weight + ' : acc score : ' +  str(list_value[1]['val_accuracy'][-1]))

#Best model are the one with same weight, let's check a bit more values around it

list_class_weights = [
    [1, 1],
    [1, 2],
    [2, 1],
    [3, 1],
    [1, 3],
]

dic_weight_models = {}
for class_weights in list_class_weights:
    model = build_model_binary_classification(
        n_hidden=4,
        n_neurons=150,
        learning_rate=3e-3,
        input_shape=X_train.shape[1:]
    )
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
    history_training = model.fit(X_train, y_train,
                                 epochs = 200,
                                 class_weight={i : class_weights[i] for i in range(0,2)},
                                 callbacks=[early_stopping],
                                 validation_data=(X_valid, y_valid))



    key_dict = str(class_weights[0]) + '_' + str(class_weights[1])
    list_value = [model, history_training.history]
    dic_weight_models[key_dict] = list_value

for key_weight, list_value in dic_weight_models.items():
    print(key_weight + ' : acc score : ' +  str(list_value[1]['val_accuracy'][-1]))


####"
# Comment previous results
# On a du 1_1 : acc score : 0.6756756901741028
# Et du 3_1 : acc score : 0.6798336505889893
# Et 1_2 : acc score : 0.6673596501350403
# Let's find the best model for those three weights with different initialization
#####

df = df = pd.read_csv(os.path.join(DATA_FOLDER_PATH, filename), sep='\t', index_col=[0])
df = df.drop(['currency_pair_id', 'date_start_process','nb_sold_order', 'nb_bought_order'
              , 'gain_loss_percentage'
              , 'gain_loss'
              , 'quote_increment'], axis=1)

df = df.reset_index(drop=True)

#Calcul the gain loss of a single trade
fees_rate = 0.006
quote_volume = 10
df['one_trade_gain_loss'] = ((((quote_volume - (fees_rate * quote_volume)) / df['y_support']) * (1 - fees_rate)) * df['y_resistance']) - quote_volume

#Drop the ones that can't be profitable
df = df[df['one_trade_gain_loss'] > 0]
df = df.drop(['y_support', 'y_resistance'], axis=1)
df = df.reset_index(drop=True)

#Separate features and label
y = df['result_label']
X = df.drop(['result_label'], axis=1)

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

list_class_weights = [
    [1, 1],
    [1, 2],
    [3, 1],
]

dic_weight_models = {}
for class_weights in list_class_weights:
    for i in range(5):

        #Key used to save the models and their training
        key_dict = str(class_weights[0]) + '_' + str(class_weights[1]) + '_v' + str(i)

        #Neuronal model
        model = build_model_binary_classification(
            n_hidden=4,
            n_neurons=150,
            learning_rate=3e-3,
            input_shape=X_train.shape[1:]
        )

        #Callbacks used for early stopping and saving best model
        early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=50)
        checkpoint_filepath = os.path.join(os.getcwd(), 'bin', key_dict)
        model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_filepath,
            save_weights_only=False,
            monitor='val_accuracy',
            mode='max',
            save_best_only=True)

        #Train and catch the history of the training
        history_training = model.fit(X_train, y_train,
                                     epochs = 400,
                                     class_weight={i : class_weights[i] for i in range(0,2)},
                                     callbacks=[early_stopping, model_checkpoint_callback],
                                     validation_data=(X_valid, y_valid))



        #Add to the dictionnary
        list_value = [model, history_training.history]
        dic_weight_models[key_dict] = list_value

#Print perf
for key_weight, list_value in dic_weight_models.items():
    print(key_weight + ' : acc score : ' +  str(max(list_value[1]['accuracy']))
          + ' : loss score : ' +  str(min(list_value[1]['loss']))
          + ' : val acc score : ' +  str(max(list_value[1]['val_accuracy']))
          + ' : val loss score : ' +  str(min(list_value[1]['val_loss'])))


# 1_1_v0 : acc score : 0.8001387715339661 : loss score : 0.4271796941757202 : val acc score : 0.6964656710624695 : val loss score : 0.5958542823791504
# 1_1_v1 : acc score : 0.8498727679252625 : loss score : 0.3551793098449707 : val acc score : 0.6902287006378174 : val loss score : 0.59456467628479
# 1_1_v2 : acc score : 0.7423085570335388 : loss score : 0.523959755897522 : val acc score : 0.6881496906280518 : val loss score : 0.5920976996421814
# 1_1_v3 : acc score : 0.7356002926826477 : loss score : 0.5354910492897034 : val acc score : 0.6819126605987549 : val loss score : 0.6103762984275818
# 1_1_v4 : acc score : 0.7601202726364136 : loss score : 0.4953739643096924 : val acc score : 0.704781711101532 : val loss score : 0.593705952167511
# 1_2_v0 : acc score : 0.8699976801872253 : loss score : 0.41878074407577515 : val acc score : 0.6819126605987549 : val loss score : 0.6179903745651245
# 1_2_v1 : acc score : 0.6655100584030151 : loss score : 0.7808473110198975 : val acc score : 0.6153846383094788 : val loss score : 0.648831307888031
# 1_2_v2 : acc score : 0.9104788303375244 : loss score : 0.3141879737377167 : val acc score : 0.6632016897201538 : val loss score : 0.6306576132774353
# 1_2_v3 : acc score : 0.660189688205719 : loss score : 0.792116105556488 : val acc score : 0.6361746191978455 : val loss score : 0.651494026184082
# 1_2_v4 : acc score : 0.9733980894088745 : loss score : 0.135588139295578 : val acc score : 0.6860706806182861 : val loss score : 0.6333222389221191

#The best 1_1_v4
#We are going to load it

model = tf.keras.models.load_model(os.path.join(os.getcwd(), 'bin', '1_1_v4'))

#Y pred
y_pred_proba = model.predict(X_test)
y_pred = y_pred_proba > 0.72

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

####
# With > 0.72 probs we got 7 true positive / 179 et 0 False positive
# It is quite good, lets batcktest the model and see if it is profitable at least
####