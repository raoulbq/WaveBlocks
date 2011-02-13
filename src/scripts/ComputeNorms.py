"""The WaveBlocks Project

Calculate the norms of the different wave packets as well as the sum of all norms.

@author: R. Bourquin
@copyright: Copyright (C) 2010, 2011 R. Bourquin
@license: Modified BSD License
"""

import sys

from WaveBlocks import IOManager


if __name__ == "__main__":

    iom = IOManager()

    # Read file with simulation data
    try:
        iom.load_file(filename=sys.argv[1])
    except IndexError:
        iom.load_file()

    parameters = iom.get_parameters()

    if parameters.algorithm == "fourier":
        import NormWavefunction 
        NormWavefunction.compute_norm(iom)

    elif parameters.algorithm == "hagedorn":
        import NormWavepacket
        NormWavepacket.compute_norm(iom)

    elif parameters.algorithm == "multihagedorn":
        import NormWavepacketInhomog
        NormWavepacketInhomog.compute_norm(iom)

    else:
        raise ValueError("Unknown propagator algorithm.")
    
    iom.finalize()
