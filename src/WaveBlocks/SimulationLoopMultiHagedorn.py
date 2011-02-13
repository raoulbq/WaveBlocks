"""The WaveBlocks Project

This file contains the main simulation loop
for the inhomogeneous Hagedorn propagator.

@author: R. Bourquin
@copyright: Copyright (C) 2010, 2011 R. Bourquin
@license: Modified BSD License
"""

import numpy as np
import scipy as sp

from PotentialFactory import PotentialFactory as PF
from HagedornMultiWavepacket import HagedornMultiWavepacket
from HagedornMultiPropagator import HagedornMultiPropagator
from SimulationLoop import SimulationLoop
from IOManager import IOManager


class SimulationLoopMultiHagedorn(SimulationLoop):
    """This class acts as the main simulation loop. It owns a propagator that
    propagates a set of initial values during a time evolution. All values are
    read from the I{Parameters.py} file."""

    def __init__(self, parameters):
        """Create a new simulation loop instance."""
        # Keep a reference to the simulation parameters
        self.parameters = parameters
        
        #: The time propagator instance driving the simulation.
        self.propagator = None
        
        #: A I{IOManager} instance for saving simulation results.
        self.IOManager = None

        #: The number of time steps we will perform.
        self.nsteps = parameters.nsteps
        
        # Set up serializing of simulation data
        self.IOManager = IOManager()
        self.IOManager.create_file(self.parameters)
        

    def prepare_simulation(self):
        """Set up a multi Hagedorn propagator for the simulation loop. Set the
        potential and initial values according to the configuration.
        @raise ValueError: For invalid or missing input data.
        """
        potential = PF.create_potential(self.parameters)
        N = potential.get_number_components()
        
        # Check for enough initial values
        if len(self.parameters.parameters) < N:
            raise ValueError("Too few initial states given. Parameters are missing.")
            
        if len(self.parameters.coefficients) < N:
            raise ValueError("Too few initial states given. Coefficients are missing.")
        
        # Create a suitable wave packet
        packet = HagedornMultiWavepacket(self.parameters)
        packet.set_quadrator(None)

        # Set the parameters for each energy level
        for index, item in enumerate(self.parameters.parameters):
            packet.set_parameters(item, index)

        # Set the initial values
        for component, data in enumerate(self.parameters.coefficients):
            for index, value in data:
                packet.set_coefficient(component, index, value)

        # Project the initial values to the canonical base
        packet.project_to_canonical(potential)

        # Finally create and initialize the propagator instace
        self.propagator = HagedornMultiPropagator(potential, packet, self.parameters)

        # Which data do we want to save
        tm = self.parameters.get_timemanager()
        slots = tm.compute_number_saves()

        self.IOManager.add_grid(self.parameters)
        self.IOManager.add_wavepacket_inhomog(self.parameters, timeslots=slots)
      
        # Write some initial values to disk
        nodes = self.parameters.f * sp.pi * sp.arange(-1, 1, 2.0/self.parameters.ngn, dtype=np.complexfloating)
        # self.nodes = nodes
        self.IOManager.save_grid(nodes)
        self.IOManager.save_coefficients_inhomog(self.propagator.get_wavepacket().get_coefficients(), timestep=0)
        self.IOManager.save_parameters_inhomog(self.propagator.get_wavepacket().get_parameters(), timestep=0)
        

    def run_simulation(self):
        """Run the simulation loop for a number of time steps. The number of steps
        is calculated in the I{initialize} function."""
        tm = self.parameters.get_timemanager()
        
        # Run the simulation for a given number of timesteps
        for i in xrange(1, self.nsteps+1):
            print(" doing timestep "+str(i))

            self.propagator.propagate()

            # Save some simulation data
            if tm.must_save(i):
                self.IOManager.save_coefficients_inhomog(self.propagator.get_wavepacket().get_coefficients(), timestep=i)
                self.IOManager.save_parameters_inhomog(self.propagator.get_wavepacket().get_parameters(), timestep=i)

            # vals = self.propagator.get_wavepacket().evaluate_at(self.nodes, prefactor=True)

            # from pylab import *
            # figure()
            # plot(self.nodes, conj(vals[0])*vals[0])
            # plot(self.nodes, conj(vals[1])*vals[1])
            # show()


    def end_simulation(self):
        """Do the necessary cleanup after a simulation. For example request the
        IOManager to write the data and close the output files.
        """
        self.IOManager.finalize()
