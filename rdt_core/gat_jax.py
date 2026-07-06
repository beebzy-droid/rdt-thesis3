"""rdt_core.gat_jax — Edge-featured GATv2 prototype (JAX).

SCOPE NOTE (§9.2): prototype implementation for the container environment.
Production model is PyTorch Geometric GATv2Conv per lifecycle Table 6.1, trained
on reference hardware; this module exists to (a) validate the §2.2 architecture
end-to-end on dataset v0 and (b) set the graph-model baseline vs the state-only
flat bar (R² = 0.623, Finding #13). Architecture is §2.2-faithful at prototype
scale: GATv2 dynamic attention  a·LeakyReLU(W[h_u ‖ h_v ‖ e]),  multi-head
concat, edge features in attention AND messages, ΔG injected as an edge channel.
"""
from __future__ import annotations
import numpy as np
import jax, jax.numpy as jnp
import optax
from functools import partial


def init_params(key, d_v, d_e, dim=32, heads=4, layers=2):
    ks = jax.random.split(key, 3 + layers * 3)
    dh = dim // heads
    P = {"enc_v": jax.random.normal(ks[0], (d_v, dim)) * (2 / d_v) ** 0.5,
         "enc_e": jax.random.normal(ks[1], (d_e, dim)) * (2 / d_e) ** 0.5,
         "layers": []}
    for l in range(layers):
        P["layers"].append({
            "W": jax.random.normal(ks[2 + 3 * l], (heads, dim, dh)) * (2 / dim) ** 0.5,
            "We": jax.random.normal(ks[3 + 3 * l], (heads, dim, dh)) * (2 / dim) ** 0.5,
            "a": jax.random.normal(ks[4 + 3 * l], (heads, 3 * dh)) * 0.1,
        })
    P["head1"] = jax.random.normal(ks[-1], (2 * dim, 64)) * (2 / (2 * dim)) ** 0.5
    P["head2"] = jax.random.normal(key, (64, 1)) * (2 / 64) ** 0.5
    P["b1"] = jnp.zeros(64)
    return P


def gat_layer(lp, h, e, src, dst, n_nodes):
    """One GATv2 layer, ALL HEADS BATCHED. h [N,dim], e [E,dim] -> [N,dim]."""
    hs = jnp.einsum("ed,hdo->eho", h[src], lp["W"])           # [E,H,dh]
    hd = jnp.einsum("ed,hdo->eho", h[dst], lp["W"])
    ee = jnp.einsum("ed,hdo->eho", e, lp["We"])
    s = jnp.concatenate([hs, hd, ee], -1)                     # [E,H,3dh]
    logit = jnp.einsum("ehk,hk->eh", jax.nn.leaky_relu(s, 0.2), lp["a"])  # GATv2
    logit -= jax.ops.segment_max(logit, dst, n_nodes)[dst]    # stable softmax
    w = jnp.exp(logit)
    w /= jax.ops.segment_sum(w, dst, n_nodes)[dst] + 1e-9
    msg = w[..., None] * (hs + ee)                            # [E,H,dh]
    agg = jax.ops.segment_sum(msg, dst, n_nodes)              # [N,H,dh]
    return jax.nn.elu(agg.reshape(n_nodes, -1)) + h           # concat heads, residual


def forward_batched(P, Xv, Xe, Dg, src, dst, N, E):
    """Block-diagonal batch (PyG semantics): B graphs as one super-graph.
    Xv [B,N,d_v], Xe [B,E,d_e], Dg [B,E] -> predictions [B]."""
    B = Xv.shape[0]
    off = (jnp.arange(B) * N)[:, None]
    S = (src[None, :] + off).ravel()
    D = (dst[None, :] + off).ravel()
    h = jax.nn.elu(Xv.reshape(B * N, -1) @ P["enc_v"])
    e_in = jnp.concatenate([Xe, Dg[..., None]], -1).reshape(B * E, -1)
    e = jax.nn.elu(e_in @ P["enc_e"])
    for lp in P["layers"]:
        h = gat_layer(lp, h, e, S, D, B * N)
    gid_n = jnp.repeat(jnp.arange(B), N)
    gid_e = jnp.repeat(jnp.arange(B), E)
    g_mean = jax.ops.segment_sum(h, gid_n, B) / N
    dgf = Dg.ravel()
    w = dgf / (jax.ops.segment_sum(dgf, gid_e, B)[gid_e] + 1e-9)
    g_delta = jax.ops.segment_sum(w[:, None] * (h[S] + h[D]), gid_e, B)
    z = jax.nn.elu(jnp.concatenate([g_mean, g_delta], -1) @ P["head1"] + P["b1"])
    return (z @ P["head2"])[:, 0]


def train(XV, XE, DG, y, ei, tr, te, seed=0, epochs=400, lr=3e-3):
    """Full-batch Adam; Huber loss on standardized target. Returns test preds."""
    src, dst = jnp.array(ei[0]), jnp.array(ei[1])
    mu, sd = y[tr].mean(), y[tr].std() + 1e-9
    yt = jnp.array((y - mu) / sd)
    Xv, Xe, Dg = map(jnp.array, (XV, XE, DG))
    N, E = XV.shape[1], XE.shape[1]
    P = init_params(jax.random.PRNGKey(seed), XV.shape[-1], XE.shape[-1] + 1)
    batch_fwd = lambda p, a, b, c: forward_batched(p, a, b, c, src, dst, N, E)

    def loss(P, idx):
        pred = batch_fwd(P, Xv[idx], Xe[idx], Dg[idx])
        return optax.huber_loss(pred, yt[idx], delta=1.0).mean()

    opt = optax.adam(lr)
    tri = jnp.array(tr)

    @jax.jit
    def fit(P):
        st = opt.init(P)
        def body(_, carry):
            P, st = carry
            g = jax.grad(loss)(P, tri)
            up, st = opt.update(g, st)
            return optax.apply_updates(P, up), st
        P, _ = jax.lax.fori_loop(0, epochs, body, (P, st))
        return P
    P = fit(P)
    pred = np.array(batch_fwd(P, Xv[jnp.array(te)], Xe[jnp.array(te)],
                              Dg[jnp.array(te)])) * float(sd) + float(mu)
    return pred
