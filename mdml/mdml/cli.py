# -*- coding: utf-8 -*-
"""
Command Line Interface
----------------------
A basic interface for MDML scripts.

@author: Benjamin Shields 
@email: benjamin.shields@bms.com
"""

############################################################################## Imports

import logging
import pandas as pd
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pandas.core.frame import DataFrame

############################################################################## Logger

logger = logging.getLogger(__name__)

############################################################################## Interface

def parser(description:str, add_computation:bool=False, **kwargs) -> (ArgumentParser, dict):
    """
    Generate a formatted argparse parser.

    Parameters
    ----------
    description : str
        CLI description.
    add_computation : bool, optional
        Add a computation parameters group including nproc. The default is True.
    **kwargs
        Keyword arguments passed to argparse.ArgumentParser.

    Returns
    -------
    parser : ArgumentParser
        Argument parser.
    groups : dict
        Pre-generated argument groups.
    """
    
    # Formatted parser
    class ArgparseFormatter(ArgumentDefaultsHelpFormatter):
        pass
    
    parser = ArgumentParser(    
        description=description,
        add_help=False,
        formatter_class=lambda prog: ArgparseFormatter(prog, width=98),
        **kwargs
    )
    groups = {}
    
    # Help
    helper = parser.add_argument_group('HELP')
    helper.add_argument(
        '-h',
        action='help',
        help="""Show this help message and exit."""
    )
    helper.add_argument(
        '-debug',
        action='store_true',
        dest='debug',
        help="""Print debugging messages."""
    )
    groups['help'] = helper
    
    # Resource Management
    if add_computation:
        comp = parser.add_argument_group('COMPUTATION')
        comp.add_argument(
            '-nproc',
            action='store',
            dest='nproc',
            type=int,
            default=1,
            help="""Number of processors to use for parallel computation."""
        )
        groups['computation'] = comp
    
    return parser, groups

############################################################################## Data

def aggregate_data(data:DataFrame, id_col:str, method:str) -> DataFrame:
    """
    Aggregate SimFPs by computing the mean, min, or max of duplicate MD runs.

    Parameters
    ----------
    features : DataFrame
        Feature matrix including duplicate SimFPs.
    id_col : str
        Molecule ID column. This column is used to identify duplicate SimFPs.
    method : str
        Aggregation method. The options are 'mean', 'min', and 'max'.

    Raises
    ------
    ValueError
        The specified method is not supported.

    Returns
    -------
    data : DataFrame
        Aggregated features.
    """
    
    if method == 'min':
        data = data.groupby(id_col).min()
    elif method == 'max':
        data = data.groupby(id_col).max()
    elif method == 'mean':
        data = data.groupby(id_col).mean()
    else:
        raise ValueError(f'Grouping method {method} not recognized.')
    
    data.insert(0, 'ID', data.index.values)
    
    return data.reset_index(drop=True)

def load_data(path:str, id_col:str, drop:bool=None, aggregation:str=None) -> DataFrame:
    """
    Load SimFP and target data and preprocess it by aggregating SimFPs from 
    duplicate MD runs.
    
    Note
    ----
    Rows containing SimFPs from duplicate MD runs should all of the same ID and
    target value. Any columns not corresponding to ID, features, or target 
    should be removed via the drop argument.

    Parameters
    ----------
    path : str
        Path to input CSV file.
    id_col : str, optional
       Column header containing unique molecule IDs.
    drop : bool, optional
        Remove . The default is None.
    aggregation : str, optional
        Type of aggregation to use. The options are None, 'mean', 'min', and 
        'max'. The default is None.

    Raises
    ------
    ValueError
        An ID column is required for aggregation.

    Returns
    -------
    data : DataFrame
        Loaded and preprocessed data.
    """
    
    data = pd.read_csv(path)
    if drop is not None and len(drop) > 0:
        data = data.drop(drop, axis=1) 
    if aggregation is None:
        if id_col != 'ID':
            data.insert(0, 'ID', data[id_col].values)
            data = data.drop(id_col, axis=1)
    else:
        if id_col is None:
            raise ValueError('An ID column is required for aggregation.')
        data = aggregate_data(data, id_col, aggregation)
        
    return data

def save_json(data:dict, path:str) -> None:
    """
    Save a dictionary as a JSON file.

    Parameters
    ----------
    data : dict
        Dictionary to be saved.
    path : str
        Path to JSON file.

    Returns
    -------
    None
    """
    
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    
def load_json(path:str) -> dict:
    """
    Load a JSON file as a dictionary.

    Parameters
    ----------
    path : str
        Path to JSON file.

    Returns
    -------
    dict
        Loaded data.
    """
    
    with open(path) as file:
        data = json.load(file)
        
    return data
        





    