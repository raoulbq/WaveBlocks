"""The WaveBlocks Project

Test the complex phase plot function.

@author: R. Bourquin
@copyright: Copyright (C) 2010, 2011 R. Bourquin
@license: Modified BSD License
"""

import numpy as np
from matplotlib.pyplot import *

from WaveBlocks.Plot import stemcf

x = np.r_[0.0:2.0*np.pi:1j*2**6]
u = np.exp( -1.0j * x )

rvals = np.real(u)
ivals = np.imag(u)
cvals = np.conjugate(u)*u
angles = np.angle(u)

figure(figsize=(20,20))

subplot(2,2,1)
stemcf(x, angles, rvals)
xlabel(r"$\Re \psi$")

subplot(2,2,2)
stemcf(x, angles, ivals, color="k")
xlabel(r"$\Im \psi$")

subplot(2,2,3)
stemcf(x, angles, cvals)
xlabel(r"$|\psi|^2$")

savefig("phaseplot.png")

show()
