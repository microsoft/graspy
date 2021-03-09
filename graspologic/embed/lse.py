# Copyright (c) Microsoft Corporation and contributors.
# Licensed under the MIT License.

import warnings

from .base import BaseSpectralEmbed
from ..utils import import_graph, to_laplacian, is_fully_connected
from sklearn.utils.validation import check_is_fitted

import numpy as np


class LaplacianSpectralEmbed(BaseSpectralEmbed):
    r"""
    Class for computing the laplacian spectral embedding of a graph.

    The laplacian spectral embedding (LSE) is a k-dimensional Euclidean representation
    of the graph based on its Laplacian matrix. It relies on an SVD to reduce
    the dimensionality to the specified k, or if k is unspecified, can find a number
    of dimensions automatically.

    Parameters
    ----------
    form : {'DAD' (default), 'I-DAD', 'R-DAD'}, optional
        Specifies the type of Laplacian normalization to use.

    n_components : int or None, default = None
        Desired dimensionality of output data. If "full",
        ``n_components`` must be ``<= min(X.shape)``. Otherwise, ``n_components`` must be
        ``< min(X.shape)``. If None, then optimal dimensions will be chosen by
        :func:`~graspologic.embed.select_dimension` using ``n_elbows`` argument.

    n_elbows : int, optional, default: 2
        If ``n_components`` is None, then compute the optimal embedding dimension using
        :func:`~graspologic.embed.select_dimension`. Otherwise, ignored.

    algorithm : {'randomized' (default), 'full', 'truncated'}, optional
        SVD solver to use:

        - 'randomized'
            Computes randomized svd using
            :func:`sklearn.utils.extmath.randomized_svd`
        - 'full'
            Computes full svd using :func:`scipy.linalg.svd`
        - 'truncated'
            Computes truncated svd using :func:`scipy.sparse.linalg.svds`

    n_iter : int, optional (default = 5)
        Number of iterations for randomized SVD solver. Not used by 'full' or
        'truncated'. The default is larger than the default in randomized_svd
        to handle sparse matrices that may have large slowly decaying spectrum.

    check_lcc : bool , optional (defult = True)
        Whether to check if input graph is connected. May result in non-optimal
        results if the graph is unconnected. If True and input is unconnected,
        a UserWarning is thrown. Not checking for connectedness may result in
        faster computation.

    regularizer: int, float or None, optional (default=None)
        Constant to be added to the diagonal of degree matrix. If None, average
        node degree is added. If int or float, must be >= 0. Only used when
        ``form`` is 'R-DAD'.

    concat : bool, optional (default False)
        If graph is directed, whether to concatenate left and right (out and in) latent positions along axis 1.


    Attributes
    ----------
    n_features_in_: int
        Number of features passed to the :func:`~graspologic.embed.LaplacianSpectralEmbed.fit` method.

    latent_left_ : array, shape (n_samples, n_components)
        Estimated left latent positions of the graph.

    latent_right_ : array, shape (n_samples, n_components), or None
        Only computed when the graph is directed, or adjacency matrix is assymetric.
        Estimated right latent positions of the graph. Otherwise, None.

    singular_values_ : array, shape (n_components)
        Singular values associated with the latent position matrices.

    See Also
    --------
    graspologic.embed.selectSVD
    graspologic.embed.select_dimension
    graspologic.utils.to_laplacian

    Notes
    -----
    The singular value decomposition:

    .. math:: A = U \Sigma V^T

    is used to find an orthonormal basis for a matrix, which in our case is the
    Laplacian matrix of the graph. These basis vectors (in the matrices U or V) are
    ordered according to the amount of variance they explain in the original matrix.
    By selecting a subset of these basis vectors (through our choice of dimensionality
    reduction) we can find a lower dimensional space in which to represent the graph.

    References
    ----------
    .. [1] Sussman, D.L., Tang, M., Fishkind, D.E., Priebe, C.E.  "A
       Consistent Adjacency Spectral Embedding for Stochastic Blockmodel Graphs,"
       Journal of the American Statistical Association, Vol. 107(499), 2012.
    .. [2] Von Luxburg, Ulrike. "A tutorial on spectral clustering," Statistics
        and computing, Vol. 17(4), pp. 395-416, 2007.
    .. [3] Rohe, Karl, Sourav Chatterjee, and Bin Yu. "Spectral clustering and
        the high-dimensional stochastic blockmodel," The Annals of Statistics,
        Vol. 39(4), pp. 1878-1915, 2011.
    """

    def __init__(
        self,
        form="DAD",
        n_components=None,
        n_elbows=2,
        algorithm="randomized",
        n_iter=5,
        check_lcc=True,
        regularizer=None,
        concat=False,
    ):
        super().__init__(
            n_components=n_components,
            n_elbows=n_elbows,
            algorithm=algorithm,
            n_iter=n_iter,
            check_lcc=check_lcc,
            concat=concat,
        )
        self.form = form
        self.regularizer = regularizer

    def transform(self, X):
        """
        Obtain latent positions from an adjacency matrix or matrix of out-of-sample
        vertices. For more details on transforming out-of-sample vertices, see the
        :ref:`tutorials <embed_tutorials>`.

        Parameters
        ----------
        X : array-like or tuple, original shape or (n_oos_vertices, n_vertices).

            The original fitted matrix ("graph" in fit) or new out-of-sample data.
            If ``X`` is the original fitted matrix, returns a matrix close to
            ``self.fit_transform(X)``.

            If ``X`` is an out-of-sample matrix, n_oos_vertices is the number
            of new vertices, and n_vertices is the number of vertices in the
            original graph. If tuple, graph is directed and ``X[0]`` contains
            edges from out-of-sample vertices to in-sample vertices.

        Returns
        -------
        array_like or tuple, shape (n_oos_vertices, n_components)
        or (n_vertices, n_components).

            Array of latent positions. Transforms the fitted matrix if it was passed
            in.

            If ``X`` is an array or tuple containing adjacency vectors corresponding to
            new nodes, returns the estimated latent positions for the new out-of-sample
            adjacency vectors.
            If undirected, returns array.
            If directed, returns ``(X_out, X_in)``, where ``X_out`` contains
            latent positions corresponding to nodes with edges from out-of-sample
            vertices to in-sample vertices.
        """
        # checks
        check_is_fitted(self, "is_fitted_")
        if isinstance(X, nx.classes.graph.Graph):
            X = import_graph(X)
        directed = self.latent_right_ is not None

        # correct types?
        if directed and not isinstance(X, tuple):
            if X.shape[0] == X.shape[1]:  # in case original matrix was passed
                msg = """A square matrix A was passed to ``transform`` in the directed case. 
                If this was the original in-sample matrix, either use ``fit_transform`` 
                or pass a tuple (A.T, A). If this was an out-of-sample matrix, directed
                graphs require a tuple (X_out, X_in)."""
                raise TypeError(msg)
            else:
                msg = "Directed graphs require a tuple (X_out, X_in) for out-of-sample transforms."
                raise TypeError(msg)
        if not directed and not isinstance(X, np.ndarray):
            raise TypeError("Undirected graphs require array input")

        # correct shape in y?
        latent_rows = self.latent_left_.shape[0]
        _X = X[0] if directed else X
        X_cols = _X.shape[-1]
        if _X.ndim > 2:
            raise ValueError("out-of-sample vertex must be 1d or 2d")
        if latent_rows != X_cols:
            msg = "out-of-sample vertex must be shape (n_oos_vertices, n_vertices)"
            raise ValueError(msg)

        # workhorse code
        if self.latent_right_ is None:
            return X @ self._pinv_left
        else:
            return X[1] @ self._pinv_right, X[0] @ self._pinv_left

    def fit(self, graph, y=None):
        """
        Fit LSE model to input graph

        By default, uses the Laplacian normalization of the form:

        .. math:: L = D^{-1/2} A D^{-1/2}

        Parameters
        ----------
        graph : array-like, scipy.sparse.csr_matrix, or networkx.Graph
            Input graph to embed. see graspologic.utils.import_graph

        Returns
        -------
        self : object
            Returns an instance of self.
        """
        A = import_graph(graph)

        if self.check_lcc:
            if not is_fully_connected(A):
                msg = (
                    "Input graph is not fully connected. Results may not"
                    + "be optimal. You can compute the largest connected component by"
                    + "using ``graspologic.utils.largest_connected_component``."
                )
                warnings.warn(msg, UserWarning)

        self.n_features_in_ = A.shape[0]
        L_norm = to_laplacian(A, form=self.form, regularizer=self.regularizer)
        self._reduce_dim(L_norm)

        # for out-of-sample
        inv_eigs = np.diag(1 / self.singular_values_)
        self._pinv_left = self.latent_left_ @ inv_eigs
        if self.latent_right_ is not None:
            self._pinv_right = self.latent_right_ @ inv_eigs

        self.is_fitted_ = True
        return self
