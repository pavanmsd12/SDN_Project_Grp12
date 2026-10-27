"""
Conformal Uncertainty Calibration & Wasserstein Ambiguity Radius:
Implements split conformal prediction and fidelity-calibrated expansion of the uncertainty set.
"""

import numpy as np

class ConformalCalibrator:
    def __init__(self, alpha_conf=0.10, beta_phi=1.5, beta_e=0.8, eps_0=0.05):
        self.alpha_conf = alpha_conf  # 1 - coverage level (e.g., 90% coverage)
        self.beta_phi = beta_phi      # fidelity scaling factor (Eq. 20)
        self.beta_e = beta_e          # rolling error scaling factor
        self.eps_0 = eps_0            # baseline nominal ambiguity radius
        self.error_history = []

    def calibrate_interval(self, q_low, q_high, phi_e):
        """
        Calibrates predicted quantile interval [q_low, q_high] using link fidelity phi_e.
        Lower fidelity (phi_e < 1) inflates the uncertainty interval proportionally:
        interval_width = (q_high - q_low) * [1 + beta_phi * (1 - phi_e)]
        """
        nominal_half_width = (q_high - q_low) / 2.0
        inflated_half_width = nominal_half_width * (1.0 + self.beta_phi * (1.0 - phi_e))
        center = (q_high + q_low) / 2.0

        calibrated_low = np.maximum(0.0, center - inflated_half_width)
        calibrated_high = center + inflated_half_width
        return calibrated_low, calibrated_high

    def update_error(self, y_true, y_pred):
        """Updates rolling prediction error e_bar(t)."""
        rel_err = float(np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + 1e-4)))
        self.error_history.append(rel_err)
        if len(self.error_history) > 10:
            self.error_history.pop(0)

    def get_rolling_error(self):
        if not self.error_history:
            return 0.05
        return float(np.mean(self.error_history))

    def compute_wasserstein_radius(self, global_fidelity):
        """
        Computes dynamic Wasserstein ambiguity radius (Eq. 20 in PDF):
        epsilon_t = epsilon_0 + beta_phi * (1 - Phi(t)) + beta_e * e_bar(t)
        """
        e_bar = self.get_rolling_error()
        eps_t = self.eps_0 + self.beta_phi * (1.0 - global_fidelity) + self.beta_e * e_bar
        return float(eps_t)
