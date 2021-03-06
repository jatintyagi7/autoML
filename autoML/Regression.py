# AUTOGENERATED! DO NOT EDIT! File to edit: 01_Regression.ipynb (unless otherwise specified).

__all__ = ['convert_str', 'scaler', 'comb', 'rf_colselector', 'corr_colselector', 'ColProcessor', 'interaction_feats',
           'poly_feats', 'pca_feats', 'clubbed_feats', 'preprocess', 'final_preprocessor', 'combined_metrics',
           'to_excel', 'get_table_download_link', 'GNB', 'LinearReg', 'LogisticReg', 'KNN', 'SVM', 'DT', 'RF', 'GB',
           'ERT', 'XGB', 'SGD', 'NN', 'data', 'test_data']

# Cell

import streamlit as st
import streamlit.components.v1 as components
from pdpbox import pdp

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import shap
# load JS visualization code to notebook
shap.initjs()

import base64

from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris, load_digits

#Simple Regressor
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR

#Tree based Regressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import ExtraTreesRegressor
from xgboost import XGBRegressor

#Gradient Based Regressor
from sklearn.linear_model import SGDRegressor
from sklearn.neural_network import MLPRegressor

#Preprocessing packages
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import *
from sklearn.decomposition import PCA

#Metrics
from sklearn import metrics
from sklearn.metrics import *
from sklearn.model_selection import GridSearchCV
import random
from sklearn.inspection import plot_partial_dependence

import os
import base64
from io import BytesIO

def convert_str(a):
    a = str(a)
    return a

def scaler(scaling_scheme='standard_scaler'):

    if scaling_scheme == 'max_abs_scaler':
        scal = MaxAbsScaler()

    elif scaling_scheme == 'min_max_scaler':
        scal = MinMaxScaler()

    elif scaling_scheme == 'normalizer':
        scal = Normalizer()

    elif scaling_scheme == 'quantile_transformer':
        scal = QuantileTransformer()

    elif scaling_scheme == 'robust_scaler':
        scal = RobustScaler()

    elif scaling_scheme == 'power_transformer':
        scal = PowerTransformer()

    elif scaling_scheme == 'standard_scaler':
        scal = StandardScaler()
    return scal

def comb(X, pairwise_linear=False, pairwise_product=False):

    from itertools import combinations

    X_copy = X.copy()
    columns = [str(i) for i in X.columns]
    X.columns = columns

    comb = combinations(columns, 2)

    # Print the obtained combinations
    if pairwise_linear:
        for i in list(comb):
            a = i[0]
            b = i[1]
            col_name_add = a+'+'+b
            X_copy[col_name_add] = X[a]+X[b]
            col_name_sub = a+'-'+b
            X_copy[col_name_sub] = X[a]-X[b]

    if pairwise_product:
        comb = combinations(columns, 2)
        # Print the obtained combinations
        for i in list(comb):
            a = i[0]
            b = i[1]
            col_name = a+'*'+b
            X_copy[col_name] = X[a]*X[b]
    return X_copy

def rf_colselector(X_train, y_train, no_of_cols, n_estimators=100):

    rf = RandomForestRegressor(n_estimators=n_estimators)
    rf.fit(X_train, y_train)
    importance = rf.feature_importances_
    df_importance = pd.DataFrame(importance, index = X_train.columns, columns = ['importance'])
    importance_sorted = df_importance.sort_values(by=['importance'], ascending=False)
    selected_columns = importance_sorted[:no_of_cols].index
    return selected_columns


def corr_colselector(X_train, y_train, threshold):

    d = pd.concat([X_train, y_train.reset_index(drop=True)], axis=1)
    columns = d.corr().iloc[:, -1][np.logical_or((d.corr().iloc[:, -1] > threshold), (d.corr().iloc[:, -1] < -threshold))].index
    return columns[:-1], d.corr()


