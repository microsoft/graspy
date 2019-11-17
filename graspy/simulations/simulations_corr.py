import numpy as np
from graspy.simulations import sample_edges, er_np


def sample_edges_corr(P, r, directed, loops):
    """
    Generate a pair of correlated graphs with Bernoulli distribution.
    Both G1 and G2 are binary matrices. 

    Parameters
    ----------
    P: np.ndarray, shape (n_vertices, n_vertices)
        Matrix of probabilities (between 0 and 1) for a random graph.
        
    R: float
        Probability of the correlation between the same vertices in two graphs.

    directed: boolean, optional (default=False)
        If False, output adjacency matrix will be symmetric. Otherwise, output adjacency
        matrix will be asymmetric.

    loops: boolean, optional (default=False)
        If False, no edges will be sampled in the diagonal. Otherwise, edges
        are sampled in the diagonal.

    References
    ----------
    .. [1] Vince Lyzinski, et al. "Seeded Graph Matching for Correlated Erdos-Renyi Graphs", 
       Journal of Machine Learning Research 15, 2014
        
    Returns
    -------
    G1: ndarray (n_vertices, n_vertices)
        Adjacency matrix the same size as P representing a random graph,

    G2: ndarray (n_vertices, n_vertices)
        Adjacency matrix the same size as P representing a random graph,

    Examples
    --------
    >>> np.random.seed(1)
    >>> p = 0.5
    >>> r = 0.3
    >>> P = p * np.ones((5,5))

    To sample a correlated graph pair based on P and Rho matrices:

    >>> sample_edges_corr(P, r, directed = False, loops = False)
    (array([[0., 1., 0., 0., 0.],
            [1., 0., 0., 0., 0.],
            [0., 0., 0., 0., 1.],
            [0., 0., 0., 0., 1.],
            [0., 0., 1., 1., 0.]]), array([[0., 1., 0., 0., 0.],
            [1., 0., 1., 0., 1.],
            [0., 1., 0., 1., 1.],
            [0., 0., 1., 0., 1.],
            [0., 1., 1., 1., 0.]]))
    """
    # test input
    if type(P) is not np.ndarray:
        raise TypeError("P must be numpy.ndarray")
    if len(P.shape) != 2:
        raise ValueError("P must have dimension 2 (n_vertices, n_dimensions)")
    if P.shape[0] != P.shape[1]:
        raise ValueError("P must be a square matrix")

    if not np.issubdtype(type(r), np.floating):
        raise TypeError("r is not of type float.")
    elif r < 0 or r > 1:
        msg = "r must be between 0 and 1."
        raise ValueError(msg)

    if type(directed) is not bool:
        raise TypeError("directed is not of type bool.")
    if type(loops) is not bool:
        raise TypeError("loops is not of type bool.")

    G1 = sample_edges(P, directed=directed, loops=loops)
    P2 = G1.copy()
    P2 = np.where(P2 == 1, P + r * (1 - P), P * (1 - r))
    G2 = sample_edges(P2, directed=directed, loops=loops)
    return G1, G2


def sample_edges_er_corr(n, p, r, directed, loops):
    """
    Generate a pair of correlated graphs with specified edge probability
    Both G1 and G2 are binary matrices. 

    Parameters
    ----------
    n: int
       Number of vertices

    p: float
        Probability of an edge existing between two vertices, between 0 and 1.
    
    R: float
        Probability of the correlation between the same vertices in two graphs.
    
    directed: boolean, optional (default=False)
        If False, output adjacency matrix will be symmetric. Otherwise, output adjacency
        matrix will be asymmetric.
    
    loops: boolean, optional (default=False)
        If False, no edges will be sampled in the diagonal. Otherwise, edges
        are sampled in the diagonal.
    
    Returns
    -------
    G1: ndarray (n_vertices, n_vertices)
        Sampled adjacency matrix

    G2: ndarray (n_vertices, n_vertices)
        Binary matrix the same size as P representing a random graph
        generated by the function of sample_edges
    
    Examples
    --------
    >>> np.random.seed(2)
    >>> p = 0.5
    >>> r = 0.3
    >>> n = 5

    To sample a correlated ER graph pair based on n, p and R matrices:

    >>> sample_edges_er_corr(n, p, r, directed=False, loops=False)
    (array([[0., 0., 1., 0., 0.],
        [0., 0., 0., 1., 0.],
        [1., 0., 0., 1., 1.],
        [0., 1., 1., 0., 1.],
        [0., 0., 1., 1., 0.]]), array([[0., 1., 1., 1., 0.],
        [1., 0., 0., 1., 0.],
        [1., 0., 0., 1., 1.],
        [1., 1., 1., 0., 1.],
        [0., 0., 1., 1., 0.]]))
    """
    # test input
    if not np.issubdtype(type(n), np.integer):
        raise TypeError("n is not of type int.")
    elif n <= 0:
        msg = "n must be > 0."
        raise ValueError(msg)

    if not np.issubdtype(type(p), np.floating):
        raise TypeError("r is not of type float.")
    elif p < 0 or p > 1:
        msg = "p must between 0 and 1."
        raise ValueError(msg)

    if not np.issubdtype(type(r), np.floating):
        raise TypeError("r is not of type float.")
    elif r < 0 or r > 1:
        msg = "r must between 0 and 1."
        raise ValueError(msg)

    if type(directed) is not bool:
        raise TypeError("directed is not of type bool.")
    if type(loops) is not bool:
        raise TypeError("loops is not of type bool.")

    P = p * np.ones((n, n))
    G1, G2 = sample_edges_corr(P, r, directed=directed, loops=loops)
    return G1, G2
