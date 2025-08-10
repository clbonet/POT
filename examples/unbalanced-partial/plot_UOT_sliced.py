# -*- coding: utf-8 -*-
"""
===============================
Sliced Unbalanced optimal transport
===============================

This example illustrates the behavior of Sliced UOT versus
Unbalanced Sliced OT.

The first one removes outliers on each sliced while the second one
removes outliers of the original marginals.
"""

# Author:
#
# License: MIT License

import numpy as np
import matplotlib.pylab as pl
import ot
import torch
import matplotlib.pyplot as plt
import matplotlib as mpl

from sklearn.neighbors import KernelDensity

##############################################################################
# Generate data
# -------------


# %% parameters

get_rot = lambda theta: np.array(
    [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
)


# regular distribution of Gaussians around a circle
def make_blobs_reg(n_samples, n_blobs, scale=0.5):
    per_blob = int(n_samples / n_blobs)
    result = np.random.randn(per_blob, 2) * scale + 5
    theta = (2 * np.pi) / (n_blobs)
    for r in range(1, n_blobs):
        new_blob = (np.random.randn(per_blob, 2) * scale + 5).dot(get_rot(theta * r))
        result = np.vstack((result, new_blob))
    return result


def make_blobs_random(n_samples, n_blobs, scale=0.5, offset=3):
    per_blob = int(n_samples / n_blobs)
    result = np.random.randn(per_blob, 2) * scale + np.random.randn(1, 2) * offset
    for r in range(1, n_blobs):
        new_blob = np.random.randn(per_blob, 2) * scale + np.random.randn(1, 2) * offset
        result = np.vstack((result, new_blob))
    return result


def make_spiral(n_samples, noise=0.5):
    n = np.sqrt(np.random.rand(n_samples, 1)) * 780 * (2 * np.pi) / 360
    d1x = -np.cos(n) * n + np.random.rand(n_samples, 1) * noise
    d1y = np.sin(n) * n + np.random.rand(n_samples, 1) * noise
    return np.array(np.hstack((d1x, d1y)))


n_samples = 500
expe = "outlier"

np.random.seed(42)

nb_outliers = 200
Xs = make_blobs_random(n_samples=n_samples, scale=0.2, n_blobs=1, offset=0) - 0.5
Xs_outlier = make_blobs_random(
    n_samples=nb_outliers, scale=0.05, n_blobs=1, offset=0
) - [2, 0.5]

Xs = np.vstack((Xs, Xs_outlier))
Xt = make_blobs_random(n_samples=n_samples, scale=0.2, n_blobs=1, offset=0) + 1.5
y = np.hstack(([0] * (n_samples + nb_outliers), [1] * n_samples))
X = np.vstack((Xs, Xt))


Xs_torch = torch.from_numpy(Xs).type(torch.float)
Xt_torch = torch.from_numpy(Xt).type(torch.float)

p = 2
num_proj = 180

a = torch.ones(Xs.shape[0], dtype=torch.float)
b = torch.ones(Xt.shape[0], dtype=torch.float)

# construct projections
thetas = np.linspace(0, np.pi, num_proj)
dir = np.array([(np.cos(theta), np.sin(theta)) for theta in thetas])
dir_torch = torch.from_numpy(dir).type(torch.float)


Xps = torch.dot(Xs_torch, dir_torch.T)  # shape (n, n_projs)
Xpt = torch.dot(Xt_torch, dir_torch.T)

##############################################################################
# Compute SUOT and USOT
# -------------

# %%

rho1_SUOT = 1
rho2_SUOT = 1
_, log = ot.unbalanced.sliced_unbalanced_ot(
    Xs_torch,
    Xt_torch,
    (rho1_SUOT, rho2_SUOT),
    a,
    b,
    num_proj,
    p,
    numItermax=10,
    projections=dir_torch.T,
    mode="backprop",
    log=True,
)
A_SUOT, B_SUOT = log["a_reweighted"].T, log["b_reweighted"].T


rho1_USOT = 1
rho2_USOT = 1
A_USOT, B_USOT, _ = ot.unbalanced_sliced_ot(
    Xs_torch,
    Xt_torch,
    (rho1_USOT, rho2_USOT),
    a,
    b,
    num_proj,
    p,
    numItermax=10,
    projections=dir_torch.T,
    mode="backprop",
)


##############################################################################
# Plot reweighted distributions on several slices
# -------------

# %%


def kde_sklearn(x, x_grid, weights=None, bandwidth=0.2, **kwargs):
    """Kernel Density Estimation with Scikit-learn"""
    kde_skl = KernelDensity(bandwidth=bandwidth, **kwargs)
    if weights is not None:
        kde_skl.fit(x[:, np.newaxis], sample_weight=weights)
    else:
        kde_skl.fit(x[:, np.newaxis])
    # score_samples() returns the log-likelihood of the samples
    log_pdf = kde_skl.score_samples(x_grid[:, np.newaxis])
    return np.exp(log_pdf)


c1 = np.array(mpl.colors.to_rgb("lightcoral"))
c2 = np.array(mpl.colors.to_rgb("steelblue"))

# define plotting grid
xlim_min = -3
xlim_max = 3
x_grid = np.linspace(xlim_min, xlim_max, 200)
bw = 0.05

# visu parameters
nb_slices = 6
offset_degree = int(180 / nb_slices)

delta_degree = np.pi / nb_slices
colors = plt.cm.Reds(np.linspace(0.3, 1, nb_slices))

X1 = np.array([-4, 0])
X2 = np.array([4, 0])

fig = plt.figure(figsize=(28, 8))
ax1 = plt.subplot2grid((nb_slices, 3), (0, 0), rowspan=nb_slices)


for i in range(nb_slices):
    R = get_rot(delta_degree * (-i))
    X1_r = X1.dot(R)
    X2_r = X2.dot(R)
    if i == 0:
        ax1.plot(
            [X1_r[0], X2_r[0]],
            [X1_r[1], X2_r[1]],
            color=colors[i],
            alpha=0.8,
            zorder=0,
            label="Directions",
        )
    else:
        ax1.plot(
            [X1_r[0], X2_r[0]], [X1_r[1], X2_r[1]], color=colors[i], alpha=0.8, zorder=0
        )
ax1.scatter(Xs[:, 0], Xs[:, 1], zorder=1, color=c2, label="Source data")
ax1.scatter(Xt[:, 0], Xt[:, 1], zorder=1, color=c1, label="Target data")
ax1.set_xlim([-3, 3])
ax1.set_ylim([-3, 3])
ax1.set_yticks([])
ax1.set_xticks([])
ax1.legend(loc="best", fontsize=18)
ax1.set_xlabel("Original distributions", fontsize=22)

# ***** plot SUOT
fig.subplots_adjust(hspace=0)
fig.subplots_adjust(wspace=0.1)

for i in range(nb_slices):
    ax = plt.subplot2grid((nb_slices, 3), (i, 1))
    weights_src = A_SUOT[i * offset_degree, :].cpu().numpy()
    weights_tgt = B_SUOT[i * offset_degree, :].cpu().numpy()
    samples_src = Xps[i * offset_degree, :].cpu().numpy()
    samples_tgt = Xpt[i * offset_degree, :].cpu().numpy()
    pdf_source = kde_sklearn(samples_src, x_grid, weights=weights_src, bandwidth=bw)
    pdf_target = kde_sklearn(samples_tgt, x_grid, weights=weights_tgt, bandwidth=bw)
    pdf_source_without_w = kde_sklearn(samples_src, x_grid, bandwidth=bw)
    pdf_target_without_w = kde_sklearn(samples_tgt, x_grid, bandwidth=bw)

    ax.scatter(samples_src, [-0.2] * samples_src.shape[0], color=c2, s=2)
    ax.plot(x_grid, pdf_source, color=c2, alpha=0.8, lw=2)
    ax.fill(x_grid, pdf_source_without_w, ec="grey", fc="grey", alpha=0.3)
    ax.fill(x_grid, pdf_source, ec=c2, fc=c2, alpha=0.3)

    ax.scatter(samples_tgt, [-0.2] * samples_tgt.shape[0], color=c1, s=2)
    ax.plot(x_grid, pdf_target, color=c1, alpha=0.8, lw=2)
    ax.fill(x_grid, pdf_target_without_w, ec="grey", fc="grey", alpha=0.3)
    ax.fill(x_grid, pdf_target, ec=c2, fc=c1, alpha=0.3)

    # frac_mass = int(100*weights_src.sum())
    # plt.text(.9, .9, '% mass={}%'.format(frac_mass), ha='right', va='top', color='red',fontsize=14, transform=ax.transAxes)

    ax.set_xlim(xlim_min, xlim_max)
    ax.set_ylabel(
        r"$\theta=${}$^o$".format(i * offset_degree), color=colors[i], fontsize=16
    )
    ax.set_yticks([])
    ax.set_yticks([])
ax.set_xlabel(
    r"SUOT  $\rho_1={}$ $\rho_2={}$".format(rho1_SUOT, rho2_SUOT), fontsize=22
)
# ***** plot USOT

for i in range(nb_slices):
    ax = plt.subplot2grid((nb_slices, 3), (i, 2))
    weights_src = A_USOT.cpu().numpy()
    weights_tgt = B_USOT.cpu().numpy()
    samples_src = Xps[i * offset_degree, :].cpu().numpy()
    samples_tgt = Xpt[i * offset_degree, :].cpu().numpy()
    pdf_source = kde_sklearn(samples_src, x_grid, weights=weights_src, bandwidth=bw)
    pdf_target = kde_sklearn(samples_tgt, x_grid, weights=weights_tgt, bandwidth=bw)
    pdf_source_without_w = kde_sklearn(samples_src, x_grid, bandwidth=bw)
    pdf_target_without_w = kde_sklearn(samples_tgt, x_grid, bandwidth=bw)

    ax.scatter(samples_src, [-0.2] * samples_src.shape[0], color=c2, s=2)
    ax.plot(x_grid, pdf_source, color=c2, alpha=0.8, lw=2)
    ax.fill(x_grid, pdf_source_without_w, ec="grey", fc="grey", alpha=0.3)
    ax.fill(x_grid, pdf_source, ec=c2, fc=c2, alpha=0.3)

    ax.scatter(samples_tgt, [-0.2] * samples_tgt.shape[0], color=c1, s=2)
    ax.plot(x_grid, pdf_target, color=c1, alpha=0.8, lw=2)
    ax.fill(x_grid, pdf_target_without_w, ec="grey", fc="grey", alpha=0.3)
    ax.fill(x_grid, pdf_target, ec=c2, fc=c1, alpha=0.3)

    ax.set_xlim(xlim_min, xlim_max)
    ax.set_ylabel(
        r"$\theta=${}$^o$".format(i * offset_degree), color=colors[i], fontsize=16
    )
    ax.set_yticks([])
ax.set_xlabel(
    r"USOT  $\rho_1={}$ $\rho_2={}$".format(rho1_USOT, rho2_USOT), fontsize=22
)

plt.show()