class ColProcessor():
    def __init__(self, cardinality, rf_col=False, corr_col=False, label_enc=False, interaction_only=False, poly_feat=False):

        self.rf_col = rf_col
        self.corr_col = corr_col

        self.label_enc = label_enc

        self.interaction_only = interaction_only
        self.poly_feat = poly_feat

        self.cardinality = cardinality

    def fit(self, X, y=None):
        categorical_cols = [cname for cname in X.columns if X[cname].nunique() < self.cardinality and
                            X[cname].dtype == "object"]
        numerical_cols = [cname for cname in X.columns if X[cname].dtype in ['int64', 'float64']]
        my_cols = categorical_cols + numerical_cols

        self.categorical_cols = categorical_cols
        self.numerical_cols = numerical_cols
        self.my_cols = my_cols

        X = X[my_cols].copy()

        imputer_num = SimpleImputer(strategy='constant')
        X_dum = imputer_num.fit_transform(X[self.numerical_cols])
        self.imputer_num = imputer_num

        if self.categorical_cols:
            imputer_cat = SimpleImputer(strategy='most_frequent')
            X_cat = imputer_cat.fit_transform(X[self.categorical_cols])
            self.imputer_cat = imputer_cat

            if not self.label_enc:
                Ohe = OneHotEncoder(handle_unknown='ignore')
                Ohe.fit(X_cat)
                self.Ohe = Ohe
            else:
                OrdEnc = OrdinalEncoder(handle_unknown='ignore')
                X_cat = OrdEnc.fit(X_cat)
                self.OrdEnc = OrdEnc

        return self

    def transform(self, X, y=None):
        X_num = pd.DataFrame(data=self.imputer_num.transform(X[self.numerical_cols]), columns=self.numerical_cols)
        if self.categorical_cols:

            if not self.label_enc:
                X_cat = pd.DataFrame(data=self.Ohe.transform(self.imputer_cat.transform(X[self.categorical_cols])).toarray(),
                                     columns=self.Ohe.get_feature_names(input_features=self.categorical_cols))
                data = pd.concat([X_cat, X_num], axis = 1)
            else:
                X_cat = pd.DataFrame(self.OrdEnc.transform(self.imputer_cat.transform(X[self.categorical_cols])), columns=self.categorical_cols)
                data = pd.concat([X_cat.reset_index(drop=True), X_num], axis = 1)

        else:
            data = X_num

        return data, X_num

def interaction_feats(X):
    interaction = PolynomialFeatures(2, interaction_only=True)
    interaction.fit(X)
    X_interaction = pd.DataFrame(data=interaction.transform(X), columns=interaction.get_feature_names(X.columns))
    return X_interaction

def poly_feats(X):
    poly = PolynomialFeatures(2)
    poly.fit(X)
    X_poly = pd.DataFrame(data=poly.transform(X), columns=poly.get_feature_names(X.columns))
    return X_poly

def pca_feats(X, n_comp):
    pca = PCA(n_components=n_comp)
    pca.fit(X)
    X_pca = pd.DataFrame(data=pca.transform(X))
    return X_pca

def clubbed_feats(X, polynomial_features, interaction_only, pca_on):

    if polynomial_features:
        X = poly_feats(X)

    elif interaction_only:
        X = interaction_feats(X)

    if pca_on:
        X = pca_feats(X, 100)

    return X

def preprocess(X_train,
               y_train,
               X_valid,
               X_test=None,
               rf_col_selection=False,
               rf_no_of_cols=20,
               rf_n_estimators=100,
               corr_col_selection=False,
               corr_threshold=0.01,
               pairwise_linear=False,
               pairwise_product=False):

    X_train = comb(X=X_train, pairwise_linear=pairwise_linear, pairwise_product=pairwise_product)
    X_valid = comb(X=X_valid, pairwise_linear=pairwise_linear, pairwise_product=pairwise_product)
    if type(X_test)!=type(None):
        X_test = comb(X=X_test, pairwise_linear=pairwise_linear, pairwise_product=pairwise_product)

    return X_train, X_valid, X_test


