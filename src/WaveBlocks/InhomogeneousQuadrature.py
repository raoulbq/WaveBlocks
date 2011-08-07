"""The WaveBlocks Project

This file contains code for the inhomogeneous (or mixing) quadrature of two
wave packets. The class defined here can compute brakets, inner products and
expectation values and compute the $F$ matrix.

@author: R. Bourquin
@copyright: Copyright (C) 2011 R. Bourquin
@license: Modified BSD License
"""

from numpy import zeros, complexfloating, sum, matrix, squeeze, imag, ones
from scipy import sqrt, exp, conj, dot

from Quadrature import Quadrature


class InhomogeneousQuadrature(Quadrature):

    def __init__(self, QR=None, order=None):
        if QR is not None:
            self.set_qr(QR)
        elif order is not None:
            self.build_qr(order)
        else:
            self.QR = None


    def __str__(self):
        return "Inhomogeneous quadrature using a " + str(self.QR)


    def transform_nodes(self, Pibra, Piket, eps, QR=None):
        """Transform the quadrature nodes such that they fit the given wavepacket.
        @param Pibra: The parameter set $Pi$ from the bra.
        @param Piket: The parameter set $Pi$ from the ket.
        @param eps: The epsilon of the wavepacket.
        @keyword QR: An optional quadrature rule providing the nodes.
        """
        if QR is None:
            QR = self.QR

        # Mix the parameters
        q0, QS = self.mix_parameters(Pibra, Piket)

        nodes = q0 + eps * QS * self.QR.get_nodes()
        return nodes.copy()


    def mix_parameters(self, Pibra, Piket):
        """Mix the two parameter sets $Pi_bra$ and $Pi_ket$ from the bra
        and the ket wavepacket.
        @param Pibra: The parameter set $Pi$ from the bra.
        @param Piket: The parameter set $Pi$ from the ket.
        @return: The mixed parameters $q0$ and $QS$. (See the theory for details.)
        """
        # <Pibra| ... | Piket>
        (Pr, Qr, Sr, pr, qr) = Pibra
        (Pc, Qc, Sc, pc, qc) = Piket

        # Mix the parameters
        rr = Pr/Qr
        rc = Pc/Qc

        r = conj(rr)-rc
        s = conj(rr)*qr - rc*qc

        q0 = imag(s) / imag(r)
        Q0 = -0.5 * imag(r)
        QS = 1 / sqrt(Q0)

        return (q0, QS)


    def quadrature(self, pacbra, packet, operator=None, summed=False, component=None):
        """Performs the quadrature of $\Braket{\Psi|f|\Psi}$ for a general $f$.
        @param pacbra: The wavepacket $<\Psi|$ from the bra with $Nbra$ components and basis size of $Kbra$.
        @param packet: The wavepacket $|\Psi>$ from the ket with $Nket$ components and basis size of $Kket$.
        @param operator: A real-valued function $f(x):R \rightarrow R^{Nbra \times Nket}$.
        @param summed: Whether to sum up the individual integrals $\Braket{\Phi_i|f_{i,j}|\Phi_j}$.
        @return: The value of $\Braket{\Psi|f|\Psi}$. This is either a scalar
        value or a list of $Nbra*Nket$ scalar elements.
        """
        # Should raise Exceptions if pacbra and packet are incompatible wrt N, K etc
        weights = self.QR.get_weights()

        # Packets can have different number of components
        Nbra = pacbra.get_number_components()
        Nket = packet.get_number_components()
        # Packets can also have different basis size
        Kbra = pacbra.get_basis_size()
        Kket = packet.get_basis_size()

        eps = packet.eps

        Pibra = pacbra.get_parameters(aslist=True)
        Piket = packet.get_parameters(aslist=True)

        coeffbra = pacbra.get_coefficients()
        coeffket = packet.get_coefficients()

        result = []

        # Operator is None is interpreted as identity transformation
        if operator is None:
            operator = lambda nodes, component=None: ones(nodes.shape) if component[0] == component[1] else zeros(nodes.shape)

        for row in xrange(Nbra):
            for col in xrange(Nket):
                Pimix = self.mix_parameters(Pibra[row], Piket[col])
                nodes = self.transform_nodes(Pibra[row], Piket[col], eps)
                # Operator should support the component notation for efficiency
                values = operator(nodes, component=(row,col))

                phase = exp(1.0j/eps**2 * (Piket[col][2]-conj(Pibra[row][2])))
                factor = squeeze(eps * values * weights * Pimix[1])

                M = zeros((Kbra,Kket), dtype=complexfloating)

                basisr = pacbra.evaluate_basis_at(nodes, component=row, prefactor=True)
                basisc = packet.evaluate_basis_at(nodes, component=col, prefactor=True)

                # Summing up matrices over all quadrature nodes
                for k in xrange(self.QR.get_number_nodes()):
                    tmpr = matrix(basisr[:,k])
                    tmpc = matrix(basisc[:,k])
                    M += factor[k] * tmpr.H * tmpc

                # And include the coefficients as conj(c)*M*c
                result.append(phase * dot(conj(coeffbra[row]).T, dot(M, coeffket[col])))

        # Todo: improve to avoid unnecessary computations of other components
        if component is not None:
            result = result[component]
        elif summed is True:
            result = sum(result)

        return result


    def build_matrix(self, pacbra, packet, operator=None):
        """Calculate the matrix representation of $\Braket{\Psi|f|\Psi}$.
        @param pacbra: The wavepacket $<\Psi|$ from the bra with $Nbra$ components and basis size of $Kbra$.
        @param packet: The wavepacket $|\Psi>$ from the ket with $Nket$ components and basis size of $Kket$.
        @param operator: A function with two arguments $f:(q, x) \rightarrow R^{Nbra \times Nket}$.
        @return: A square matrix of size $Nbra*Kbra \times Nket*Kket$.
        """
        weights = self.QR.get_weights()

        # Packets can have different number of components
        Nbra = pacbra.get_number_components()
        Nket = packet.get_number_components()
        # Packets can also have different basis size
        Kbra = pacbra.get_basis_size()
        Kket = packet.get_basis_size()

        eps = packet.eps

        Pibra = pacbra.get_parameters(aslist=True)
        Piket = packet.get_parameters(aslist=True)

        result = zeros((Nbra*Kbra,Nket*Kket), dtype=complexfloating)

        # Operator is None is interpreted as identity transformation
        if operator is None:
            operator = lambda foo, nodes, component=None: ones(nodes.shape) if component[0] == component[1] else zeros(nodes.shape)

        for row in xrange(Nbra):
            for col in xrange(Nket):
                Pimix = self.mix_parameters(Pibra[row], Piket[col])
                nodes = self.transform_nodes(Pibra[row], Piket[col], eps)
                # Operator should support the component notation for efficiency
                # Todo: operator should be only f(nodes)
                values = operator(Pimix[0], nodes, component=(row,col))

                phase = exp(1.0j/eps**2 * (Piket[col][2]-conj(Pibra[row][2])))
                factor = squeeze(eps * values * weights * Pimix[1])

                M = zeros((Kbra,Kket), dtype=complexfloating)

                basisr = pacbra.evaluate_basis_at(nodes, component=row, prefactor=True)
                basisc = packet.evaluate_basis_at(nodes, component=col, prefactor=True)

                # Summing up matrices over all quadrature nodes
                for k in xrange(self.QR.get_number_nodes()):
                    tmpr = matrix(basisr[:,k])
                    tmpc = matrix(basisc[:,k])
                    M += factor[k] * tmpr.H * tmpc

                result[row*Kbra:(row+1)*Kbra, col*Kket:(col+1)*Kket] = phase * M

        return result
