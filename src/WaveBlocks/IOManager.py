"""The WaveBlocks Project

This file contains code for serializing simulation data.

@author: R. Bourquin
@copyright: Copyright (C) 2010, 2011 R. Bourquin
@license: Modified BSD License
"""

import os
import sys
import types
import h5py as hdf
import pickle
import numpy as np

import GlobalDefaults
import ParameterProvider as ParameterProvider


class IOManager:
    """An IOManager class that can save various simulation results into data
    files. The output files can be processed further for producing e.g. plots.
    """

    def __init__(self):
        self.parameters = None
        self.srf = None


    def __getattr__(self, key):
        """Try to load a plugin if a member function is not available.
        """
        print("Requested function: "+key)

        # Plugin name convention
        name = "IOM_plugin_" + key.split("_")[1]

        # Load the necessary plugin
        print("Plugin to load: "+name)
        try:
            plugin = __import__(name)
        except ImportError:
            raise ImportError("IOM plugin '"+name+"' not found!")

        # Filter out functions we want to add to IOM and
        # bind the methods to the current IOM instance
        for k, v in plugin.__dict__.iteritems():
            if type(v) == types.FunctionType:
                self.__dict__[k] = types.MethodType(v, self)
        
        # Now return the new function to complete it's call
        return self.__dict__[key]
    
    
    def create_file(self, parameters, filename=GlobalDefaults.file_resultdatafile):
        """Set up a new I{IOManager} instance. The output files are created and opened.
        """
        #: Keep a reference to the parameters
        self.parameters = parameters

        # Create the file if it does not yet exist.
        # Otherwise raise an exception and avoid overwriting data.
        if os.path.lexists(filename):
            raise ValueError("Output file already exists!")        
        else:
            f = self.srf = hdf.File(filename)
            f.attrs["number_blocks"] = 0

        # Save the simulation parameters
        self.save_simulation_parameters(parameters)

        # Build up the hdf data tree, by default we provide one data block
        self.create_block()


    def load_file(self, filename=GlobalDefaults.file_resultdatafile):
        """Load a given file that contains the results from a former simulation.
        @keyword filename: The filename/path of the file we try to load.
        """
        if os.path.lexists(filename):
            self.srf = hdf.File(filename)
        else:
            raise ValueError("Output file does not exist!")

        # Load the simulation parameters
        self.parameters = ParameterProvider.ParameterProvider()
        p = self.srf["/simulation_parameters/parameters"].attrs

        for key, value in p.iteritems():
            self.parameters[key] = pickle.loads(value)

        # Compute some values on top of the given input parameters
        self.parameters.compute_parameters()


    def finalize(self):
        """Close the open output files."""
        self.srf.close()             


    def create_block(self):
        # Create a data block. Each data block can store several chunks
        # of information, and there may be multiple blocks per file.
        number_blocks = self.srf.attrs["number_blocks"]
        self.srf.create_group("datablock_" + str(number_blocks))
        self.srf.attrs["number_blocks"] += 1


    def save_simulation_parameters(self, parameters):
        # Store the simulation parameters
        grp_pa = self.srf.create_group("simulation_parameters")
        # We are only interested in the attributes of this data set
        # as they are used to store the simulation parameters.
        paset = grp_pa.create_dataset("parameters", (1,1))

        for param, value in parameters:
            # Store all the values as pickled strings because hdf can
            # only store strings or ndarrays as attributes.
            paset.attrs[param] = pickle.dumps(value)

    
    def get_parameters(self):
        """Return the reference to the current I{ParameterProvider} instance.
        """
        return self.parameters
    
    
    def must_resize(self, path, slot, axis=0):
        """Check if we must resize a given dataset and if yes, resize it.
        """
        # Ok, it's inefficient but sufficient for now.
        # todo: Consider resizing in bigger chunks and shrinking at the end if necessary.
        
        # Current size of the array
        cur_len = self.srf[path].shape[axis]

        # Is it smaller than what we need to store at slot "slot"?
        # If yes, then resize the array along the given axis.
        if cur_len-1 < slot:
            self.srf[path].resize(slot+1, axis=axis)
    
    
    def find_timestep_index(self, timegridpath, timestep):
        """Lookup the index for a given timestep.
        @note: Assumes the timegrid array is strictly monotone.
        """
        # todo: Make this more efficient
        # todo: allow for slicing etc
        timegrid = self.srf[timegridpath]
        index = np.squeeze(np.where(timegrid[:] == timestep))

        if index.shape == (0,):
            raise ValueError("No data for given timestep!")
        
        return index
