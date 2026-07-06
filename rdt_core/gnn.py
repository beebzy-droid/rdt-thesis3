"""rdt_core.gnn — Edge-featured GATv2 (Brody et al. 2022 attention form) in JAX.

PROTOTYPE NOTE (§9.2 transparency): implemented in JAX because the sandbox cannot
carry the 532 MB torch wheel + CUDA dependency chain; the production PyTorch
Geometric port (lifecycle §6.1) runs on reference hardware with an equivalence
test against this implementation. Architecture is dataset-v0-sized (2 layers,
4 heads, dim 32) — the §2.2.1 4/8/128 configuration is for the 50k library and
enters via the Phase 2 depth/width ablation, not by default.

Layer (GATv2, edge-conditioned):
    s_ij = a_k^T · LeakyReLU( W_s h_i + W_t h_j + W_e e_ij )        per head k
    α_ij = softmax over in-edges of node j
    h_j' = ELU( ||_k Σ_i α_ij^k · ( W_v^k h_i + W_u^k e_ij ) )
Prediction head (ΔG-conditioned):
    z_e  = MLP([h_u, h_v, e_e])            edge embedding after L layers
    ŷ    = MLP([ mean_v h_v , Σ_e ΔG_e·z_e , Σ_e ΔG_e ])
"""
from __future__ import annotations
import numpy as np
import jax
import jax.numpy as jnp
import optax
from functools import partial

HEADS, DIM, LAYERS = 4, 32, 2
LRELU = 0.2


def _glorot(key, shape):
    lim = float(np.sqrt(6.0 / (shape[-2] + shape[-1])))
    return jax.random.uniform(key, shape, minval=-lim, maxval=lim)


def init_params(key, d_v, d_e):
    ks = jax.random.split(key, 32); k = iter(ks)
    p = {"enc_v": _glorot(next(k), (d_v, DIM)), "enc_e": _glorot(next(k), (d_e, DIM))}
    for l in range(LAYERS):
        p[f"L{l}"] = {
            "Ws": _glorot(next(k), (HEADS, DIM, DIM)), "Wt": _glorot(next(k), (HEADS, DIM, DIM)),
            "We": _glorot(next(k), (HEADS, DIM, DIM)), "Wv": _glorot(next(k), (HEADS, DIM, DIM)),
            "Wu": _glorot(next(k), (HEADS, DIM, DIM)), "a": _glorot(next(k), (HEADS, DIM, 1)),
            "proj": _glorot(next(k), (HEADS * DIM, DIM)),
        }
    p["edge_mlp"] = [_glorot(next(k), (3 * DIM, DIM)), _glorot(next(k), (DIM, DIM))]
    p["head"] = [_glorot(next(k), (2 * DIM + 1, DIM)), _glorot(next(k), (DIM, 1))]
    return p


def _layer(lp, h, e, src, dst, n_nodes):
    hs = jnp.einsum("kio,ni->kno", lp["Ws"], h)[:, src]        # [H,E,D]
    ht = jnp.einsum("kio,ni->kno", lp["Wt"], h)[:, dst]
    he = jnp.einsum("kio,ei->keo", lp["We"], e)
    s = jax.nn.leaky_relu(hs + ht + he, LRELU)
    logit = jnp.einsum("keo,ko1->ke", s, lp["a"])              # GATv2: a after nonlin
    lmax = jax.ops.segment_max(logit.T, dst, n_nodes)[dst].T   # stable softmax per dst
    ex = jnp.exp(logit - lmax)
    den = jax.ops.segment_sum(ex.T, dst, n_nodes)[dst].T + 1e-12
    alpha = ex / den                                            # [H,E]
    msg = (jnp.einsum("kio,ni->kno", lp["Wv"], h)[:, src]
           + jnp.einsum("kio,ei->keo", lp["Wu"], e)) * alpha[..., None]
    agg = jax.vmap(lambda m: jax.ops.segment_sum(m, dst, n_nodes))(msg)  # [H,N,D]
    cat = jnp.transpose(agg, (1, 0, 2)).reshape(n_nodes, HEADS * DIM)
    return jax.nn.elu(cat @ lp["proj"]) + h                    # residual


def forward(p, Xv, Xe, dG, src, dst):
    """Single graph: Xv [N,d_v], Xe [E,d_e], dG [E] -> scalar prediction."""
    n = Xv.shape[0]
    h = jax.nn.elu(Xv @ p["enc_v"])
    e = jax.nn.elu(Xe @ p["enc_e"])
    for l in range(LAYERS):
        h = _layer(p[f"L{l}"], h, e, src, dst, n)
    z = jnp.concatenate([h[src], h[dst], e], axis=1)
    z = jax.nn.elu(jax.nn.elu(z @ p["edge_mlp"][0]) @ p["edge_mlp"][1])   # [E,D]
    pooled = jnp.concatenate([h.mean(0), (dG[:, None] * z).sum(0),
                              jnp.array([dG.sum()])])
    return (jax.nn.elu(pooled @ p["head"][0]) @ p["head"][1])[0]


batched_forward = jax.vmap(forward, in_axes=(None, 0, 0, 0, None, None))


def huber(res, d=0.05):
    a = jnp.abs(res)
    return jnp.where(a <= d, 0.5 * res**2, d * (a - 0.5 * d)).mean()


@partial(jax.jit, static_argnums=())
def _noop(x):  # placeholder to keep jit imports explicit
    return x


def train(Xv, Xe, dG, y, src, dst, tr, va, seed=0, steps=2500, lr=3e-3,
          patience=300):
    """Full-batch Adam with early stopping on validation loss. Returns best params."""
    key = jax.random.PRNGKey(seed)
    p = init_params(key, Xv.shape[-1], Xe.shape[-1])
    opt = optax.adam(lr)
    st = opt.init(p)
    Xv_, Xe_, dG_, y_ = (jnp.array(a) for a in (Xv, Xe, dG, y))
    src_, dst_ = jnp.array(src), jnp.array(dst)

    @jax.jit
    def step(p, st):
        def loss(p):
            pred = batched_forward(p, Xv_[tr], Xe_[tr], dG_[tr], src_, dst_)
            return huber(pred - y_[tr])
        l, g = jax.value_and_grad(loss)(p)
        up, st = opt.update(g, st)
        return optax.apply_updates(p, up), st, l

    @jax.jit
    def vloss(p):
        pred = batched_forward(p, Xv_[va], Xe_[va], dG_[va], src_, dst_)
        return huber(pred - y_[va])

    best, best_v, since = p, np.inf, 0
    for i in range(steps):
        p, st, _ = step(p, st)
        if i % 25 == 0:
            v = float(vloss(p))
            if v < best_v - 1e-6:
                best, best_v, since = p, v, 0
            else:
                since += 25
                if since >= patience:
                    break
    return best


def predict(p, Xv, Xe, dG, src, dst):
    return np.array(batched_forward(p, jnp.array(Xv), jnp.array(Xe),
                                    jnp.array(dG), jnp.array(src), jnp.array(dst)))