def final_preprocessor(X_train,
                       y_train,
                       X_valid,
                       X_test=None,
                       rf_col_selection=False,
                       rf_no_of_cols=20,
                       rf_n_estimators=100,
                       corr_col_selection=False,
                       corr_threshold=0.01,
                       pairwise_linear=False,
                       pairwise_product=False,
                       cardinality=100,
                       polynomial_features=False,
                       interaction_only=False,
                       pca_on=False,
                       label_enc=False
                      ):

    col = ColProcessor(cardinality=100, label_enc=label_enc)
    col.fit(X_train)
    data_train, X_train_num = col.transform(X_train)
    data_valid, X_valid_num = col.transform(X_valid)
    if type(X_test)!=type(None):
        data_test, X_test_num = col.transform(X_test)
    else:
        X_test_num = None

    X_train_num = clubbed_feats(X_train_num,
                                polynomial_features=polynomial_features,
                                interaction_only=interaction_only,
                                pca_on=pca_on)
    X_valid_num = clubbed_feats(X_valid_num,
                                polynomial_features=polynomial_features,
                                interaction_only=interaction_only,
                                pca_on=pca_on)

    if type(X_test)!=type(None):
        X_test_num = clubbed_feats(X_test_num,
                                   polynomial_features=polynomial_features,
                                   interaction_only=interaction_only,
                                   pca_on=pca_on)

    train, valid, test = preprocess(X_train_num,
                                    y_train,
                                    X_valid_num,
                                    X_test_num,
                                    rf_col_selection=rf_col_selection,
                                    rf_no_of_cols=rf_no_of_cols,
                                    rf_n_estimators=rf_n_estimators,
                                    corr_col_selection=corr_col_selection,
                                    corr_threshold=corr_threshold,
                                    pairwise_linear=pairwise_linear,
                                    pairwise_product=pairwise_product
                                    )

    if col.categorical_cols:
        if not label_enc:
            Ohe_cat_cols = col.Ohe.get_feature_names(col.categorical_cols)
            train = pd.concat([train, data_train[Ohe_cat_cols]], axis=1)
            valid = pd.concat([valid, data_valid[Ohe_cat_cols]], axis=1)
            if type(X_test)!=type(None):
                test = pd.concat([test, data_test[Ohe_cat_cols]], axis=1)
        else:
            train = data_train
            valid = data_valid
            if type(X_test)!=type(None):
                test = data_test

    if rf_col_selection:
        columns_selected = rf_colselector(train,
                                          y_train,
                                          no_of_cols=rf_no_of_cols,
                                          n_estimators=rf_n_estimators)
        train = train[columns_selected]
        valid = valid[columns_selected]

        if type(X_test)!=type(None):
            test = test[columns_selected]

    if corr_col_selection:
        corr_cols, df = corr_colselector(train, y_train, threshold=corr_threshold)
        train = train[corr_cols]
        valid = valid[corr_cols]

        if type(X_test)!=type(None):
            test = test[corr_cols]

    return train, valid, test, col


def combined_metrics(X_test, y_test, clf):

    metrics_list = [[explained_variance_score(y_test, clf.predict(X_test))],
                    [max_error(y_test, clf.predict(X_test))],
                    [mean_absolute_error(y_test, clf.predict(X_test))],
                    [mean_squared_error(y_test, clf.predict(X_test))],
#                     [mean_squared_log_error(y_test, clf.predict(X_test))],
                    [median_absolute_error(y_test, clf.predict(X_test))],
                    [mean_absolute_percentage_error(y_test, clf.predict(X_test))],
                    [r2_score(y_test, clf.predict(X_test))],
#                     [mean_poisson_deviance(y_test, clf.predict(X_test))],
#                     [mean_gamma_deviance(y_test, clf.predict(X_test))],
                   ]



    index = ['Explained Variance',
             'Max Error',
             'Mean Absolute Error',
             'Mean Squared Error',
#              'Mean Squared Log Error',
             'Median Absolute Error',
             'Mean Absolute Percentage Error',
             'R2 Score',
#              'Mean Poisson Deviance',
#              'Mean Gamma Deviance'
            ]

    df_metric = pd.DataFrame(metrics_list, index = index, columns = ['Value'])

    return df_metric

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index = False, sheet_name='Sheet1')
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) # Tried with '0%' and '#,##0.00' also.
    worksheet.set_column('A:A', None, format1) # Say Data are in column A
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="Your_File.xlsx">Download output file</a>' # decode b'abc' => abc


def GNB():
    gnb_params = {'clf__estimator':[GaussianNB()]
                 }
    return gnb_params

def LinearReg():
    lin_params = {'clf__estimator': [LinearRegression()]
                 }

    st.subheader('Linear Regression')
    fit_intercept = st.multiselect('Fit Intercept', [True, False], [True])
    normalize = st.multiselect('Normalize', [True, False], [False])

    lin_params['clf__estimator__fit_intercept'] = fit_intercept
    lin_params['clf__estimator__normalize'] = normalize
    return lin_params

