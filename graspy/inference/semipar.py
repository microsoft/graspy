# Ben Pedigo
# bpedigo [at] jhu.edu
# 10.18.2018

import numpy as np
from .base import BaseInference
from ..embed import AdjacencySpectralEmbed, LaplacianSpectralEmbed, OmnibusEmbed, select_dimension
from ..simulations import rdpg
from scipy.spatial import procrustes
from scipy.linalg import orthogonal_procrustes
from ..utils import import_graph, is_symmetric


class SemiparametricTest(BaseInference):
    r"""
    Two sample hypothesis test for the semiparametric problem of determining
    whether two random dot product graphs have the same latent positions [1].

    Currently, the function only supports undirected graphs

    Parameters
    ----------
    embedding : string, { 'ase' (default), 'omnibus'}
        String describing the embedding method to use.
        'ase'
            Embed each graph separately using adjacency spectral embedding
            and use Procrustes to align the embeddings.
        'omnibus'
            Embed all graphs simultaneously using omnibus embedding.

    n_components : None (default), or int
        Number of embedding dimensions. If None, the optimal embedding
        dimensions are found by the Zhu and Godsi algorithm.

    test_case : string, {'rotation' (default), 'scalar-rotation', 'diagonal-rotation'}
        describes the exact form of the hypothesis to test when using 'ase' or 'lse' 
        as an embedding method. Ignored if using 'omnibus'. Given two latent positions,
        :math:`X_1` and :math:`X_2`, and an orthogonal rotation matrix :math:`R` that 
        minimizes :math:`||X1 - X2 R||_F`:

        - 'rotation'
            .. math:: H_o: X_1 = X_2 R
        - 'scalar-rotation'
            .. math:: H_o: X_1 = c X_2 R
            where `c` is a scalar, `c > 0`
        - 'diagonal-rotation'
            .. math:: H_o: X_1 = D X_2 R
            where `D` is an arbitrary diagonal matrix

    n_bootstraps : int, optional (default 500)
        Number of bootstrap simulations to run to generate the null distribution

    Examples
    --------
    >>> spt = SemiparametricTest(n_components=2, test_case='rotation')
    >>> p = spt.fit(A1, A2)

    See also
    --------
    graspy.embed.AdjacencySpectralEmbed
    graspy.embed.OmnibusEmbed
    graspy.embed.selectSVD

    References  
    ----------
    .. [1] Tang, M., A. Athreya, D. Sussman, V. Lyzinski, Y. Park, Priebe, C.E. 
       "A Semiparametric Two-Sample Hypothesis Testing Problem for Random Graphs"
       Journal of Computational and Graphical Statistics, Vol. 26(2), 2017
    """

    def __init__(
            self,
            embedding='ase',
            n_components=None,
            n_bootstraps=500,
            test_case='rotation',
    ):
        if type(n_bootstraps) is not int:
            raise TypeError()
        if type(test_case) is not str:
            raise TypeError()
        if n_bootstraps < 1:
            raise ValueError(
                '{} is invalid number of bootstraps, must be greater than 1'.
                format(n_bootstraps))
        if test_case not in [
                'rotation', 'scalar-rotation', 'diagonal-rotation'
        ]:
            raise ValueError(
                'test_case must be one of \'rotation\', \'scalar-rotation\',\'diagonal-rotation\''
            )

        super().__init__(
            embedding=embedding,
            n_components=n_components,
        )

        self.n_bootstraps = n_bootstraps
        self.test_case = test_case
        # paper uses these always, but could be kwargs eventually. need to test
        self.rescale = False
        self.loops = False

    def _bootstrap(self, X_hat):
        t_bootstrap = np.zeros(self.n_bootstraps)
        for i in range(self.n_bootstraps):
            A1_simulated = rdpg(X_hat, rescale=self.rescale, loops=self.loops)
            A2_simulated = rdpg(X_hat, rescale=self.rescale, loops=self.loops)
            X1_hat_simulated, X2_hat_simulated = self._embed(
                A1_simulated, A2_simulated)
            t_bootstrap[i] = self._difference_norm(X1_hat_simulated,
                                                   X2_hat_simulated)
        return t_bootstrap

    def _difference_norm(self, X1, X2):
        if self.embedding in ['ase']:
            if self.test_case == 'rotation':
                R = orthogonal_procrustes(X1, X2)[0]
                return np.linalg.norm(X1 @ R - X2)
            elif self.test_case == 'scalar-rotation':
                R, s = orthogonal_procrustes(X1, X2)
                return np.linalg.norm(s / np.sum(X1**2) * X1 @ R - X2)
            elif self.test_case == 'diagonal-rotation':
                normX1 = np.sum(X1**2, axis=1)
                normX2 = np.sum(X2**2, axis=1)
                normX1[normX1 <= 1e-15] = 1
                normX2[normX2 <= 1e-15] = 1
                X1 = X1 / np.sqrt(normX1[:, None])
                X2 = X2 / np.sqrt(normX2[:, None])
                R = orthogonal_procrustes(X1, X2)[0]
                return np.linalg.norm(X1 @ R - X2)
        else:
            # in the omni case we don't need to align
            return np.linalg.norm(X1 - X2)

    def _embed(self, A1, A2):
        if self.embedding == 'ase':
            X1_hat = AdjacencySpectralEmbed(
                n_components=self.n_components).fit_transform(A1)
            X2_hat = AdjacencySpectralEmbed(
                n_components=self.n_components).fit_transform(A2)
        elif self.embedding == 'omnibus':
            X_hat_compound = OmnibusEmbed(
                n_components=self.n_components).fit_transform((A1, A2))
            X1_hat = X_hat_compound[:A1.shape[0], :]
            X2_hat = X_hat_compound[A2.shape[0]:, :]
        return (X1_hat, X2_hat)

    def fit(self, A1, A2):
        """
        Fits the test to the two input graphs

        Parameters
        ----------
        A1, A2 : nx.Graph, nx.DiGraph, nx.MultiDiGraph, nx.MultiGraph, np.ndarray
            The two graphs to run a hypothesis test on
            If np.ndarray, shape must be `(n_vertices, n_vertices)` for both graphs, 
            where `n_vertices` is the same for both
        
        Returns
        -------
        p : float
            The p value corresponding to the specified hypothesis test
        """
        A1 = import_graph(A1)
        A2 = import_graph(A2)
        if not is_symmetric(A1) or not is_symmetric(A2):
            raise NotImplementedError()  # TODO asymmetric case
        if A1.shape != A2.shape:
            raise ValueError('Input matrices do not have matching dimensions')
        if self.n_components is None:
            # get the last elbox from ZG for each and take the maximum
            num_dims1 = select_dimension(A1)[0][-1]
            num_dims2 = select_dimension(A2)[0][-1]
            self.n_components = max(num_dims1, num_dims2)
        X_hats = self._embed(A1, A2)
        T_sample = self._difference_norm(X_hats[0], X_hats[1])
        T1_bootstrap = self._bootstrap(X_hats[0])
        T2_bootstrap = self._bootstrap(X_hats[1])

        # Continuity correction - note that the +0.5 causes p > 1 sometimes # TODO
        p1 = (len(T1_bootstrap[T1_bootstrap >= T_sample]) +
              0.5) / self.n_bootstraps
        p2 = (len(T2_bootstrap[T2_bootstrap >= T_sample]) +
              0.5) / self.n_bootstraps

        p = max(p1, p2)

        # TODO : what to store as fields here, or make _private fields
        # at least for the sake of testing, I'm going to keep everything

        self.T1_bootstrap = T1_bootstrap
        self.T2_bootstrap = T2_bootstrap
        self.T_sample = T_sample
        self.p1 = p1
        self.p2 = p2
        self.p = p

        return p
