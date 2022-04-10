import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from sklearn.decomposition import PCA

class UtilsClassifier:

    """Show plot of confusion matrix as pct"""
    @staticmethod
    def plot_confusion_matrix_in_pct(conf_matrix, y):
        conf_matrix_pct = conf_matrix.astype('float') / conf_matrix.sum(axis=1)[:, np.newaxis]
        plt.figure(figsize=(5, 3))
        plt.subplots_adjust(bottom=0.20)
        sns.set(font_scale=1)
        sns.heatmap(conf_matrix_pct, annot=True, annot_kws={'size': 10},
                    cmap=plt.cm.Greens, linewidths=0.2)
        class_names = y.value_counts().index.to_numpy()
        tick_marks = np.arange(len(class_names))
        tick_marks2 = tick_marks + 0.5
        plt.xticks(tick_marks, class_names, rotation=25)
        plt.yticks(tick_marks2, class_names, rotation=0)
        plt.xlabel('Predicted label')
        plt.ylabel('True label')
        plt.title('Confusion Matrix')
        plt.show()


    @staticmethod
    def plot_features_vs_featues(df, feature_cols, label_col):
        fig = px.scatter_matrix(
            df,
            dimensions=feature_cols,
            color=label_col
        )
        fig.update_traces(diagonal_visible=True)
        fig.show()

    @staticmethod
    def plot_pc_vs_pc_from_pca(df, feature_cols, label_col, nb_pc):
        pca = PCA()
        components = pca.fit_transform(df[feature_cols])
        labels = {
            str(i): f"PC {i + 1} ({var:.1f}%)"
            for i, var in enumerate(pca.explained_variance_ratio_ * 100)
        }

        fig = px.scatter_matrix(
            components,
            labels=labels,
            dimensions=range(nb_pc),
            color=df[label_col]
        )
        fig.update_traces(diagonal_visible=False)
        fig.show()