# -*- coding: utf-8 -*-
"""
Base Classes
------------
Helpful base classes for development.

@author: Benjamin Shields 
@email: benjamin.shields@bms.com
"""

############################################################################## Imports

import logging
import dill

############################################################################## Logger

logger = logging.getLogger(__name__)

############################################################################## Methods 

class Savable:
    """
    The Savable class implements general methods for saving and loading class
    objects. The __save__ method will save the state dictionary (__dict__) or
    any key/value pair as a pickled dictionary. The __load__ method will load
    and automatically name an entire pickled dictionary or any individual key
    value pair. In addition, __load__ will load non-dictionary pickled objects
    into a specified attribute.
    """
    
    def __save__(self, path:str, attrname:[str,list]=None) -> None:
        """
        Save the state dictionary or an individual attribute as a key/value 
        pair. If attrname is None then the entire state dictionary is saved.

        Parameters
        ----------
        path : str
            Path to save attribute. Data will be saved as a pickle file using
            dill.
        attrname : str, list, optional
            Name of attribute. The default is None. If None, the entire state 
            dictionary will be saved.
        """
        
        if isinstance(attrname, str):
            assert hasattr(self, attrname)
            savedict = {attrname: getattr(self, attrname)}
        elif isinstance(attrname, list):
            savedict = {}
            for name in attrname:
                assert hasattr(self, name)
                savedict[name] = getattr(self, name)
        else:
            savedict = self.__dict__
        with open(path, 'wb') as file:
            dill.dump(savedict, file)    

    def __load__(self, path:str, attrname:[str, list]=None) -> None:
        """
        Load saved objects to attributes based on dictionary key/value pairs,
        load an individual element from a pickled dictionary, or load objects 
        to a specified attribute.

        Parameters
        ----------
        path : str
            Path to pickled object file. For example a scikit-learn model.
        attrname : str, list, optional
            Name of attribute when loaded. For example 'model'. If attrname is
            None or not present in the loaded dict, all key/value pairs will be
            loaded.
        """
        
        # Load pickle file
        with open(path, 'rb') as file:
            loaded = dill.load(file)
        
        # Make sure it is a dict
        if not isinstance(loaded, dict):
            loaded = {attrname: loaded}
        
        # Load specific attributes
        if isinstance(attrname, str):
            attrname = [attrname]
        if isinstance(attrname, list):
            for name in attrname:
                attr = loaded.get(name)
                if attr is not None:
                    setattr(self, name, attr)
        
        # Load full dict
        else:
            self.__dict__.update(loaded) 



