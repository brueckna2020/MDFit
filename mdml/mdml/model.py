# -*- coding: utf-8 -*-
"""
Modeling
--------
Implementations of an interpretable model base class, training, hyperparameter
optimization, and cross-validation methods.

@author: Benjamin Shields 
@email: benjamin.shields@bms.com
"""

############################################################################## Imports

import logging
from abc import ABCMeta, abstractmethod
import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series
import numpy as np
from numpy import ndarray
from sklearn.model_selection import LeaveOneOut, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn import metrics
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from tqdm import tqdm

from mdml import base

############################################################################## Logger

logger = logging.getLogger(__name__)

############################################################################## Methods

def train_model(model:object, search_params:dict, X:ndarray, y:ndarray, 
                cv:int=-1, n_jobs:int=1, **kwargs) -> (object, dict):
    """
    Optimize regression model parameters using grid search cross-validation and 
    return the trained model and optimal parameters.

    Parameters
    ----------
    model : object
        Instantiated scikit-learn model.
    search_params : dict
        Dictionary of parameters to be used in the grid search.
    X : ndarray
        Feature matrix.
    y : ndarray
        Possibly scaled target values.
    cv : int, optional
        Number of folds to use for cross-validation. A -1 indicates leave-one-
        out cross-validation. The default is -1.
    n_jobs : int, optional
        Number of parallel threads to use for optimization. The default is 1.
    **kwargs : dict
        Additional keyword arguments are passed to the GridSearchCV object.

    Returns
    -------
    model : object
        Scikit-learn model trained using the optimal paramters identified via
        grid search.
    best_params : dict
        Parameters identified by minimizing negative mean squared error via
        grid search cross-validation.
    """
    
    if cv == -1:
        cv = len(X)
    if search_params is None:
        best_params = {}
        model.fit(X, y)
    else:
        grid_search = GridSearchCV(
            model, [search_params], cv=cv, refit=True, n_jobs=n_jobs,
            scoring='neg_mean_squared_error', **kwargs
        )
        grid_search.fit(X, y)    
        best_params = grid_search.best_params_
        model = grid_search.best_estimator_
        
    return model, best_params

def cross_validation(model:object, X:ndarray, y:ndarray, search_params:dict, 
                     ids:ndarray=None, importance:object=None, 
                     features:ndarray=None, cv:int=-1, n_jobs:int=1, 
                     scale:bool=True, desc:str='CV', **kwargs) -> dict:
    """
    Carry out (possibly nested) random cross-validation and keep track of 
    predictions and feature importance in each fold.
    
    Note
    ----
    Specifying search_params will enable nested cross-validation. Otherwise the
    hyperparameters specified in the instantiated model will be used for all 
    folds.

    Parameters
    ----------
    model : object
        Instantiated scikit-learn model.
    X : ndarray
        Feature matrix.
    y : ndarray
        Target values.
    search_params : dict
        Dictionary of parameters to be used in the grid search.
    ids : ndarray, optional
        Molecule ID values corresponding to each row in X. The default is None.
    importance : object, optional
        Static method used for computing feature importance. The default is 
        None.
    features : ndarray, optional
        Names of features corresponding to columns in X. The default is None.
    cv : int, optional
        Number of folds to use for cross-validation. A -1 indicates leave-one-
        out cross-validation. The default is -1.
    n_jobs : int, optional
        Number of parallel threads to use for optimization. The default is 1.
    scale : bool, optional
        Scale input features in each fold to zero mean and unit variance. The 
        default is True.
    desc : str, optional
        Discription shown on progress bar which displays number of completed
        CV folds. The default is 'CV'.
    **kwargs : dict
        Additional keyword arguments are passed to the train_model method.

    Returns
    -------
    dict
        A dictionary containing fold predictions, observed values, molecule IDs
        and feature importances. In addition the coefficient of determination
        and MSE are included.
    """
    
    results = {'pred':[], 'obs':[], 'ids':[]}
    if importance is not None and features is not None:
        results['imp'] = {name:[] for name in features}
    for train_index, test_index in tqdm(LeaveOneOut().split(X), desc=desc, total=len(X)):
        # Preprocess
        if scale:
            target_scaler = StandardScaler()
            y_train = y[train_index].reshape(len(train_index), 1)
            y_train = target_scaler.fit_transform(y_train).flatten()
            feature_scaler = MinMaxScaler()
            X_train = feature_scaler.fit_transform(X[train_index])
        else:
            y_train = y[train_index]
            X_train = X[train_index]
        # Train
        model, best_params = train_model(
            model, search_params, X_train, y_train, cv=cv, 
            n_jobs=n_jobs, **kwargs
        )
        # Predict
        if scale:
            predk = model.predict(feature_scaler.transform(X[test_index]))
            predk = target_scaler.inverse_transform(predk.reshape(len(predk), 1)).flatten()
        else:
            predk = model.predict(X[test_index])
        # Save results
        results['pred'] += predk.tolist()
        results['obs'] += y[test_index].tolist()
        results['ids'] += ids[test_index].tolist()
        if importance is not None and features is not None:
            imp = importance(model, features).to_dict()
            for name in features:
                results['imp'][name].append(imp.get(name))
    results['Q^2'] = metrics.r2_score(results.get('obs'), results.get('pred'))
    results['MSE'] = metrics.mean_squared_error(results.get('obs'), results.get('pred'))

    return results

