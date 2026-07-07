"""rdt_core.bocpd — Bayesian Online Change Point Detection (Eq. 2.14–2.15).

Adams & MacKay (2007) recursion with constant hazard H = 1/lambda_h, per-channel
Normal-Inverse-Gamma conjugate model (Student-t predictive), channels combined as
independent log-likelihoods. Trigger (Eq. 2.15):
    P(disruption at t) = sum_{r_t <= r_min} P(r_t | x_1:t) > threshold
Run-length support pruned at R_MAX with renormalization (standard practice).
All observations are z-scored against a nominal calibration window so channel
scales don't dominate the joint likelihood.
"""
from __future__ import annotations
import numpy as np
from scipy.special import gammaln


class BOCPD:
    def __init__(self, n_channels: int, lam: float = 500.0, r_max: int = 200,
                 mu0: float = 0.0, kappa0: float = 1.0,
                 alpha0: float = 1.0, beta0: float = 1.0):
        self.C, self.lam, self.r_max = n_channels, lam, r_max
        self.mu0, self.k0, self.a0, self.b0 = mu0, kappa0, alpha0, beta0
        self.reset()

    def reset(self):
        self.R = np.array([1.0])                    # P(r_0 = 0) = 1
        C = self.C
        self.mu = np.full((1, C), self.mu0)
        self.k = np.full((1, C), self.k0)
        self.a = np.full((1, C), self.a0)
        self.b = np.full((1, C), self.b0)

    def _pred_loglik(self, x):
        """Student-t predictive per run-length hypothesis, summed over channels."""
        df = 2 * self.a
        scale2 = self.b * (self.k + 1) / (self.a * self.k)
        z2 = (x[None, :] - self.mu) ** 2 / scale2
        ll = (gammaln((df + 1) / 2) - gammaln(df / 2)
              - 0.5 * np.log(np.pi * df * scale2)
              - (df + 1) / 2 * np.log1p(z2 / df))
        return ll.sum(axis=1)                       # [n_r]

    def update(self, x: np.ndarray) -> np.ndarray:
        """One observation vector x [C]. Returns run-length posterior P(r_t|x_1:t)."""
        ll = self._pred_loglik(x)
        pred = np.exp(ll - ll.max())
        h = 1.0 / self.lam
        growth = self.R * pred * (1 - h)            # r -> r+1
        cp = (self.R * pred * h).sum()              # r -> 0
        R_new = np.concatenate([[cp], growth])
        R_new /= R_new.sum() + 1e-300

        # posterior parameter update (NIG conjugacy), prepend fresh prior for r=0
        mu_n = (self.k * self.mu + x[None, :]) / (self.k + 1)
        k_n = self.k + 1
        a_n = self.a + 0.5
        b_n = self.b + 0.5 * self.k * (x[None, :] - self.mu) ** 2 / (self.k + 1)
        C = self.C
        self.mu = np.vstack([np.full((1, C), self.mu0), mu_n])
        self.k = np.vstack([np.full((1, C), self.k0), k_n])
        self.a = np.vstack([np.full((1, C), self.a0), a_n])
        self.b = np.vstack([np.full((1, C), self.b0), b_n])

        if len(R_new) > self.r_max:                 # prune tail, renormalize
            R_new = R_new[:self.r_max]
            R_new /= R_new.sum()
            self.mu, self.k = self.mu[:self.r_max], self.k[:self.r_max]
            self.a, self.b = self.a[:self.r_max], self.b[:self.r_max]
        self.R = R_new
        return R_new

    def p_disruption(self, r_min: int = 4) -> float:
        """Eq. 2.15: posterior mass on short run lengths."""
        return float(self.R[:r_min + 1].sum())


def cusum_alarms(obs: np.ndarray, k: float = 0.5, h: float = 8.0,
                 burn_in: int = 48) -> list[int]:
    """Two-sided tabular CUSUM per channel on z-scored obs; alarm when any
    channel statistic exceeds h. Complements BOCPD: run-length triggers catch
    steps, CUSUM catches slow drifts (D1/D8 ramp class, finding 2026-07-03)."""
    T, C = obs.shape
    sp = np.zeros(C); sn = np.zeros(C)
    alarms, last = [], -10**9
    for t in range(T):
        sp = np.maximum(0, sp + obs[t] - k)
        sn = np.maximum(0, sn - obs[t] - k)
        if t >= burn_in and max(sp.max(), sn.max()) > h:
            if t - last > 4:
                alarms.append(t)
            sp[:] = 0; sn[:] = 0
            last = t
    return alarms


def detect(obs: np.ndarray, threshold: float = 0.85, r_min: int = 4,
           burn_in: int = 48, lam: float = 500.0,
           fuse_cusum: bool = True, cusum_h: float = 8.0) -> list[int]:
    """Hybrid detector: BOCPD run-length trigger OR CUSUM drift trigger.
    Returns merged alarm step indices."""
    d = BOCPD(obs.shape[1], lam=lam)
    alarms, last = [], -10**9
    for t in range(obs.shape[0]):
        d.update(obs[t])
        if t >= burn_in and d.p_disruption(r_min) > threshold:
            if t - last > r_min:
                alarms.append(t)
            last = t
    if fuse_cusum:
        merged = sorted(set(alarms) | set(cusum_alarms(obs, h=cusum_h, burn_in=burn_in)))
        out, last = [], -10**9
        for a in merged:
            if a - last > r_min:
                out.append(a)
            last = a
        return out
    return alarms
