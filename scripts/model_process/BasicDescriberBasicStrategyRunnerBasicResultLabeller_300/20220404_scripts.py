import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import os
from sklearn.metrics import confusion_matrix
from utils_classifier import UtilsClassifier
from sklearn import metrics
import numpy as np

#Read data from tsv file
DATA_FOLDER_PATH = os.path.join(os.getcwd(), '..', 'data')
filename = 'BasicDescriberBasicStrategyRunnerBasicResultLabeller_300_dataframe.tsv'
df = pd.read_csv(os.path.join(DATA_FOLDER_PATH, filename), sep='\t', index_col=[0])

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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

#Get random forest classifier
random_forest_clf = RandomForestClassifier(n_estimators=100)

#Train model
random_forest_clf.fit(X_train, y_train)

#Predict y for test set
y_pred = random_forest_clf.predict(X_test)

#Accuracy
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

#Feature importance
feature_imp = pd.Series(random_forest_clf.feature_importances_, index=X.columns).sort_values(ascending=False)

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#Terrible ce qu'on a. Il misclassifie toutes les lignes qui ont un succès (sauf 1).

#Add weight to our success label {0: 1, 1: 5}
random_forest_clf = RandomForestClassifier(n_estimators=100, class_weight={0: 1, 1: 100})

#Train model
random_forest_clf.fit(X_train, y_train)

#Predict y for test set
y_pred = random_forest_clf.predict(X_test)

#Accuracy
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

#Feature importance
feature_imp = pd.Series(random_forest_clf.feature_importances_, index=X.columns).sort_values(ascending=False)

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
#C'est toujours pas terrible on va tenter en virant des colonnes
#Par contre quand il prédit 1, c'est uniquement des true 1. Donc une précision de 100%
#Mais 95% de faux négatifs.
#

#Delete some cols that are not comparable
X = X.drop(['raw_diff_highestlowest', 'raw_diff_Q3Q1', 'Q1', 'lowest_price', 'median', 'highest_price', 'Q3', 'quote_increment'], axis=1)

#Get train and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

#Add weight to our success label {0: 1, 1: 5}
random_forest_clf = RandomForestClassifier(n_estimators=100, class_weight={0: 1, 1: 100})

#Train model
random_forest_clf.fit(X_train, y_train)

#Predict y for test set
y_pred = random_forest_clf.predict(X_test)

#Accuracy
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

#Feature importance
feature_imp = pd.Series(random_forest_clf.feature_importances_, index=X.columns).sort_values(ascending=False)

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
#C'est encore pire mdr. 100% faux négatif, et 1 faux positif.
#Tentons avec un autre modèle. Un SVC
#

#Standardization of X for using SVC
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X = scaler.fit_transform(X)

#Get train and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

#Let's get df to plot, standardized
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
df_to_plot = df.drop(['raw_diff_highestlowest', 'raw_diff_Q3Q1', 'Q1', 'lowest_price', 'median', 'highest_price', 'Q3', 'quote_increment'], axis=1)
columns = df_to_plot.columns.to_numpy()
label_col_name = 'result_label'
features = np.delete(columns, np.where(columns == label_col_name))
ct = ColumnTransformer([
        ('scaler', StandardScaler(), features)
    ], remainder='passthrough')
df_to_plot = ct.fit_transform(df_to_plot)
df_to_plot = pd.DataFrame(df_to_plot)
df_to_plot = df_to_plot.set_axis(columns, axis=1, inplace=False)


#Let's look features vs features plot
import plotly.express as px
fig = px.scatter_matrix(
    df_to_plot,
    dimensions=features,
    color="result_label"
)
fig.update_traces(diagonal_visible=True)
fig.show()

#Let's look what our data looks like after dimension reduction
from sklearn.decomposition import PCA
pca = PCA()
components = pca.fit_transform(df_to_plot[features])
labels = {
    str(i): f"PC {i+1} ({var:.1f}%)"
    for i, var in enumerate(pca.explained_variance_ratio_ * 100)
}

fig = px.scatter_matrix(
    components,
    labels=labels,
    dimensions=range(4),
    color=df_to_plot["result_label"]
)
fig.update_traces(diagonal_visible=False)
fig.show()

#Looking at the pca it feels completly impossible to use a SVC with a polynomial kernel or a gaussian rbf kernel
#But let's try it anyways. Let's start with the polynomial kernel
y = df_to_plot['result_label']
X = df_to_plot.drop(['result_label'], axis=1)

#Get train and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

#Train SVC
from sklearn.svm import SVC
svm_clf = SVC(kernel='poly', degree=10, coef0=15, C=100)
svm_clf.fit(X_train, y_train)

#Get y pred
y_pred = svm_clf.predict(X_test)

#Accuracy
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
#Not great. 0.38 success were well predicted. But 18% failed strat were misclassified as success.
#Let's try the gaussian rbf kernel.
#

from sklearn.model_selection import GridSearchCV

grid_search = GridSearchCV(SVC(),
                           param_grid={'kernel': ['rbf'],
                                       'gamma': [1*(10**n) for n in range(1,10, 3)],
                                       'C': [1*(10**n) for n in range(-3,3,3)]},
                           cv=3)

grid_search.fit(X_train, y_train)

#See what is the best estimator
grid_search.best_estimator_

#See what is the best score
grid_search.best_score_

#Get y pred
y_pred = grid_search.predict(X_test)

#Accuracy
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

#Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)

#Plot confusion matrix
UtilsClassifier.plot_confusion_matrix_in_pct(conf_matrix, y)

#
#Even worst than the previous classifier
#It just predicts that everything is a fail, way to go champ.
#