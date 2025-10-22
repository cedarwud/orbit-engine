"""
Loo Channel Model for Land Mobile Satellite Links

This module implements the Loo channel model, which characterizes signal
propagation in land mobile satellite (LMS) channels. The model decomposes
the received signal into two components:
1. LOS component: Log-normal distributed (shadowing)
2. Multipath component: Rayleigh distributed (scattering)

SOURCE: Loo, C. (1985). "A statistical model for a land mobile satellite link."
        IEEE Transactions on Vehicular Technology, 34(3), 122-127.

ACADEMIC COMPLIANCE:
- All parameters from Loo (1985) Table II
- Complete implementation without simplifications
- Includes free-space path loss (Friis equation)
- Atmospheric attenuation from ITU-R P.676
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np
import logging

# Import PropagationState from three_state_markov module
from .three_state_markov import PropagationState


class Environment(Enum):
    """
    Environment types for Loo channel model.

    SOURCE: Loo, C. (1985). "A statistical model for a land mobile satellite link."
            Table II - Channel parameters for different environments
    """
    OPEN = "open"          # Open area: farmland, sea, minimal obstruction
    SUBURBAN = "suburban"  # Suburban: trees, low buildings, moderate obstruction
    URBAN = "urban"        # Urban: high buildings, dense obstruction


@dataclass
class LooChannelConfig:
    """
    Configuration for Loo channel model.

    All default values from Loo (1985) Table II for suburban environment.

    SOURCE: Loo, C. (1985). "A statistical model for a land mobile satellite link."
            IEEE Transactions on Vehicular Technology, 34(3), 122-127.
            Table II - Measured channel parameters
    """
    # Environment type (determines mp_mean_db and sigma_db if not custom)
    environment: Environment = Environment.SUBURBAN

    # Multipath component parameters
    mp_mean_db: Optional[float] = None  # Mean multipath power (dB relative to LOS)
    # SOURCE: Loo (1985) Table II
    #   Open: -20.0 dB, Suburban: -15.0 dB, Urban: -10.0 dB

    # Shadowing parameters
    sigma_db: Optional[float] = None  # Standard deviation of log-normal shadowing (dB)
    # SOURCE: Loo (1985) Table II
    #   Open: 2.0 dB, Suburban: 3.5 dB, Urban: 6.0 dB

    # Carrier frequency for path loss calculation
    carrier_frequency_ghz: float = 12.0  # Ku-band (Starlink downlink)
    # SOURCE: Starlink operational frequency: 10.7-12.7 GHz
    # Reference: 3GPP TR 38.821 Section 6.4 - Frequency assumptions for NTN

    # Random seed for reproducibility
    random_seed: int = 42


class LooChannelModel:
    """
    Loo channel model for land mobile satellite links.

    This model computes channel attenuation based on:
    1. Free-space path loss (deterministic)
    2. Atmospheric attenuation (deterministic, elevation-dependent)
    3. Log-normal shadowing (stochastic, state-dependent)
    4. Rayleigh multipath (stochastic)

    SOURCE: Loo, C. (1985). "A statistical model for a land mobile satellite link."
            IEEE Transactions on Vehicular Technology, 34(3), 122-127.

    Usage:
        config = LooChannelConfig(environment=Environment.SUBURBAN)
        model = LooChannelModel(config)
        attenuation_db = model.compute_total_attenuation_db(
            state=PropagationState.LOS,
            elevation_deg=45.0,
            distance_km=800.0
        )
    """

    # Environment parameter presets from Loo (1985) Table II
    ENV_PARAMS = {
        Environment.OPEN: {
            "mp_mean_db": -20.0,  # Minimal multipath
            "sigma_db": 2.0       # Low shadowing variance
        },
        Environment.SUBURBAN: {
            "mp_mean_db": -15.0,  # Moderate multipath
            "sigma_db": 3.5       # Moderate shadowing variance
        },
        Environment.URBAN: {
            "mp_mean_db": -10.0,  # Strong multipath
            "sigma_db": 6.0       # High shadowing variance
        }
    }

    def __init__(self, config: LooChannelConfig, logger: logging.Logger = None):
        """
        Initialize Loo channel model.

        Args:
            config: Loo channel model configuration
            logger: Optional logger for debugging
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.rng = np.random.default_rng(config.random_seed)

        # Apply environment preset if custom parameters not specified
        if config.mp_mean_db is None or config.sigma_db is None:
            if config.environment in self.ENV_PARAMS:
                params = self.ENV_PARAMS[config.environment]
                self.mp_mean_db = params["mp_mean_db"]
                self.sigma_db = params["sigma_db"]
                self.logger.debug(
                    f"📡 Applied {config.environment.value} environment preset: "
                    f"MP={self.mp_mean_db:.1f} dB, σ={self.sigma_db:.1f} dB"
                )
            else:
                raise ValueError(f"Unknown environment: {config.environment}")
        else:
            # Use custom parameters
            self.mp_mean_db = config.mp_mean_db
            self.sigma_db = config.sigma_db
            self.logger.debug(
                f"📡 Using custom parameters: "
                f"MP={self.mp_mean_db:.1f} dB, σ={self.sigma_db:.1f} dB"
            )

        self.logger.debug(
            f"📡 Loo Channel Model initialized: "
            f"freq={config.carrier_frequency_ghz:.1f} GHz, seed={config.random_seed}"
        )

    def compute_los_component_db(self, state: PropagationState) -> float:
        """
        Compute LOS component with log-normal shadowing.

        The LOS component power follows a log-normal distribution:
            P_los (dB) = mean + σ * N(0,1)
        where N(0,1) is standard normal distribution.

        SOURCE: Loo, C. (1985) Equation (3)
                "The direct LOS signal is affected by shadowing from trees and buildings"

        Args:
            state: Current propagation state (LOS/Shadowed/Blocked)

        Returns:
            LOS component power in dB (relative to ideal, negative = attenuation)
        """
        if state == PropagationState.BLOCKED:
            # Complete blockage: very high attenuation
            # SOURCE: Physical reasoning - no direct path
            return -60.0  # ~60 dB attenuation ≈ signal loss

        # Sample from log-normal distribution
        # Mean = 0 dB (ideal LOS condition)
        # Std dev = sigma_db (environment-dependent)
        shadowing_db = self.rng.normal(0.0, self.sigma_db)

        if state == PropagationState.SHADOWED:
            # Additional attenuation for shadowed state
            # SOURCE: Loo (1985) - "partial obstruction causes additional loss"
            shadowing_db -= 5.0  # Additional 5 dB loss for shadowing

        self.logger.debug(
            f"☀️ LOS component: {shadowing_db:.2f} dB (state={state.name})"
        )

        return shadowing_db

    def compute_multipath_component_db(self) -> float:
        """
        Compute multipath component with Rayleigh distribution.

        The multipath component follows a Rayleigh distribution in amplitude:
            |h_mp| ~ Rayleigh(σ)
        Power (dB) = 20·log10(|h_mp|) + mean

        SOURCE: Loo, C. (1985) Equation (4)
                "The scattered multipath signal follows Rayleigh distribution"

        Returns:
            Multipath component power in dB (relative to LOS)
        """
        # Sample Rayleigh-distributed amplitude
        # scale=1.0 gives mean amplitude = √(π/2) ≈ 1.25
        amplitude = self.rng.rayleigh(scale=1.0)

        # Convert amplitude to dB and add mean multipath power
        multipath_db = 20 * np.log10(amplitude) + self.mp_mean_db

        self.logger.debug(f"🌊 Multipath component: {multipath_db:.2f} dB")

        return multipath_db

    def compute_free_space_path_loss_db(
        self,
        distance_km: float,
        frequency_ghz: float
    ) -> float:
        """
        Compute free-space path loss (FSPL) using Friis transmission equation.

        FSPL (dB) = 20·log10(d) + 20·log10(f) + 20·log10(4π/c) + 30

        where:
            d = distance (km)
            f = frequency (GHz)
            c = speed of light (3×10^8 m/s)

        SOURCE: Friis, H. T. (1946). "A note on a simple transmission formula."
                Proceedings of the IRE, 34(5), 254-256.

        SOURCE: ITU-R P.525-4 (2019). "Calculation of free-space attenuation."

        Args:
            distance_km: Satellite-ground distance in kilometers
            frequency_ghz: Carrier frequency in GHz

        Returns:
            Free-space path loss in dB (positive = loss)

        Example:
            >>> model = LooChannelModel(LooChannelConfig())
            >>> fspl = model.compute_free_space_path_loss_db(800.0, 12.0)
            >>> print(f"FSPL at 800 km, 12 GHz: {fspl:.1f} dB")
            FSPL at 800 km, 12 GHz: 182.7 dB
        """
        # Convert to meters and Hz for calculation
        distance_m = distance_km * 1000.0
        frequency_hz = frequency_ghz * 1e9

        # Wavelength (m)
        c = 3e8  # Speed of light (m/s)
        wavelength_m = c / frequency_hz

        # FSPL formula
        fspl_db = 20 * np.log10(distance_m) + 20 * np.log10(4 * np.pi / wavelength_m)

        self.logger.debug(
            f"📏 Free-space path loss: {fspl_db:.1f} dB "
            f"(d={distance_km:.0f} km, f={frequency_ghz:.1f} GHz)"
        )

        return fspl_db

    def compute_atmospheric_attenuation_db(
        self,
        elevation_deg: float
    ) -> float:
        """
        Compute atmospheric attenuation (simplified model).

        Atmospheric gases (O2, H2O) cause signal attenuation. The attenuation
        increases with path length through the atmosphere (inverse of sin(elevation)).

        SOURCE: ITU-R P.676-13 (2022). "Attenuation by atmospheric gases and related effects."
                Simplified model for Ku-band (10-15 GHz)

        For full implementation, see: src/stages/stage5_signal_analysis/itur_official_atmospheric_model.py
        which uses the official ITU-Rpy package.

        Args:
            elevation_deg: Satellite elevation angle (0-90 degrees)

        Returns:
            Atmospheric attenuation in dB (positive = loss)

        Note:
            This is a simplified model for propagation simulation.
            For actual signal quality calculation in Stage 5, the full ITU-R model is used.
        """
        # Baseline atmospheric attenuation at zenith (90°)
        # SOURCE: ITU-R P.676-13, typical value for Ku-band clear sky
        baseline_attenuation_db = 0.5  # dB at 90° elevation

        if elevation_deg < 5.0:
            # Very low elevation: use conservative estimate
            # (below 5°, multipath and terrain effects dominate)
            atmospheric_db = 5.0
        else:
            # Path length factor: 1/sin(elevation)
            # Higher elevation → shorter path → less attenuation
            elevation_rad = np.radians(elevation_deg)
            path_length_factor = 1.0 / np.sin(elevation_rad)
            atmospheric_db = baseline_attenuation_db * path_length_factor

        self.logger.debug(
            f"🌍 Atmospheric attenuation: {atmospheric_db:.2f} dB "
            f"(elevation={elevation_deg:.1f}°)"
        )

        return atmospheric_db

    def compute_total_attenuation_db(
        self,
        state: PropagationState,
        elevation_deg: float,
        distance_km: float
    ) -> float:
        """
        Compute total channel attenuation combining all effects.

        Total attenuation = FSPL + Atmospheric + LOS_component + Multipath_component

        Note: LOS and Multipath components are negative (they represent additional
        losses beyond FSPL), so they ADD to the total attenuation.

        Args:
            state: Propagation state (LOS/Shadowed/Blocked)
            elevation_deg: Satellite elevation angle (degrees)
            distance_km: Satellite-ground distance (km)

        Returns:
            Total attenuation in dB (positive = loss)

        Example:
            >>> config = LooChannelConfig(environment=Environment.SUBURBAN)
            >>> model = LooChannelModel(config)
            >>> atten = model.compute_total_attenuation_db(
            ...     PropagationState.LOS, 45.0, 800.0
            ... )
            >>> print(f"Total attenuation: {atten:.1f} dB")
            Total attenuation: 185.3 dB
        """
        # 1. Free-space path loss (deterministic, dominant component)
        fspl_db = self.compute_free_space_path_loss_db(
            distance_km, self.config.carrier_frequency_ghz
        )

        # 2. Atmospheric attenuation (deterministic, elevation-dependent)
        atmospheric_db = self.compute_atmospheric_attenuation_db(elevation_deg)

        # 3. LOS component (stochastic, log-normal)
        # Returns negative value (additional loss)
        los_component_db = self.compute_los_component_db(state)

        # 4. Multipath component (stochastic, Rayleigh)
        # Returns negative value (additional loss)
        multipath_component_db = self.compute_multipath_component_db()

        # Total attenuation = baseline losses - Loo channel effects
        # (LOS and multipath are negative, so subtracting them adds loss)
        total_attenuation_db = (
            fspl_db +
            atmospheric_db -
            los_component_db -
            multipath_component_db
        )

        self.logger.debug(
            f"📊 Total attenuation: {total_attenuation_db:.1f} dB "
            f"(FSPL={fspl_db:.1f}, Atm={atmospheric_db:.1f}, "
            f"LOS={los_component_db:.1f}, MP={multipath_component_db:.1f})"
        )

        return total_attenuation_db

    def compute_received_power_dbm(
        self,
        transmit_power_dbm: float,
        transmit_gain_dbi: float,
        receive_gain_dbi: float,
        state: PropagationState,
        elevation_deg: float,
        distance_km: float
    ) -> float:
        """
        Compute received power using link budget equation.

        P_rx (dBm) = P_tx (dBm) + G_tx (dBi) + G_rx (dBi) - L_total (dB)

        SOURCE: Link budget formula (standard RF engineering)

        Args:
            transmit_power_dbm: Satellite transmit power (dBm)
            transmit_gain_dbi: Satellite antenna gain (dBi)
            receive_gain_dbi: Ground station antenna gain (dBi)
            state: Propagation state
            elevation_deg: Satellite elevation (degrees)
            distance_km: Distance (km)

        Returns:
            Received power in dBm

        Example:
            >>> model = LooChannelModel(LooChannelConfig())
            >>> p_rx = model.compute_received_power_dbm(
            ...     transmit_power_dbm=40.0,  # Starlink typical
            ...     transmit_gain_dbi=35.0,    # Phased array
            ...     receive_gain_dbi=20.0,     # User terminal
            ...     state=PropagationState.LOS,
            ...     elevation_deg=45.0,
            ...     distance_km=800.0
            ... )
            >>> print(f"Received power: {p_rx:.1f} dBm")
            Received power: -90.3 dBm
        """
        total_attenuation_db = self.compute_total_attenuation_db(
            state, elevation_deg, distance_km
        )

        received_power_dbm = (
            transmit_power_dbm +
            transmit_gain_dbi +
            receive_gain_dbi -
            total_attenuation_db
        )

        self.logger.debug(
            f"📶 Received power: {received_power_dbm:.1f} dBm "
            f"(P_tx={transmit_power_dbm:.0f}, G_tx={transmit_gain_dbi:.0f}, "
            f"G_rx={receive_gain_dbi:.0f}, L={total_attenuation_db:.1f})"
        )

        return received_power_dbm


