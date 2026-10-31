"""Two tagged arch 7.2.0 reference functions, not the installed arch package.

Copyright (c) 2017 Kevin Sheppard. All rights reserved.
See docs/licenses/arch-7.2.0.txt for the complete permission and disclaimer.
Sources: https://raw.githubusercontent.com/bashtage/arch/v7.2.0/arch/bootstrap/base.py
https://raw.githubusercontent.com/bashtage/arch/v7.2.0/arch/bootstrap/_samplers_python.py
Only import/type scaffolding differs; function definitions are captured verbatim.
"""
from typing import Optional
import numpy as np

Float64Array = Int64Array = np.ndarray


def _single_optimal_block(x: Float64Array) -> tuple[float, float]:
    """
    Compute the optimal window length for a single series

    Parameters
    ----------
    x : ndarray
        The data to use in the optimal window estimation

    Returns
    -------
    stationary : float
        Estimated optimal window length for stationary bootstrap
    circular : float
        Estimated optimal window length for circular bootstrap
    """
    nobs = x.shape[0]
    eps = x - x.mean(0)
    b_max = np.ceil(min(3 * np.sqrt(nobs), nobs / 3))
    kn = max(5, int(np.log10(nobs)))
    m_max = int(np.ceil(np.sqrt(nobs))) + kn
    # Find first collection of kn autocorrelations that are insignificant
    cv = 2 * np.sqrt(np.log10(nobs) / nobs)
    acv = np.zeros(m_max + 1)
    abs_acorr = np.zeros(m_max + 1)
    opt_m: Optional[int] = None
    for i in range(m_max + 1):
        v1 = eps[i + 1 :] @ eps[i + 1 :]
        v2 = eps[: -(i + 1)] @ eps[: -(i + 1)]
        cross_prod = eps[i:] @ eps[: nobs - i]
        acv[i] = cross_prod / nobs
        abs_acorr[i] = np.abs(cross_prod) / np.sqrt(v1 * v2)
        if i >= kn:
            if np.all(abs_acorr[i - kn : i] < cv) and opt_m is None:
                opt_m = i - kn
    m = 2 * max(opt_m, 1) if opt_m is not None else m_max
    m = min(m, m_max)

    g = 0.0
    lr_acv = acv[0]
    for k in range(1, m + 1):
        lam = 1 if k / m <= 1 / 2 else 2 * (1 - k / m)
        g += 2 * lam * k * acv[k]
        lr_acv += 2 * lam * acv[k]
    d_sb = 2 * lr_acv**2
    d_cb = 4 / 3 * lr_acv**2
    b_sb = ((2 * g**2) / d_sb) ** (1 / 3) * nobs ** (1 / 3)
    b_cb = ((2 * g**2) / d_cb) ** (1 / 3) * nobs ** (1 / 3)
    b_sb = min(b_sb, b_max)
    b_cb = min(b_cb, b_max)
    return b_sb, b_cb


def stationary_bootstrap_sample_python(
    indices: Int64Array, u: Float64Array, p: float
) -> Int64Array:
    """
    Generate indices for sampling from the stationary bootstrap.

    Parameters
    -------
    indices: ndarray
        Single-dimensional array containing draws from randint with the same
        size as the data in the range of [0,nobs).
    u : ndarray
        Single-dimensional Array of standard uniforms.
    p : float
        Probability that a new block is started in the stationary bootstrap.
        The multiplicative reciprocal of the window length.

    Returns
    -------
    ndarray
        Indices for an iteration of the stationary bootstrap.
    """
    num_items = indices.shape[0]
    for i in range(1, num_items):
        if u[i] > p:
            indices[i] = indices[i - 1] + 1
            if indices[i] == num_items:
                indices[i] = 0

    return indices