def LogisticReg():
    lr_params = {'clf__estimator': [LogisticRegression()]
                    }

    st.subheader('Logistic Regression')
    penalty = st.multiselect('Penalty', ['l1', 'l2'], ['l2'])
    reg = st.multiselect('C', [0.1, 1.0, 2.0], [1.0])
    solver = st.multiselect('Solver', ['liblinear', 'newton-cg', 'lbfgs', 'sag', 'saga'], ['liblinear'])
    lr_params['clf__estimator__penalty'] = penalty
    lr_params['clf__estimator__C'] = reg
    lr_params['clf__estimator__solver'] = solver
    return lr_params

def KNN():
    knn_params = {'clf__estimator': [KNeighborsRegressor()]
                 }

    st.subheader('KNN')
    n_neighbors = st.multiselect('Neighbors', list(range(1,30)), [5])
    leaf_size = st.multiselect('Leaf Size', list(range(1,50)), [30])
    p_distance = st.multiselect('Distance Metric', [1,2], [2])

    knn_params['clf__estimator__n_neighbors'] = n_neighbors
    knn_params['clf__estimator__leaf_size'] = leaf_size
    knn_params['clf__estimator__p'] = p_distance
    return knn_params

def SVM():
    svm_params = {'clf__estimator': [SVR()]
                 }

    st.subheader('Support Vector Machines')
    c = st.multiselect('C', [0.1, 1, 10, 100, 1000], [1])
    gamma = st.multiselect('Gamma', ['scale', 'auto'], ['scale'])
    kernel = st.multiselect('Kernel', ['linear', 'rbf', 'poly', 'sigmoid'], ['rbf'])

    svm_params['clf__estimator__C'] = c
    svm_params['clf__estimator__gamma'] = gamma
    svm_params['clf__estimator__kernel'] = kernel
    return svm_params


def DT():
    dt_params = {'clf__estimator': [DecisionTreeRegressor()]}

    st.subheader('Decision Tree')
    criterion = st.multiselect('Criterion', ["gini", "entropy"], ['gini'])
    min_samp_split = st.multiselect('Min Samples Split', [2, 10], [2])
    max_depth = st.multiselect('Max Depth', [2, 5, 10], [10])

    dt_params['clf__estimator__criterion'] = criterion
    dt_params['clf__estimator__min_samples_leaf'] = min_samp_split
    dt_params['clf__estimator__max_depth'] = max_depth
    return dt_params

def RF():
    rf_params = {'clf__estimator': [RandomForestRegressor()]
                }

    st.subheader('Random Forest')
    n_estimators = st.multiselect('Number of Trees', [100, 200, 500], [100])
    max_features = st.multiselect('Max Features', [2, 10, 'auto', 'sqrt', 'log2'], ['auto'])
    max_depth = st.multiselect('Max Depth', [4,5,6,7,8, None], [None])
    criterion = st.multiselect('Criteria', ['gini', 'entropy'], ['gini'])

    rf_params['clf__estimator__n_estimators'] = n_estimators
    rf_params['clf__estimator__max_features'] = max_features
    rf_params['clf__estimator__max_depth'] = max_depth
    rf_params['clf__estimator__criterion'] = criterion
    return rf_params

def GB():
    gb_params = {'clf__estimator': [GradientBoostingRegressor()]
            }

    st.subheader('Gradient Booster')
    loss = st.multiselect('Loss Function', ['deviance', 'exponential'], ['deviance'])
    learning_rate = st.multiselect('Learning Rate', [0.001, 0.01, 0.1], [0.1])
    min_samples_split = st.multiselect('Min Samples Split', list(range(1, 10)), [2])
    min_samples_leaf = st.multiselect('Min Samples Leaf', list(range(1, 10)), [1])
    max_depth = st.multiselect('Max Depth', [1, 2, 3, 4, 5, 6], [3])
    max_features = st.multiselect('Max Features', ['auto', 'log2', 'sqrt', None], [None])
    criterion = st.multiselect('Criterion', ['friedman_mse', 'mse', 'mae'], ['friedman_mse'])
    subsample = st.multiselect('Subsample', [0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0], [1.0])
    n_estimators = st.multiselect('Number of Trees', [50, 100, 150, 200, 250], [100])

    gb_params['clf__estimator__loss'] = loss
    gb_params['clf__estimator__learning_rate'] = learning_rate
    gb_params['clf__estimator__min_samples_split'] = min_samples_split
    gb_params['clf__estimator__min_samples_leaf'] = min_samples_leaf
    gb_params['clf__estimator__max_depth'] = max_depth
    gb_params['clf__estimator__max_features']  = max_features
    gb_params['clf__estimator__criterion'] = criterion
    gb_params['clf__estimator__subsample'] = subsample
    gb_params['clf__estimator__n_estimators'] = n_estimators
    return gb_params