def _get_subset(array:np.ndarray, matches:list) -> np.ndarray:
    return np.argwhere([v in matches for v in array]).flatten()

def molecule_cross_validation(model:object, X:ndarray, y:ndarray, search_params:dict, 
                              ids:ndarray=None, importance:object=None, features:ndarray=None, 
                              cv:int=-1, n_jobs:int=1, scale:bool=True, desc:str='Molecule CV', 
                              **kwargs) -> dict:
    """
    Carry out (possibly nested) molecule cross-validation and keep track of 
    predictions and feature importance in each fold.
    
    Note
    ----
    Specifying search_params will enable nested cross-validation. Otherwise the
    hyperparameters specified in the instantiated model will be used for all 
    folds.

    Parameters
    ----------
    model : object
        Instantiated scikit-learn model.
    X : ndarray
        Feature matrix.
    y : ndarray
        Target values.
    search_params : dict
        Dictionary of parameters to be used in the grid search.
    ids : ndarray, optional
        Molecule ID values corresponding to each row in X. The default is None.
    importance : object, optional
        Static method used for computing feature importance. The default is 
        None.
    features : ndarray, optional
        Names of features corresponding to columns in X. The default is None.
    cv : int, optional
        Number of folds to use for cross-validation. A -1 indicates leave-one-
        out cross-validation. The default is -1.
    n_jobs : int, optional
        Number of parallel threads to use for optimization. The default is 1.
    scale : bool, optional
        Scale input features in each fold to zero mean and unit variance. The 
        default is True.
    desc : str, optional
        Discription shown on progress bar which displays number of completed
        CV folds. The default is 'CV'.
    **kwargs : dict
        Additional keyword arguments are passed to the train_model method.

    Returns
    -------
    dict
        A dictionary containing fold predictions, observed values, molecule IDs
        and feature importances. In addition the coefficient of determination
        and MSE are included.
    """

    results = {'pred':[], 'obs':[], 'ids':[]}
    if importance is not None and features is not None:
        results['imp'] = {name:[] for name in features}
    unique_ids = np.array(list(set(ids)))
    for train_mol_index, test_mol_index in tqdm(LeaveOneOut().split(unique_ids), desc=desc, total=len(unique_ids)):
        train_index = _get_subset(ids, unique_ids[train_mol_index])
        test_index = _get_subset(ids, unique_ids[test_mol_index])
        # Preprocess
        if scale:
            target_scaler = StandardScaler()
            y_train = y[train_index].reshape(len(train_index), 1)
            y_train = target_scaler.fit_transform(y_train).flatten()
            feature_scaler = MinMaxScaler()
            X_train = feature_scaler.fit_transform(X[train_index])
        else:
            y_train = y[train_index]
            X_train = X[train_index]
        # Train
        model, best_params = train_model(
            model, search_params, X_train, y_train, cv=cv, 
            n_jobs=n_jobs, **kwargs
        )
        # Predict
        if scale:
            predk = model.predict(feature_scaler.transform(X[test_index]))
            predk = target_scaler.inverse_transform(predk.reshape(len(predk), 1)).flatten()
        else:
            predk = model.predict(X[test_index])
        # Save results
        results['pred'] += predk.tolist()
        results['obs'] += y[test_index].tolist()
        results['ids'] += ids[test_index].tolist()
        if importance is not None and features is not None:
            imp = importance(model, features).to_dict()
            for name in features:
                results['imp'][name].append(imp.get(name))
    results['Q^2'] = metrics.r2_score(results.get('obs'), results.get('pred'))
    results['MSE'] = metrics.mean_squared_error(results.get('obs'), results.get('pred'))

    return results

