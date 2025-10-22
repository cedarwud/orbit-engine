"""
Propagation Condition Simulator for Stage 5

This module integrates the Three-State Markov Model and Loo Channel Model
to simulate dynamic propagation conditions for satellite-ground links.

For each satellite at each time step, it:
1. Simulates Markov state transition (LOS/Shadowed/Blocked)
2. Computes channel attenuation using Loo model
3. Tracks state history for each satellite
4. Generates complete propagation condition data

SOURCE: Combining methodologies from:
        - 3GPP TR 38.901 (Three-state Markov)
        - Loo (1985) (Channel model)

ACADEMIC COMPLIANCE:
- No simplified algorithms
- All parameters traceable to official sources
- Complete implementation of both models
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import logging

from .three_state_markov import (
    ThreeStateMarkovModel,
    MarkovConfig,
    PropagationState
)
from .loo_channel import (
    LooChannelModel,
    LooChannelConfig,
    Environment
)


@dataclass
class PropagationResult:
    """
    Complete propagation condition result for a single satellite link.

    This dataclass contains all information about the propagation conditions
    at a specific time step.
    """
    # Identifiers
    satellite_id: str
    timestamp: str

    # Markov state
    propagation_state: str  # "LOS" | "Shadowed" | "Blocked"
    state_probabilities: Dict[str, float]  # Steady-state distribution

    # Loo channel attenuation
    channel_attenuation_db: float  # Total attenuation
    los_component_db: float        # LOS component (log-normal)
    multipath_component_db: float  # Multipath component (Rayleigh)

    # Link geometry
    elevation_deg: float
    distance_km: float

    # Configuration
    environment: str  # "open" | "suburban" | "urban"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PropagationConditionSimulator:
    """
    Main controller that integrates Markov model and Loo channel model.

    This simulator manages the dynamic propagation conditions for all satellites
    over time, maintaining state continuity and generating comprehensive
    propagation data.

    Usage:
        config = {
            'markov_model': {...},
            'loo_channel': {...}
        }
        simulator = PropagationConditionSimulator(config, logger)

        result = simulator.simulate(
            satellite_id="46061",
            timestamp="2025-10-22T01:53:00Z",
            elevation_deg=45.0,
            distance_km=800.0
        )
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize propagation condition simulator.

        Args:
            config: Configuration dictionary with 'markov_model' and 'loo_channel' sections
            logger: Logger instance for debugging and monitoring
        """
        self.config = config
        self.logger = logger

        # Initialize Markov model
        markov_config_dict = config.get('markov_model', {})
        markov_config = MarkovConfig(**markov_config_dict)
        self.markov_model = ThreeStateMarkovModel(markov_config, logger)

        self.logger.info("🔀 Markov model initialized")

        # Initialize Loo channel model
        loo_config_dict = config.get('loo_channel', {})

        # Handle environment enum conversion
        if 'environment' in loo_config_dict:
            env_str = loo_config_dict['environment']
            if isinstance(env_str, str):
                loo_config_dict['environment'] = Environment(env_str)

        loo_config = LooChannelConfig(**loo_config_dict)
        self.loo_model = LooChannelModel(loo_config, logger)

        self.logger.info(
            f"📡 Loo channel model initialized: "
            f"environment={loo_config.environment.value}"
        )

        # State tracking: satellite_id -> current_state
        self.current_states: Dict[str, PropagationState] = {}

        # Initial state setting
        initial_state_str = config.get('initial_state', 'LOS')
        self.initial_state = PropagationState[initial_state_str.upper()]

        self.logger.info(
            f"✅ PropagationConditionSimulator initialized "
            f"(initial_state={self.initial_state.name})"
        )

    def get_or_initialize_state(self, satellite_id: str) -> PropagationState:
        """
        Get current state for satellite, or initialize if first observation.

        Args:
            satellite_id: Satellite identifier

        Returns:
            Current propagation state
        """
        if satellite_id not in self.current_states:
            # First observation: use initial state
            self.current_states[satellite_id] = self.initial_state
            self.logger.debug(
                f"🆕 Initialized state for {satellite_id}: {self.initial_state.name}"
            )

        return self.current_states[satellite_id]

    def simulate(
        self,
        satellite_id: str,
        timestamp: str,
        elevation_deg: float,
        distance_km: float
    ) -> PropagationResult:
        """
        Simulate propagation conditions for a single satellite link.

        This is the main entry point for generating propagation condition data.
        It performs the following steps:
        1. Get or initialize current state
        2. Simulate next state using Markov model
        3. Compute channel attenuation using Loo model
        4. Calculate steady-state distribution
        5. Package results

        Args:
            satellite_id: Satellite identifier (e.g., "46061")
            timestamp: ISO 8601 timestamp (e.g., "2025-10-22T01:53:00+00:00")
            elevation_deg: Satellite elevation angle (0-90 degrees)
            distance_km: Satellite-ground distance (kilometers)

        Returns:
            PropagationResult containing complete propagation condition data

        Example:
            >>> simulator = PropagationConditionSimulator(config, logger)
            >>> result = simulator.simulate("46061", "2025-10-22T01:53:00Z", 45.0, 800.0)
            >>> print(f"State: {result.propagation_state}, Attenuation: {result.channel_attenuation_db:.1f} dB")
            State: LOS, Attenuation: 145.3 dB
        """
        # Step 1: Get current state
        current_state = self.get_or_initialize_state(satellite_id)

        # Step 2: Simulate next state using Markov model
        next_state = self.markov_model.simulate_next_state(
            current_state, elevation_deg
        )

        # Update state tracking
        self.current_states[satellite_id] = next_state

        # Step 3: Compute steady-state distribution
        pi = self.markov_model.get_steady_state_distribution(elevation_deg)
        state_probabilities = {
            "LOS": float(pi[0]),
            "Shadowed": float(pi[1]),
            "Blocked": float(pi[2])
        }

        # Step 4: Compute channel attenuation using Loo model
        total_attenuation_db = self.loo_model.compute_total_attenuation_db(
            next_state, elevation_deg, distance_km
        )

        # Get individual components for detailed analysis
        los_component_db = self.loo_model.compute_los_component_db(next_state)
        multipath_component_db = self.loo_model.compute_multipath_component_db()

        # Step 5: Package results
        result = PropagationResult(
            satellite_id=satellite_id,
            timestamp=timestamp,
            propagation_state=next_state.name,
            state_probabilities=state_probabilities,
            channel_attenuation_db=float(total_attenuation_db),
            los_component_db=float(los_component_db),
            multipath_component_db=float(multipath_component_db),
            elevation_deg=float(elevation_deg),
            distance_km=float(distance_km),
            environment=self.loo_model.config.environment.value
        )

        self.logger.debug(
            f"📡 {satellite_id} @ {timestamp}: "
            f"State={next_state.name}, "
            f"Elevation={elevation_deg:.1f}°, "
            f"Attenuation={total_attenuation_db:.1f} dB"
        )

        return result

    def reset_state(self, satellite_id: Optional[str] = None) -> None:
        """
        Reset state tracking for one or all satellites.

        This is useful when starting a new simulation run or when a satellite
        leaves and re-enters visibility.

        Args:
            satellite_id: Specific satellite to reset, or None to reset all
        """
        if satellite_id is None:
            # Reset all satellites
            count = len(self.current_states)
            self.current_states.clear()
            self.logger.info(f"🔄 Reset all satellite states ({count} satellites)")
        else:
            # Reset specific satellite
            if satellite_id in self.current_states:
                del self.current_states[satellite_id]
                self.logger.debug(f"🔄 Reset state for {satellite_id}")

    def get_state_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current propagation states.

        Returns:
            Dictionary with state distribution statistics

        Example:
            >>> stats = simulator.get_state_statistics()
            >>> print(f"LOS: {stats['state_counts']['LOS']} satellites")
            LOS: 65 satellites
        """
        if not self.current_states:
            return {
                "total_satellites": 0,
                "state_counts": {"LOS": 0, "Shadowed": 0, "Blocked": 0},
                "state_percentages": {"LOS": 0.0, "Shadowed": 0.0, "Blocked": 0.0}
            }

        # Count states
        state_counts = {
            "LOS": 0,
            "Shadowed": 0,
            "Blocked": 0
        }

        for state in self.current_states.values():
            state_counts[state.name] += 1

        total = len(self.current_states)

        # Calculate percentages
        state_percentages = {
            name: (count / total) * 100.0
            for name, count in state_counts.items()
        }

        return {
            "total_satellites": total,
            "state_counts": state_counts,
            "state_percentages": state_percentages
        }