def ERT():
    ert_params = {'clf__estimator': [ExtraTreesRegressor()]
                 }

    st.subheader('Extra Random Trees')
    n_estimators = st.multiselect('Number of Trees', [100, 200, 500, 1000], [100]) #fix
    max_depth = st.multiselect('Max Depth', [None, 4, 5, 6, 7, 8, 9], [None])  #fix
    min_samples_leaf = st.multiselect('Min Sample per Leaf', [1, 2, 3, 4, 5], [1])
    n_jobs = st.selectbox('Parallelism', [1, 2, 3, 4, -1], 4)

    ert_params['clf__estimator__n_estimators'] = n_estimators
    ert_params['clf__estimator__max_depth'] = max_depth
    ert_params['clf__estimator__min_samples_leaf'] = min_samples_leaf
    ert_params['clf__estimator__n_jobs'] = [n_jobs]
    return ert_params

def XGB():
    xgb_params ={'clf__estimator':[XGBRegressor()]
                }

    st.subheader('XGBoost')
    n_estimators = st.multiselect('Number of Trees', list(range(50, 1000, 50)), [100]) #fix
    max_depth = st.multiselect('Max Depth', list(range(1, 20)), [6])  #fix
    min_child_weight = st.multiselect('Min Child Weight', list(range(1, 10, 1)), [1])
    gamma = st.multiselect('Gamma', list(range(0, 10)), [1])
    learning_rate = st.multiselect('Learning Rate', [0.01, 0.05, 0.1, 0.2, 0.3], [0.3])
    subsample = st.multiselect('Subsample', list(np.divide(range(5, 11), 10)), [1.0])
    booster = st.multiselect('Booster', ['gbtree', 'gblinear'], ['gbtree'])

    xgb_params['clf__estimator__n_estimators'] = n_estimators
    xgb_params['clf__estimator__max_depth'] = max_depth
    xgb_params['clf__estimator__min_child_weight'] =  min_child_weight
    xgb_params['clf__estimator__gamma'] = gamma
    xgb_params['clf__estimator__learning_rate'] = learning_rate
    xgb_params['clf__estimator__subsample'] = subsample
    xgb_params['clf__estimator__booster'] = booster
    return xgb_params

def SGD():
    sgd_params = {'clf__estimator': [SGDRegressor()]
                 }

    st.subheader('SGD')
    loss = st.multiselect('Loss Function', ['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron'], ['hinge']) #fix
    max_iter = st.multiselect('Max Iterations', list(np.multiply(range(5, 16),  100)), [1000])  #fix
    tol = st.multiselect('Tolerance', [0.0001, 0.001, 0.05, 0.1], [0.0001])
    penalty = st.multiselect('Penalty', ['l2', 'l1', 'elasticnet'], ['l2'])
    alpha = st.multiselect('Alpha', [0.0001, 0.001, 0.05, 0.1, 0.2, 0.3], [0.0001])
    n_jobs = st.selectbox('Parallelization', [1, 2, 3, 4, -1], 4)

    sgd_params['clf__estimator__loss'] = loss
    sgd_params['clf__estimator__max_iter'] = max_iter
    sgd_params['clf__estimator__tol'] = tol
    sgd_params['clf__estimator__penalty'] = penalty
    sgd_params['clf__estimator__alpha'] = alpha
    sgd_params['clf__estimator__n_jobs'] = [n_jobs]
    return sgd_params

def NN():
    nn_params = {'clf__estimator': [MLPRegressor()]
                }

    st.subheader('Neural Network')
    solver = st.multiselect('Solver', ['lbfgs', 'sgd', 'adam'], ['adam'])
    max_iter = st.multiselect('Max Iterations', [1000,1100,1200,1300,1400], [1000])
    alpha = st.multiselect('Alpha', list(10.0 ** -np.arange(1, 10)), [0.0001])
    hidden_layer_sizes = st.multiselect('Hidden Layer Sizes', list(range(50, 500, 50)), [100])
