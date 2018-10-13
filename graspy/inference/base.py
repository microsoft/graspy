from abc import abstractmethod

from sklearn.base import BaseEstimator


class BaseInference(BaseEstimator):
    """
    Base class for inference tasks such as semiparametric and
    nonparametric inference tasks.

    Parameters
    ----------
    embedding : { 'ase' (default), 'lse, 'omnibus'}
        String describing the embedding method to use.
        Must be one of:
        'ase'
            Embed each graph separately using adjacency spectral embedding
            and use Procrustes to align the embeddings.
        'lse'
            Embed each graph separately using laplacian spectral embedding
            and use Procrustes to align the embeddings.
        'omnibus'
            Embed all graphs simultaneously using omnibus embedding.

    n_components : None (default), or Int
        Number of embedding dimensions. If None, the optimal embedding
        dimensions are found by the Zhu and Godsi algorithm.
    """

    def __init__(self, embedding='ase', n_components=None):
        self.embedding = embedding
        self.n_components = n_components

    @abstractmethod
    def _bootstrap(self):
        pass

    @abstractmethod
    def _embed(self, X1, X2, n_componets):
        """
        Computes the latent positions of input graphs

        Returns
        -------
        X1_hat : array-like, shape (n_vertices, n_components)
            Estimated latent positions of X1
        X2_hat : array-like, shape(n_vertices, n_components)
            Estimated latent positions of X2
        """
        if embedding == 'omnibus':
            pass
        elif embedding == 'ase':
            pass
        elif embedding == 'lse':
            pass
        else:
            msg = "{} is not a valid embedding method.".format(embedding)
            raise ValueError(msg)

    @abstractmethod
    def fit(self, A1, A2):
        """
        Compute the test statistic and the null distribution.

        Parameters
        ----------
        X1 : nx.Graph or np.ndarray
            A graph
        X2 : nx.Graph or np.ndarray
            A graph
        """