import unittest
from graspy.simulations.simulations import sample_edges, p_from_latent
from graspy.simulations.rdpg_corr import rdpg_corr
import numpy as np
import pytest
import warnings


class Test_RDPG_Corr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = 0.3
        cls.Y = None
        cls.X = np.random.dirichlet([20, 20], size=300)

    def test_dimensions(self):
        np.random.seed(1234)
        A, B = rdpg_corr(
            self.X, self.Y, self.r, rescale=False, directed=False, loops=False
        )
        self.assertTrue(A.shape, (300, 300))
        self.assertTrue(B.shape, (300, 300))

    def test_inputs(self):
        x1 = np.array([[1, 1], [1, 1]])
        x2 = np.array([[1, 1]])
        x3 = np.zeros((2, 2, 2))
        with self.assertRaises(TypeError):
            p_from_latent("hi")  # wrong type
        with self.assertRaises(ValueError):
            p_from_latent(x1, x2)  # dimension mismatch
        with self.assertRaises(ValueError):
            p_from_latent(x3)  # wrong num dimensions
        with self.assertRaises(TypeError):
            sample_edges("XD")  # wrong type
        with self.assertRaises(ValueError):
            sample_edges(x3)  # wrong num dimensions
        with self.assertRaises(ValueError):
            sample_edges(x2)  # wrong shape for P

        if any(self.X[self.X > 1]) or any(self.X[self.X < -1]):  # wrong values for P
            raise ValueError("P values should be less than 1 and bigger than -1")

    def test_rdpg_corr(self):
        np.random.seed(123)
        g1, g2 = rdpg_corr(
            self.X, self.Y, self.r, rescale=False, directed=False, loops=False
        )

        # check the dimention of g1, g2
        self.assertTrue(g1.shape == (self.X.shape[0], self.X.shape[0]))
        self.assertTrue(g1.shape == (self.X.shape[0], self.X.shape[0]))

        # check rho
        g1 = g1[np.where(~np.eye(g1.shape[0], dtype=bool))]
        g2 = g2[np.where(~np.eye(g2.shape[0], dtype=bool))]
        correlation = np.corrcoef(g1, g2)[0, 1]
        self.assertTrue(np.isclose(correlation, self.r, atol=0.01))

    # check P
    def test_p_is_close(self):
        P = p_from_latent(self.X, self.Y, rescale=False, loops=False)
        if any(P[P > 1]) or any(P[P < -1]):  # wrong values for P
            raise ValueError("P values should be less than 1 and bigger than -1")

        np.random.seed(8888)
        X = 0.5 * np.ones((100, 2))
        graphs = []
        P = p_from_latent(X, rescale=True, loops=True)
        for i in range(1000):
            graphs.append(sample_edges(P, directed=True, loops=True))
        graphs = np.stack(graphs)
        self.assertAlmostEqual(np.mean(graphs), 0.5, delta=0.01)