def create_default_simulator(
    environment: Environment = Environment.SUBURBAN,
    random_seed: int = 42,
    logger: logging.Logger = None
) -> PropagationConditionSimulator:
    """
    Create a propagation simulator with default parameters.

    This is a convenience function for quick initialization.

    Args:
        environment: Environment type (Open/Suburban/Urban)
        random_seed: Random seed for reproducibility
        logger: Optional logger

    Returns:
        Initialized PropagationConditionSimulator

    Example:
        >>> simulator = create_default_simulator(Environment.SUBURBAN, 42)
        >>> result = simulator.simulate("46061", "2025-10-22T01:53:00Z", 45.0, 800.0)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    config = {
        'markov_model': {
            'random_seed': random_seed,
            'elevation_adjustment_enabled': True
        },
        'loo_channel': {
            'environment': environment.value,
            'carrier_frequency_ghz': 12.0,  # Ku-band (Starlink)
            'random_seed': random_seed
        },
        'initial_state': 'LOS'
    }

    return PropagationConditionSimulator(config, logger)


# Module metadata
__all__ = [
    'PropagationResult',
    'PropagationConditionSimulator',
    'create_default_simulator'
]


if __name__ == "__main__":
    # Example usage and validation
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    print("=" * 70)
    print("PropagationConditionSimulator - Example Usage")
    print("=" * 70)

    # Create simulator with default settings
    simulator = create_default_simulator(
        environment=Environment.SUBURBAN,
        random_seed=42
    )

    print("\n📋 Configuration:")
    print(f"   Environment: {simulator.loo_model.config.environment.value}")
    print(f"   MP Mean: {simulator.loo_model.mp_mean_db:.1f} dB")
    print(f"   Sigma: {simulator.loo_model.sigma_db:.1f} dB")
    print(f"   Initial State: {simulator.initial_state.name}")

    # Simulate a satellite link over multiple time steps
    print("\n🛰️  Simulating satellite 46061 over 10 time steps:")
    print("-" * 70)

    satellite_id = "46061"
    base_time = "2025-10-22T01:53:"
    elevation = 45.0
    distance = 800.0

    results = []

    for i in range(10):
        timestamp = f"{base_time}{i:02d}+00:00"

        result = simulator.simulate(
            satellite_id=satellite_id,
            timestamp=timestamp,
            elevation_deg=elevation,
            distance_km=distance
        )

        results.append(result)

        print(f"   Step {i+1:2d} | {result.timestamp} | "
              f"State: {result.propagation_state:10s} | "
              f"Attenuation: {result.channel_attenuation_db:6.1f} dB | "
              f"LOS: {result.los_component_db:6.2f} dB")

    # State statistics
    print("\n📊 State Distribution:")
    state_count = {}
    for result in results:
        state = result.propagation_state
        state_count[state] = state_count.get(state, 0) + 1

    for state, count in state_count.items():
        percentage = (count / len(results)) * 100
        print(f"   {state:10s}: {count:2d}/10 = {percentage:5.1f}%")

    # Steady-state distribution (theoretical)
    print("\n📈 Theoretical Steady-State (elevation=45°):")
    pi = simulator.markov_model.get_steady_state_distribution(elevation)
    print(f"   LOS:      {pi[0]:.1%}")
    print(f"   Shadowed: {pi[1]:.1%}")
    print(f"   Blocked:  {pi[2]:.1%}")

    # Attenuation statistics
    print("\n📉 Attenuation Statistics:")
    attenuations = [r.channel_attenuation_db for r in results]
    import statistics
    print(f"   Mean:   {statistics.mean(attenuations):.1f} dB")
    print(f"   Std:    {statistics.stdev(attenuations):.1f} dB")
    print(f"   Min:    {min(attenuations):.1f} dB")
    print(f"   Max:    {max(attenuations):.1f} dB")

    # Simulator state statistics
    print("\n🔍 Simulator State Statistics:")
    stats = simulator.get_state_statistics()
    print(f"   Total satellites tracked: {stats['total_satellites']}")
    for state, count in stats['state_counts'].items():
        print(f"   {state}: {count}")

    # Example JSON output
    print("\n📄 Example JSON Output (first result):")
    import json
    print(json.dumps(results[0].to_dict(), indent=2))

    # Test reset functionality
    print("\n🔄 Testing state reset...")
    simulator.reset_state()
    stats_after_reset = simulator.get_state_statistics()
    print(f"   Satellites after reset: {stats_after_reset['total_satellites']}")
    assert stats_after_reset['total_satellites'] == 0, "Reset failed"
    print("   ✅ Reset successful")

    print("\n" + "=" * 70)
    print("✅ PropagationConditionSimulator validation complete")
    print("=" * 70)
