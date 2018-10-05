import numpy as np

from .base import BaseInference
from ..embed import AdjacencySpectralEmbed, LaplacianSpectralEmbed, OmnibusEmbed


class NonparametricTest(BaseInference):
    """
    Two sample hypothesis test for the nonparametric problem of determining 
    whether two random dot product graphs have the same underlying
    distributions.

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
        self.embedding = 'ase'
        self.n_components_ = n_components