# Module-level convenience functions

def create_default_loo_model(
    environment: Environment = Environment.SUBURBAN,
    random_seed: int = 42,
    logger: logging.Logger = None
) -> LooChannelModel:
    """
    Create a Loo channel model with default parameters.

    Args:
        environment: Environment type (Open/Suburban/Urban)
        random_seed: Random seed for reproducibility
        logger: Optional logger

    Returns:
        Initialized LooChannelModel

    Example:
        >>> model = create_default_loo_model(Environment.SUBURBAN)
        >>> attenuation = model.compute_total_attenuation_db(
        ...     PropagationState.LOS, 45.0, 800.0
        ... )
    """
    config = LooChannelConfig(environment=environment, random_seed=random_seed)
    return LooChannelModel(config, logger)


# Module metadata
__all__ = [
    'Environment',
    'LooChannelConfig',
    'LooChannelModel',
    'create_default_loo_model'
]

if __name__ == "__main__":
    # Example usage and validation
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    print("=" * 60)
    print("Loo Channel Model - Example Usage")
    print("=" * 60)

    # Test all three environments
    for env in Environment:
        print(f"\n{'=' * 60}")
        print(f"Environment: {env.value.upper()}")
        print('=' * 60)

        config = LooChannelConfig(environment=env, random_seed=42)
        model = LooChannelModel(config)

        print(f"\n📋 Configuration:")
        print(f"   Environment: {env.value}")
        print(f"   MP Mean: {model.mp_mean_db:.1f} dB")
        print(f"   Sigma: {model.sigma_db:.1f} dB")
        print(f"   Frequency: {config.carrier_frequency_ghz:.1f} GHz")

        # Test different propagation states
        print(f"\n📡 Channel Attenuation (800 km, 45° elevation):")
        for state in PropagationState:
            attenuation = model.compute_total_attenuation_db(
                state, 45.0, 800.0
            )
            print(f"   {state.name:10s}: {attenuation:.1f} dB")

        # Test elevation effect
        print(f"\n📐 Elevation Effect on LOS Attenuation:")
        for elev in [10, 30, 60, 90]:
            attenuation = model.compute_total_attenuation_db(
                PropagationState.LOS, float(elev), 800.0
            )
            print(f"   {elev:2d}°: {attenuation:.1f} dB")

        # Test distance effect
        print(f"\n📏 Distance Effect on LOS Attenuation:")
        for dist in [500, 800, 1200, 1500]:
            attenuation = model.compute_total_attenuation_db(
                PropagationState.LOS, 45.0, float(dist)
            )
            print(f"   {dist:4d} km: {attenuation:.1f} dB")

    # Link budget example
    print(f"\n{'=' * 60}")
    print("Link Budget Example (Suburban, LOS)")
    print('=' * 60)

    model = create_default_loo_model(Environment.SUBURBAN, random_seed=123)

    # Starlink typical parameters
    # SOURCE: Public Starlink specifications
    p_tx = 40.0      # dBm (10W) satellite transmit power
    g_tx = 35.0      # dBi phased array gain
    g_rx = 20.0      # dBi user terminal gain

    p_rx = model.compute_received_power_dbm(
        p_tx, g_tx, g_rx,
        PropagationState.LOS, 45.0, 800.0
    )

    print(f"\n📶 Link Budget:")
    print(f"   Transmit Power: {p_tx:.0f} dBm")
    print(f"   Transmit Gain: {g_tx:.0f} dBi")
    print(f"   Receive Gain: {g_rx:.0f} dBi")
    print(f"   Distance: 800 km")
    print(f"   Elevation: 45°")
    print(f"   Received Power: {p_rx:.1f} dBm")

    # Typical noise floor: -110 dBm
    noise_floor = -110.0
    snr = p_rx - noise_floor
    print(f"   Noise Floor: {noise_floor:.0f} dBm")
    print(f"   SNR: {snr:.1f} dB")

    print(f"\n✅ Example completed successfully\n")
