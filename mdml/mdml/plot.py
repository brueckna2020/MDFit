# -*- coding: utf-8 -*-
"""
Plotting Methods
----------------
Generate basic plots for MDML analysis.

@author: Benjamin Shields 
@email: benjamin.shields@bms.com 
"""

############################################################################## Imports

import logging
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

############################################################################## Logger

logger = logging.getLogger(__name__)

############################################################################## Functions

def parity_plot(pred:list, obs:list, title:str='Fit', export_path:str=None, 
                xlabel:str='Predicted', ylabel:str='Observed', 
                color:str='black', cod:str='R^2') -> (float, float):
    """
    Plot predicted versus observed and return the RMSE and coefficient of
    determination.

    Parameters
    ----------
    pred : list
        Predicted values
    obs : list
        Observed values.
    title : str, optional
        Plot title. The default is 'Fit'.
    export_path : str, optional
        Path to export SVG. Images are exported as export_path.svg. The default 
        is None.
    xlabel : str, optional
        Label for x-axis. The default is 'Predicted'.
    ylabel : str, optional
        Label for y-axis. The default is 'Observed'.
    color : str, optional
        Color of plot points and error bars. The default is 'black'.
    cod : str, optional
        Nominclature used for the computed coefficient of determination. If the
        results are from cross-validation use 'Q^2'. The default is 'R^2'.

    Returns
    -------
    rmse : float
        Root mean squared error for predicted values.
    r2 : float
        Coefficient of determination for predicted values.
    """
    
    plt.set_loglevel("info")
    
    # Compute RMSE and R^2 values
    pred = np.array(pred)
    obs = np.array(obs)
    rmse = np.sqrt(np.mean((pred - obs) ** 2))
    r2 = r2_score(obs, pred)
    
    # Get upper and lower bounds of plot
    upper = max([max(pred), max(obs)])
    lower = min([min(pred), min(obs)])
    pad = (upper - lower) * 0.05
    
    # Plot
    plt.figure(figsize=(6,6))
    plt.scatter(pred, obs, color=color, alpha=0.4)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title('{0}($RMSE={1}$, ${2}={3}$)'.format(
        title, 
        round(float(rmse),2), 
        cod,
        round(r2,2))
    )
    plt.plot([lower,upper], [lower,upper], 'k-', alpha=0.75, zorder=0)
    plt.xlim(lower - pad, upper + pad)
    plt.ylim(lower - pad, upper + pad)
    
    # Save and/or show
    if export_path is not None:
        plt.savefig(export_path + '.svg', format='svg', dpi=1200, bbox_inches='tight')
        plt.close()
    else:
        plt.show() 
        
    return rmse, r2


