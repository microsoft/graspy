from typing import Union

import numpy as np
from packaging import version
from scipy import __version__ as scipy_version
from scipy.sparse import csr_matrix

if version.parse(scipy_version) >= version.parse("1.8.0"):
    from scipy.sparse import csr_array
else:
    # HACK: what should this be?
    csr_array = csr_matrix

from typing_extensions import Literal

from graspologic.types import List

# redefining since I don't want to add csr_array for ALL code in graspologic yet
AdjacencyMatrix = Union[np.ndarray, csr_matrix, csr_array]

MultilayerAdjacency = Union[List[AdjacencyMatrix], AdjacencyMatrix, np.ndarray]

PaddingType = Literal["adopted", "naive"]

InitType = Union[Literal["barycenter"], np.ndarray]

Scalar = Union[int, float, np.integer]

Int = Union[int, np.integer]