#     hidden_layer_sizes = st.multiselect('Hidden Layer Sizes', [50, 100, 150, 200, 250, 300, 350, 400, 450, 500] , [100])

    nn_params['clf__estimator__solver'] = solver
    nn_params['clf__estimator__max_iter'] = max_iter
    nn_params['clf__estimator__alpha'] = alpha
    nn_params['clf__estimator__hidden_layer_sizes'] = hidden_layer_sizes
    return nn_params


data = st.file_uploader('Upload a csv')
test_data = st.file_uploader('Upload a csv for prediction:')

if (data != None) & (test_data != None):
    df = pd.read_csv(data)
    df_test = pd.read_csv(test_data)
    target_col =st.selectbox('Choose target variable', df.columns)
    X = df.drop(target_col, axis = 1)
    y = df[target_col]
    test_ratio = st.number_input('Enter test split ratio, 0 < ratio < 1', min_value = 0.0,
                                 max_value = 1.0, value = 0.2)

    if test_ratio:
        X_train_full, X_valid_full, y_train, y_valid = train_test_split(X, y,
                                                                        test_size=test_ratio,
                                                                        random_state = 0)

        rf_col_selection = st.sidebar.selectbox(
                              'Random Forest Column Selection', [True, False], 1)

        corr_col_selection = st.sidebar.selectbox(
                              'Correlation Column Selection', [True, False], 1)

        pairwise_linear = st.sidebar.selectbox(
                              'Pairwise Linear', [True, False], 1)

        pairwise_product = st.sidebar.selectbox(
                              'Pairwise Product', [True, False], 1)

        polynomial_features = st.sidebar.selectbox(
                              'Polynomial Features', [True, False], 1)

        interaction_only = st.sidebar.selectbox(
                              'Interaction Only', [True, False], 1)

        pca_on = st.sidebar.selectbox(
                              'Principal Component Analysis', [True, False], 1)

        label_enc = st.sidebar.selectbox(
                              'Label Encoding', [True, False], 1)


        selected_models = st.sidebar.multiselect(
                              'Choose Algorithms:',(
                                  'Gaussian NB',
                                  'Linear Regression',
                                  'Logistic Regression',
                                  'KNN',
                                  'Support Vector Machines',
                                  'Decision Tree',
                                  'Random Forest',
                                  'Gradient Boosting',
                                  'Extra Random Trees',
                                  'XGBoost',
                                  'Stochastic Gradient Descent',
                                  'Neural Network'), ['KNN', 'Support Vector Machines', 'Decision Tree'])

        if selected_models:
            func_dict = {'Gaussian NB': GNB(),
                         'Linear Regression': LinearReg(),
                         'Logistic Regression':LogisticReg(),
                          'KNN': KNN(),
                          'Support Vector Machines': SVM(),
                          'Decision Tree': DT(),
                          'Random Forest': RF(),
                          'Gradient Boosting': GB(),
                          'Extra Random Trees': ERT(),
                          'XGBoost': XGB(),
                          'Stochastic Gradient Descent': SGD(),
                          'Neural Network': NN()
                        }


            param_dict = {}

            for i in selected_models:
                param_dict[i] = func_dict[i]


            from sklearn.base import BaseEstimator, RegressorMixin

            class MyRegressor(BaseEstimator, RegressorMixin):

                def __init__(
                    self,
                    estimator = XGBRegressor(),
                ):
                    """
                    A Custom BaseEstimator that can switch between Regressor.
                    :param estimator: sklearn object - The Regressor
                    """

                    self.estimator = estimator


                def fit(self, X, y=None, **kwargs):
                    self.estimator.fit(X, y)
                    return self


                def predict(self, X, y=None):
                    return self.estimator.predict(X)


                def predict_proba(self, X):
                    return self.estimator.predict_proba(X)


                def score(self, X, y):
                    return self.estimator.score(X, y)

                @property
                def classes_(self):
                    return self.estimator.classes_



            X_train, X_valid, df_test, col = final_preprocessor(X_train_full,
                                                                y_train,
                                                                X_valid_full,
                                                                df_test,
                                                                rf_col_selection=rf_col_selection,
                                                                rf_no_of_cols=20,
                                                                rf_n_estimators=100,
                                                                corr_col_selection=corr_col_selection,
                                                                corr_threshold=0.2,
                                                                pairwise_linear=pairwise_linear,
                                                                pairwise_product=pairwise_product,
                                                                cardinality=100,
                                                                polynomial_features=polynomial_features,
                                                                interaction_only=interaction_only,
                                                                pca_on=pca_on,
                                                                label_enc=label_enc
                                                               )

            data_valid = pd.concat([X_valid, y_valid.reset_index(drop=True)], axis = 1)

            st.write(X_train.shape)

            my_pipeline = Pipeline([('scaler', scaler(scaling_scheme='power_transformer')),
                        ('clf', MyRegressor())
                       ])

            parameters = []

            for i in selected_models:
                parameters.append(param_dict[i])
            st.write(parameters)
            train = st.button('Train Model')
            if train:
                with st.spinner('Training Model...'):
                    from sklearn.model_selection import GridSearchCV
                    gscv = GridSearchCV(my_pipeline, parameters, cv=3, n_jobs=-1, return_train_score=False, verbose=3)
                    gscv.fit(X_train, y_train)
                    st.text('Best Parameters')
                    st.write(gscv.best_params_)


                    st.text('Best Score')
                    st.write(gscv.best_score_)


                    st.text('Validation Score')
                    st.write(gscv.score(X_valid, y_valid))


                    st.text('Fit vs Time vs HyperParameters')
                    data = gscv.cv_results_.values()
                    columns = gscv.cv_results_.keys()
                    df_fit = pd.DataFrame(data, columns).T
                    df_fit['param_clf__estimator'] = df_fit['param_clf__estimator'].apply(convert_str)
                    st.write(df_fit)


                    st.text('Prediction on Validation Data')
                    data_valid['Predicted'] = gscv.predict(X_valid)
                    st.write(data_valid)
                    st.text('Performance Metrics')
                    st.write(combined_metrics(X_valid, y_valid, gscv))


                    st.text('Scatter Plot: Actual vs Predicted')
                    #Scatter Plot of Actual vs Predicted
                    fig, ax = plt.subplots(figsize=(20, 10))
                    sns.regplot(x=y_valid,
                                y=gscv.predict(X_valid),
                                scatter_kws={"color":"green"},
                                line_kws={"color": "orange"},
                                ax=ax,
                                marker='.')
                    ax.set_ylabel('Actual Values')
                    ax.set_xlabel('Predicted Values')
                    st.pyplot(fig)


                    st.text('Error Distribution Plot')
                    #Error Distribution Plot
                    error = gscv.predict(X_valid) - y_valid
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.histplot(data=error, bins=40)
                    st.pyplot(fig)

                    st.text('Partial Dependence Plot')
                    features = [0, 1, (0, 1)]
                    fig, ax = plt.subplots(1,3, figsize = (15,9))
                    plot_partial_dependence(gscv,X_valid, features=features, ax=ax)
                    plt.tight_layout()
                    st.pyplot(fig)

                    st.text('ICE Plot')
                    features = [0, 1]
                    fig, ax = plt.subplots(figsize=(14, 12))
                    plot_partial_dependence(gscv, X_valid, features, kind='both', ax=ax)
                    plt.tight_layout()
                    st.pyplot(fig)

                    st.text('Prediction on Test file')
                    df_test['Predicted'] = gscv.predict(df_test)
                    st.write(df_test)

                    st.text('Shapley Explainer')
#                     X_test = df_test.drop('Predicted', axis = 1)
                    explainer = shap.KernelExplainer(gscv.predict, X_valid)
                    shap_values = explainer.shap_values(X_valid.iloc[2,:])
                    st.pyplot(shap.force_plot(explainer.expected_value, shap_values, X_valid.iloc[2,:], matplotlib=True, text_rotation=8))

                    st.text('Shapley Explainer WaterFall Plot')
                    f = lambda x: gscv.predict(x)
                    med = X_train.median().values.reshape(1,X_valid.shape[1])

                    explainer = shap.Explainer(f, med)
                    shap_values = explainer(X_valid.iloc[0:100,:])
                    st.pyplot(shap.plots.waterfall(shap_values[0], max_display=7))

                    st.text('Partial Dependence Plot from pdp_box')
                    pdp_ = pdp.pdp_isolate(model=gscv, dataset=X_valid,
                                                model_features=X_valid.columns,
                                                feature=X_valid.columns[0])

                    fig, axes = pdp.pdp_plot(pdp_isolate_out=pdp_, feature_name=X_valid.columns[0], center = True, ncols=1, figsize = (15, 10))
                    st.pyplot(fig)