############################################################################## Base Workflow

class BaseWorkflow(base.Savable, metaclass=ABCMeta):
    """
    Base workflow for training Scikit-Learn models and estimating feature
    importance. This abstract base class requires the implementation of a 
    feature_importance method.
    """

    def __init__(self, base_model:object=None, data:DataFrame=None, target_col:str=None, 
                 id_col:str='ID', search_params:dict=None, scale:bool=True, **kwargs):
        """
        Parameters
        ----------
        base_model : object, optional
            Scikit-learn model. The default is None.
        data : DataFrame, optional
            A DataFrame with columns for features, molecule ID, and training target.
            The default is None.
        target_col : str, optional
            Training target column. The default is None.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        search_params : dict, optional
            Dictionary of parameters to be used in the grid search. The default is None.
        scale : bool, optional
            Scale input features in each fold to zero mean and unit variance. The 
            default is True.
        """

        # Loading
        if base_model is None:
            return None
        
        # Scaling
        data = data.copy()
        self.features = data.drop([target_col, id_col], axis=1).columns.values
        self.scale = scale
        if self.scale:
            self.target_scaler = StandardScaler()
            data[target_col] = self.target_scaler.fit_transform(
                data[[target_col]].values
            ).flatten()
            self.feature_scaler = MinMaxScaler()
            data[self.features] = self.feature_scaler.fit_transform(
                data[self.features].values
            )
        
        # Data
        self.X = data.drop([target_col, id_col], axis=1).values
        self.y = data[target_col].values
        self.target = target_col
        self.ids = data[id_col].values
        self.search_params = search_params
        
        # Model
        self.kwargs = kwargs
        self.base_model = base_model
        self.model = self._init_model()
        self.best_params = {}
    
    def _get_data(self, unstandardized:bool=False) -> (ndarray, ndarray):
        X = np.array(self.X)
        y = np.array(self.y)
        if unstandardized and self.scale:
            y = self.target_scaler.inverse_transform(
                y.reshape(len(y), 1)    
            ).flatten()
            X = self.feature_scaler.inverse_transform(X)
        return X, y
    
    def _init_model(self, **kwargs) -> object:
        params = {**self.kwargs, **kwargs}
        model = self.base_model(**params)
        return model
    
    def fit(self, n_jobs:int=1, cv:int=-1, **kwargs) -> None:
        """
        Train the model and optimize hyperparameters using grid search cross-validation.

        Parameters
        ----------
        n_jobs : int, optional
            Number of parallel threads to use for optimization. The default is 1.
        cv : int, optional
            Number of folds to use for cross-validation. A -1 indicates leave-one-
            out cross-validation. The default is -1.

        Returns
        -------
        None
        """

        self.model, self.best_params = train_model(
            self.model, self.search_params, self.X, self.y, cv=cv, 
            n_jobs=n_jobs, **kwargs
        )
        
    def predict(self, df:DataFrame) -> ndarray:
        """
        Make predictions using the trained model.

        Parameters
        ----------
        df : DataFrame
            A DataFrame containing columns for each of the model features.

        Returns
        -------
        ndarray
            Predicted values.
        """

        df = df.copy()
        if self.scale:
            df[self.features] = self.feature_scaler.transform(
                df[self.features].values
            )
        pred = self.model.predict(df[self.features])
        if self.scale:
            pred = pred.reshape(len(pred), 1)
            pred = self.target_scaler.inverse_transform(pred).flatten()
        
        return pred
    
    def cross_validate(self, cv_method:object=molecule_cross_validation, nested:bool=False, 
                       cv:int=-1, n_jobs:int=1, **kwargs) -> dict:
        """
        Carry out cross-validation and keep track of predictions and feature importance in 
        each fold.

        Parameters
        ----------
        cv_method : object, optional
            Cross validation method to be used. The default is molecule_cross_validation.
        nested : bool, optional
            Carry out nested cross-validation (optimize model hyperparameters in each fold).
            The default is False.
        cv : int, optional
            Number of folds to use for cross-validation. A -1 indicates leave-one-
            out cross-validation. The default is -1.
        n_jobs : int, optional
            Number of parallel threads to use for optimization. The default is 1.

        Returns
        -------
        dict
            A dictionary containing fold predictions, observed values, molecule IDs
            and feature importances. In addition the coefficient of determination
            and MSE are included.
        """

        model = self._init_model(**self.best_params)
        X, y = self._get_data(unstandardized=True)
        ids = np.array(self.ids)
        search_params = {}
        if nested:
            search_params = self.search_params
        results = cv_method(
            model, X, y, search_params, cv=cv, n_jobs=n_jobs, ids=ids,
            importance=self._feature_importance, features=self.features,
            **kwargs
        )

        return results
    
    @abstractmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        """
        Workflows require the implementation of this method. It should take a trained
        sklearn model and feature names and return a sorted Series with feature names 
        as the index.
        """

        pass

    @abstractmethod
    def feature_importance(self) -> Series:
        """
        Workflows require the implementation of this method. It should return a sorted
        Series with feature names as the index.
        """

        pass

