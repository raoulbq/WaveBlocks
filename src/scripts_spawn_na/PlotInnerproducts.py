"""The WaveBlocks Project

Plot some interesting values of the original and estimated
parameters sets Pi_m=(P,Q,S,p,q) and Pi_s=(B,A,S,b,a).
Plot the inner products of spawned and original packets.

@author: R. Bourquin
@copyright: Copyright (C) 2011 R. Bourquin
@license: Modified BSD License
"""

import sys
from numpy import real, imag, abs, angle
from matplotlib.pyplot import *

from WaveBlocks import ComplexMath
from WaveBlocks import IOManager
from WaveBlocks import TrapezoidalQR
from WaveBlocks import HagedornWavepacket


def read_data_spawn(fo, fs, assume_duplicate_mother=False):
    """
    @param f: An I{IOManager} instance providing the simulation data.
    @keyword assume_duplicate_mother: Parameter to tell the code to leave out
    every second data block and only take blocks [0, 1, 3, 5, 7, ...]. This
    is usefull because in aposteriori spawning we have to store clones of
    the mother packet.
    """
    parameters = fo.get_parameters()
    ndb = fo.get_number_blocks()

    timegrids = []
    AllPA = []

    AllC = []


    timegrids.append( parameters["dt"] * fo.load_wavepacket_timegrid(block=0) )

    Pi = fo.load_wavepacket_parameters(block=0)
    Phist = Pi[:,0]
    Qhist = Pi[:,1]
    Shist = Pi[:,2]
    phist = Pi[:,3]
    qhist = Pi[:,4]
    AllPA.append( [Phist, Qhist, Shist, phist, qhist] )

    Ci = fo.load_wavepacket_coefficients(block=0)
    AllC.append(Ci)


    timegrids.append( parameters["dt"] * fs.load_wavepacket_timegrid(block=1) )

    Pi = fs.load_wavepacket_parameters(block=1)
    Phist = Pi[:,0]
    Qhist = Pi[:,1]
    Shist = Pi[:,2]
    phist = Pi[:,3]
    qhist = Pi[:,4]
    AllPA.append( [Phist, Qhist, Shist, phist, qhist] )

    Ci = fs.load_wavepacket_coefficients(block=1)
    AllC.append(Ci)

    return parameters, timegrids, AllPA, AllC



def inner(parameters, P1, P2, QR=None):
    """Compute the inner product between two wavepackets.
    """
    # Quadrature for <orig, s1>
    c1 = P1.get_coefficients(component=0)
    c2 = P2.get_coefficients(component=0)

    # Assuming same quadrature rule for both packets
    # Implies same basis size!
    if QR is None:
        QR = P1.get_quadrator()

    # Mix the parameters for quadrature
    (Pm, Qm, Sm, pm, qm) = P1.get_parameters()
    (Ps, Qs, Ss, ps, qs) = P2.get_parameters()

    rm = Pm/Qm
    rs = Ps/Qs

    r = np.conj(rm)-rs
    s = np.conj(rm)*qm - rs*qs

    q0 = np.imag(s) / np.imag(r)
    Q0 = -0.5 * np.imag(r)
    QS = 1 / np.sqrt(Q0)

    # The quadrature nodes and weights
    nodes = q0 + parameters["eps"] * QS * QR.get_nodes()
    #nodes = QR.get_nodes()
    weights = QR.get_weights()

    # Basis sets for both packets
    basis_1 = P1.evaluate_base_at(nodes, prefactor=True)
    basis_2 = P2.evaluate_base_at(nodes, prefactor=True)

    R = QR.get_order()

    # Loop over all quadrature points
    tmp = 0.0j
    for r in xrange(R):
        tmp += np.conj(np.dot( c1[:,0], basis_1[:,r] )) * np.dot( c2[:,0], basis_2[:,r]) * weights[0,r]
    result = parameters["eps"] * QS * tmp

    return result


def compute(parameters, timegrids, AllPA, AllC):
    # Grid of mother and first spawned packet
    grid_m = timegrids[0]
    grid_s = timegrids[1]

    # Parameters of the original packet
    P, Q, S, p, q = AllPA[0]

    # Parameter of the spawned packet, first try
    B, A, S, b, a = AllPA[1]

    # Parameter of the spawned packet, second try
    A2, S2, b2, a2 = A, S, b, a
    B2 = -real(B)+1.0j*imag(B)

    C0 = AllC[0]
    C1 = AllC[1]

    # Construct the packets from the data
    OWP = HagedornWavepacket(parameters)
    OWP.set_quadrator(QR)

    S1WP = HagedornWavepacket(parameters)
    S1WP.set_quadrator(QR)

    S2WP = HagedornWavepacket(parameters)
    S2WP.set_quadrator(QR)

    nrtimesteps = grid_m.shape[0]

    ip_oo = []
    ip_os1 = []
    ip_os2 = []
    ip_s1s1 = []
    ip_s2s2 = []

    # Inner products
    for step in xrange(nrtimesteps):
        print(step)

        # Put the data from the current timestep into the packets
        OWP.set_parameters((P[step], Q[step], S[step], p[step], q[step]))
        OWP.set_coefficients(C0[step,...], component=0)

        S1WP.set_parameters((B[step], A[step], S[step], b[step], a[step]))
        S1WP.set_coefficients(C1[step,...], component=0)

        S2WP.set_parameters((B2[step], A2[step], S2[step], b2[step], a2[step]))
        S2WP.set_coefficients(C1[step,...], component=0)

        # Compute the inner products
        ip_oo.append( inner(parameters, OWP, OWP, QR=QR) )
        ip_os1.append( inner(parameters, OWP, S1WP, QR=QR) )
        ip_os2.append( inner(parameters, OWP, S2WP, QR=QR) )
        ip_s1s1.append( inner(parameters, S1WP, S1WP, QR=QR) )
        ip_s2s2.append( inner(parameters, S2WP, S2WP, QR=QR) )


    # Plot
    figure()
    plot(grid_m, abs(ip_oo), label=r"$\langle O|O\rangle $")
    plot(grid_m, abs(ip_os1), "-*", label=r"$\langle O|S1\rangle $")
    plot(grid_m, abs(ip_os2), "-d", label=r"$\langle O|S2\rangle $")
    plot(grid_m, abs(ip_s1s1), label=r"$\langle S1|S1\rangle $")
    plot(grid_m, abs(ip_s2s2), label=r"$\langle S2|S2\rangle $")
    legend()
    grid(True)
    savefig("inner_products.png")
    close()




if __name__ == "__main__":
    iom_s = IOManager()
    iom_o = IOManager()

    # NOTE
    #
    # first cmd-line data file is spawning data
    # second cmd-line data file is reference data

    # Read file with new simulation data
    try:
        iom_s.open_file(filename=sys.argv[1])
    except IndexError:
        iom_s.open_file()

    # Read file with original reference simulation data
    try:
        iom_o.open_file(filename=sys.argv[2])
    except IndexError:
        iom_o.open_file()

    compute(*read_data_spawn(iom_o, iom_s))

    iom_s.finalize()
    iom_o.finalize()
