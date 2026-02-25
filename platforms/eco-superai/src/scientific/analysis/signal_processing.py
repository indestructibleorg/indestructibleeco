"""Signal processing - FFT/IFFT analysis."""
from __future__ import annotations
from typing import Any
import numpy as np


class SignalProcessor:
    def fft(self, signal: list[float], sample_rate: float, inverse: bool = False) -> dict[str, Any]:
        s = np.array(signal)
        try:
            if inverse:
                result = np.fft.ifft(s)
                return {"operation": "ifft", "result_real": np.real(result).tolist(), "result_imag": np.imag(result).tolist(), "length": len(result)}
            fft_result = np.fft.fft(s)
            n = len(s)
            freqs = np.fft.fftfreq(n, d=1.0 / sample_rate)
            magnitudes = np.abs(fft_result)
            phases = np.angle(fft_result)
            power = magnitudes ** 2
            half = n // 2
            dominant_idx = np.argmax(magnitudes[1:half]) + 1
            return {
                "operation": "fft",
                "frequencies": freqs[:half].tolist(),
                "magnitudes": magnitudes[:half].tolist(),
                "phases": phases[:half].tolist(),
                "power_spectrum": power[:half].tolist(),
                "dominant_frequency": float(freqs[dominant_idx]),
                "dominant_magnitude": float(magnitudes[dominant_idx]),
                "nyquist_frequency": sample_rate / 2,
                "frequency_resolution": sample_rate / n,
                "signal_length": n,
            }
        except Exception as e:
            return {"error": str(e)}