def leave_one_feature_out_importance(workflow:BaseWorkflow, cv_method:object=cross_validation, 
                                     nested:bool=False, cv:int=-1, n_jobs:int=1, **kwargs) -> dict:
    """
    Evaluate feature importance by iteratievly removing each feature and evaluating model
    performance by (possibly nested) cross-validation.

    Parameters
    ----------
    workflow : BaseWorkflow
        Modeling workflow.
    cv_method : object, optional
        Cross validation method to be used. The default is cross_validation.
    nested : bool, optional
        Carry out nested cross-validation (optimize model hyperparameters in each fold).
        The default is False.
    cv : int, optional
        Number of folds to use for cross-validation. A -1 indicates leave-one-
        out cross-validation. The default is -1.
    n_jobs : int, optional
        Number of parallel threads to use for optimization. The default is 1.

    Returns
    -------
    dict
        A dictionary containing fold predictions, observed values, molecule IDs
        and feature importances, coefficient of determination, and MSE for 
        cross-validation experiments carried out with the corresponding feature
        removed.
    """

    X, y = workflow._get_data(unstandardized=True)
    search_params = {}
    if nested:
        search_params = workflow.search_params
    results = {}
    for i, name in enumerate(workflow.features):
        X_dropi = np.delete(X, i, 1)
        model = workflow._init_model(**workflow.best_params)
        features_dropi = np.delete(workflow.features, i, 0)
        results[name] = cv_method(
            model, X_dropi, y, search_params, ids=workflow.ids,
            importance=workflow._feature_importance, features=features_dropi,
            cv=cv, n_jobs=n_jobs, desc=name, **kwargs
        )
    
    return results
    
def load_workflow(path:str) -> BaseWorkflow:
    """
    Load a saved workflow for making predictions.

    Note
    ----
    This method is designed for loading workflows for making predictions.
    For other analysis load the workflow with the corresponding workflow
    class.

    Parameters
    ----------
    path : str
        Path to pickled workflow.

    Returns
    -------
    BaseWorkflow
        Loaded workflow.
    """

    # Loader class
    class PredictWorkflow(BaseWorkflow):
        def _feature_importance(self) -> None:
            return None
        def feature_importance(self) -> None:
            return None

    # Load worklfow
    workflow = PredictWorkflow()
    workflow.__load__(path)

    return workflow

############################################################################## Models

class LinearRegression(BaseWorkflow):
    """
    A linear regression workflow based on sklearn.linear_model.LinearRegression.
    """

    def __init__(self, data:DataFrame=None, target_col:str=None, id_col:str='ID', **kwargs):
        """
        Parameters
        ----------
        data : DataFrame
            A DataFrame with columns for features, molecule ID, and training target.
        target_col : str
            Training target column.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        """

        parameters = None
        super(LinearRegression, self).__init__(
            base_model=linear_model.LinearRegression, data=data, 
            target_col=target_col,id_col=id_col, search_params=parameters,
            **kwargs
        )
    
    @staticmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        return pd.Series(
            model.coef_, index=features, name='importance'
        ).sort_values(ascending=False)
    
    def feature_importance(self) -> Series:
        """
        Estimate feature importance via regression weights.

        Returns
        -------
        Series
            Sorted feature importance.
        """

        return self._feature_importance(self.model, self.features)

class RidgeRegression(BaseWorkflow):
    """
    A linear regression workflow based on sklearn.linear_model.Ridge.
    """

    def __init__(self, data:DataFrame=None, target_col:str=None, id_col:str='ID', **kwargs):
        """
        Parameters
        ----------
        data : DataFrame
            A DataFrame with columns for features, molecule ID, and training target.
        target_col : str
            Training target column.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        """

        parameters = {
            "alpha": np.logspace(-6,3,300)
        }
        super(RidgeRegression, self).__init__(
            base_model=linear_model.Ridge, data=data, 
            target_col=target_col,id_col=id_col, search_params=parameters,
            **kwargs
        )
    
    @staticmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        return pd.Series(
            model.coef_, index=features, name='importance'
        ).sort_values(ascending=False)
    
    def feature_importance(self) -> Series:
        """
        Estimate feature importance via regression weights.

        Returns
        -------
        Series
            Sorted feature importance.
        """

        return self._feature_importance(self.model, self.features)
        
class LassoRegression(BaseWorkflow):
    """
    A linear regression workflow based on sklearn.linear_model.Lasso.
    """

    def __init__(self, data:DataFrame, target_col:str=None, id_col:str='ID', **kwargs):
        """
        Parameters
        ----------
        data : DataFrame
            A DataFrame with columns for features, molecule ID, and training target.
        target_col : str
            Training target column.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        """

        parameters = {
            "alpha": np.linspace(1e-6,1,300)
        }
        super(LassoRegression, self).__init__(
            base_model=linear_model.Lasso, data=data, 
            target_col=target_col,id_col=id_col, search_params=parameters,
            **kwargs
        )
    
    @staticmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        return pd.Series(
            model.coef_, index=features, name='importance'
        ).sort_values(ascending=False)
    
    def feature_importance(self) -> Series:
        """
        Estimate feature importance via regression weights.

        Returns
        -------
        Series
            Sorted feature importance.
        """

        return self._feature_importance(self.model, self.features)

class RandomForestRegression(BaseWorkflow):
    """
    A random forest regression workflow based on sklearn.ensemble.RandomForestRegressor.
    """
    
    def __init__(self, data:DataFrame, target_col:str=None, id_col:str='ID', **kwargs):
        """
        Parameters
        ----------
        data : DataFrame
            A DataFrame with columns for features, molecule ID, and training target.
        target_col : str
            Training target column.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        """

        parameters = {
            "n_estimators": [200],
            "max_depth": [2,4,10,20,None],
            "min_samples_leaf": [1,2,3,6]
        }
        super(RandomForestRegression, self).__init__(
            base_model=RandomForestRegressor, data=data, 
            target_col=target_col,id_col=id_col, search_params=parameters,
            **kwargs
        )
    
    @staticmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        importance = pd.Series(
            model.feature_importances_, index=features, name='importance'
        )
        return importance.sort_values(ascending=False)
    
    def feature_importance(self) -> Series:
        """
        Estimate feature importance via node impurity (sklearn default).

        Returns
        -------
        Series
            Sorted feature importance.
        """

        return self._feature_importance(self.model, self.features)
    
class GradientBoostingRegression(BaseWorkflow):
    """
    A gradient boosting regression workflow based on sklearn.ensemble.GradientBoostingRegressor.
    """
    
    def __init__(self, data:DataFrame, target_col:str=None, id_col:str='ID', **kwargs):
        """
        Parameters
        ----------
        data : DataFrame
            A DataFrame with columns for features, molecule ID, and training target.
        target_col : str
            Training target column.
        id_col : str, optional
            Molecule ID column. The default is 'ID'.
        """

        parameters = {
            "n_estimators": [300],
            'learning_rate': [0.01, 0.05, 0.1],
            "max_depth": [1,2,3,5,10,None],
            "min_samples_leaf": [1,2,3]
        }
        super(GradientBoostingRegression, self).__init__(
            base_model=GradientBoostingRegressor, data=data, 
            target_col=target_col,id_col=id_col, search_params=parameters,
            **kwargs
        )
    
    @staticmethod
    def _feature_importance(model:object, features:ndarray) -> Series:
        importance = pd.Series(
            model.feature_importances_, index=features, name='importance'
        )
        return importance.sort_values(ascending=False)
    
    def feature_importance(self) -> Series:
        """
        Estimate feature importance via node impurity (sklearn default).

        Returns
        -------
        Series
            Sorted feature importance.
        """

        return self._feature_importance(self.model, self.features)



