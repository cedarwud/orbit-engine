"""
Scenario Variant Generator for RL Training Diversity

This module combines traffic profiles and satellite load patterns to create
diverse scenario variants for reinforcement learning training. Each base
training sample is expanded into multiple variants with different combinations
of traffic requirements and network load conditions.

SOURCE: Badini, I., et al. (2024). "User-Centric Satellite Handover for Multiple Traffic
        Profiles Using Deep Q-Learning." IEEE TAES, 60(4), 4352-4367.
        (Traffic profile diversity)

SOURCE: He, S., et al. (2021). "Load-Aware Satellite Handover Strategy Based on
        Multi-Agent Reinforcement Learning." IEEE ICC, 1-6.
        (Load pattern diversity)

ACADEMIC COMPLIANCE:
- Combines two peer-reviewed approaches for comprehensive scenario diversity
- Cartesian product generates all traffic-load combinations
- No simplified or mock data generation
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import logging

# Conditional imports for both module and standalone usage
try:
    # Relative imports (when used as module)
    from .traffic_profile_generator import TrafficProfileGenerator, TrafficProfile, TrafficType
    from .satellite_load_simulator import SatelliteLoadSimulator, SatelliteLoad, LoadPattern
except ImportError:
    # Absolute imports (when run standalone)
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from stages.stage6_research_optimization.traffic_profile_generator import (
        TrafficProfileGenerator, TrafficProfile, TrafficType
    )
    from stages.stage6_research_optimization.satellite_load_simulator import (
        SatelliteLoadSimulator, SatelliteLoad, LoadPattern
    )


@dataclass
class ScenarioVariant:
    """
    Single scenario variant representing one RL training sample configuration.

    A scenario variant combines:
    - Traffic profile (VoIP/Video/IoT/BestEffort) → determines QoS requirements
    - Load pattern (Uniform/Concentrated/Dynamic) → determines network congestion state

    This creates diverse training conditions for the RL agent to learn robust
    handover policies that work across different user types and network states.

    SOURCE: Badini et al. (2024) + He et al. (2021) - Multi-scenario RL training
    """
    # Identification
    variant_id: str                     # Unique identifier: {base}_v{idx}_{traffic}_{load}
    base_sample_id: str                 # Original training sample ID

    # Scenario components
    traffic_profile: Dict[str, Any]     # Traffic type with QoS requirements
    satellite_loads: List[Dict[str, Any]]  # Load state for each satellite

    # Metadata
    variant_index: int                  # Index within this base sample's variants (1-12)
    total_variants: int                 # Total number of variants for this sample

    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary for JSON serialization."""
        return asdict(self)

    def get_traffic_type(self) -> str:
        """Get traffic type string (e.g., 'voip', 'video')."""
        return self.traffic_profile.get('type', 'unknown')

    def get_load_pattern(self) -> str:
        """Get load pattern string (e.g., 'uniform', 'concentrated')."""
        if self.satellite_loads:
            return self.satellite_loads[0].get('pattern', 'unknown')
        return 'unknown'

    def get_summary(self) -> str:
        """Get human-readable summary of this variant."""
        return (
            f"{self.variant_id}: "
            f"{self.get_traffic_type()} traffic + "
            f"{self.get_load_pattern()} load "
            f"({len(self.satellite_loads)} satellites)"
        )


class ScenarioVariantGenerator:
    """
    Generate multiple scenario variants for each training sample.

    This generator applies a Cartesian product strategy to combine all enabled
    traffic profiles with all enabled load patterns, creating comprehensive
    scenario diversity for RL training.

    Strategy: 4 traffic types × 3 load patterns = 12 variants per sample

    Each variant represents a unique combination of:
    - User requirements (traffic profile QoS)
    - Network conditions (satellite load distribution)

    This ensures the RL agent learns policies that work across:
    - Different service types (voice, video, IoT, data)
    - Different congestion states (balanced, hotspot, dynamic)

    SOURCE: Badini et al. (2024) - Traffic profile impact on handover
    SOURCE: He et al. (2021) - Load-aware handover optimization
    """

    def __init__(
        self,
        traffic_generator: TrafficProfileGenerator,
        load_simulator: SatelliteLoadSimulator,
        config: Dict[str, Any],
        logger: logging.Logger
    ):
        """
        Initialize scenario variant generator.

        Args:
            traffic_generator: Initialized traffic profile generator
            load_simulator: Initialized satellite load simulator
            config: Configuration dictionary with:
                - variant_id_format: Format string for variant IDs
                - generate_all_combinations: Generate full Cartesian product (default: True)
            logger: Logger for debugging and info messages
        """
        self.traffic_gen = traffic_generator
        self.load_sim = load_simulator
        self.config = config
        self.logger = logger

        # Variant ID format template
        # Default: {base_id}_v{index:03d}_{traffic}_{load}
        # Example: starlink_t000_v001_voip_uniform
        self.variant_id_format = config.get(
            'variant_id_format',
            "{base_id}_v{index:03d}_{traffic}_{load}"
        )

        # Whether to generate all combinations (Cartesian product)
        self.generate_all_combinations = config.get(
            'generate_all_combinations',
            True
        )

        # Calculate expected number of variants
        n_traffic = len(self.traffic_gen.enabled_types)
        n_load = len(self.load_sim.enabled_patterns)
        self.expected_variants_per_sample = n_traffic * n_load

        self.logger.info(
            f"🎲 ScenarioVariantGenerator initialized: "
            f"{n_traffic} traffic types × {n_load} load patterns = "
            f"{self.expected_variants_per_sample} variants per sample"
        )

    def generate_variants(
        self,
        base_sample_id: str,
        satellite_ids: List[str],
        timestamp_index: int = 0
    ) -> List[ScenarioVariant]:
        """
        Generate all scenario variants for a base training sample.

        This method creates the Cartesian product of all traffic profiles and
        load patterns, generating a comprehensive set of training scenarios.

        Args:
            base_sample_id: Base sample identifier (e.g., "starlink_t000")
            satellite_ids: List of visible satellite IDs at this time point
            timestamp_index: Time step index (for dynamic load patterns)

        Returns:
            List of ScenarioVariant objects (typically 12 variants)

        Example:
            >>> generator = ScenarioVariantGenerator(traffic_gen, load_sim, config, logger)
            >>> variants = generator.generate_variants(
            ...     "starlink_t000",
            ...     ["46061", "46062", "46063"],
            ...     timestamp_index=0
            ... )
            >>> print(f"Generated {len(variants)} variants")
            Generated 12 variants
        """
        if not satellite_ids:
            self.logger.warning(
                f"⚠️ No satellites provided for {base_sample_id}, skipping variant generation"
            )
            return []

        variants = []
        variant_index = 0

        # Generate all traffic profiles
        traffic_profiles = self.traffic_gen.generate_all_profiles()

        # Get enabled load patterns
        load_patterns = self.load_sim.enabled_patterns

        # Cartesian product: traffic × load
        # This ensures we train on all combinations of user requirements and network conditions
        for traffic_type, traffic_profile in traffic_profiles.items():
            for load_pattern in load_patterns:
                variant_index += 1

                # Generate load distribution for this pattern
                satellite_loads = self.load_sim.simulate_load(
                    satellite_ids,
                    pattern=load_pattern,
                    timestamp_index=timestamp_index
                )

                # Create unique variant ID
                variant_id = self.variant_id_format.format(
                    base_id=base_sample_id,
                    index=variant_index,
                    traffic=traffic_type,
                    load=load_pattern.value
                )

                # Create variant object
                variant = ScenarioVariant(
                    variant_id=variant_id,
                    base_sample_id=base_sample_id,
                    traffic_profile=traffic_profile.to_dict(),
                    satellite_loads=[load.to_dict() for load in satellite_loads],
                    variant_index=variant_index,
                    total_variants=len(traffic_profiles) * len(load_patterns)
                )

                variants.append(variant)

        self.logger.info(
            f"✨ Generated scenario variants: {base_sample_id} → {len(variants)} variants"
        )

        return variants

    def get_variant_statistics(self, variants: List[ScenarioVariant]) -> Dict[str, Any]:
        """
        Compute statistics about generated variants.

        Args:
            variants: List of generated variants

        Returns:
            Dictionary with statistics:
                - total_variants: Total number of variants
                - traffic_type_counts: Count of each traffic type
                - load_pattern_counts: Count of each load pattern
                - base_sample_ids: Set of base sample IDs
        """
        traffic_type_counts = {}
        load_pattern_counts = {}
        base_sample_ids = set()

        for variant in variants:
            # Count traffic types
            traffic_type = variant.get_traffic_type()
            traffic_type_counts[traffic_type] = traffic_type_counts.get(traffic_type, 0) + 1

            # Count load patterns
            load_pattern = variant.get_load_pattern()
            load_pattern_counts[load_pattern] = load_pattern_counts.get(load_pattern, 0) + 1

            # Collect base sample IDs
            base_sample_ids.add(variant.base_sample_id)

        return {
            "total_variants": len(variants),
            "traffic_type_counts": traffic_type_counts,
            "load_pattern_counts": load_pattern_counts,
            "unique_base_samples": len(base_sample_ids),
            "base_sample_ids": sorted(base_sample_ids)
        }

    def validate_variant_coverage(self, variants: List[ScenarioVariant]) -> bool:
        """
        Validate that variant generation covers all expected combinations.

        Args:
            variants: List of generated variants

        Returns:
            True if all combinations are covered, False otherwise
        """
        stats = self.get_variant_statistics(variants)

        # Check traffic type coverage
        expected_traffic_types = set(t.value for t in self.traffic_gen.enabled_types)
        actual_traffic_types = set(stats['traffic_type_counts'].keys())

        if expected_traffic_types != actual_traffic_types:
            self.logger.warning(
                f"⚠️ Traffic type coverage incomplete: "
                f"expected {expected_traffic_types}, got {actual_traffic_types}"
            )
            return False

        # Check load pattern coverage
        expected_load_patterns = set(p.value for p in self.load_sim.enabled_patterns)
        actual_load_patterns = set(stats['load_pattern_counts'].keys())

        if expected_load_patterns != actual_load_patterns:
            self.logger.warning(
                f"⚠️ Load pattern coverage incomplete: "
                f"expected {expected_load_patterns}, got {actual_load_patterns}"
            )
            return False

        # Check total count
        expected_count = len(expected_traffic_types) * len(expected_load_patterns)
        actual_count = stats['total_variants']

        if expected_count != actual_count:
            self.logger.warning(
                f"⚠️ Variant count mismatch: expected {expected_count}, got {actual_count}"
            )
            return False

        self.logger.debug(
            f"✅ Variant coverage validated: {actual_count} variants covering "
            f"{len(expected_traffic_types)} traffic types × {len(expected_load_patterns)} load patterns"
        )

        return True


# Module-level convenience function

def create_default_variant_generator(logger: logging.Logger = None) -> ScenarioVariantGenerator:
    """
    Create a scenario variant generator with default parameters.

    This convenience function initializes both the traffic generator and load
    simulator with default 3GPP/IEEE parameters, then combines them into a
    variant generator.

    Args:
        logger: Optional logger (creates default if not provided)

    Returns:
        Initialized ScenarioVariantGenerator

    Example:
        >>> generator = create_default_variant_generator()
        >>> variants = generator.generate_variants("test_sample", ["SAT001", "SAT002"])
        >>> print(f"Generated {len(variants)} variants")
        Generated 12 variants
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Create traffic generator (4 types by default)
    from .traffic_profile_generator import create_default_traffic_generator
    traffic_gen = create_default_traffic_generator(logger)

    # Create load simulator (3 patterns by default)
    from .satellite_load_simulator import create_default_load_simulator
    load_sim = create_default_load_simulator(logger)

    # Create variant generator
    config = {
        'variant_id_format': "{base_id}_v{index:03d}_{traffic}_{load}",
        'generate_all_combinations': True
    }

    return ScenarioVariantGenerator(traffic_gen, load_sim, config, logger)


# Module metadata
__all__ = [
    'ScenarioVariant',
    'ScenarioVariantGenerator',
    'create_default_variant_generator'
]


if __name__ == "__main__":
    # Example usage and validation
    import sys
    import os

    # Add parent directory to path for absolute imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    from stages.stage6_research_optimization.traffic_profile_generator import (
        TrafficProfileGenerator, create_default_traffic_generator
    )
    from stages.stage6_research_optimization.satellite_load_simulator import (
        SatelliteLoadSimulator, create_default_load_simulator
    )

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    print("=" * 70)
    print("Scenario Variant Generator - Example Usage")
    print("=" * 70)

    # Create components
    logger = logging.getLogger(__name__)
    traffic_gen = create_default_traffic_generator(logger)
    load_sim = create_default_load_simulator(logger)

    # Create variant generator
    config = {
        'variant_id_format': "{base_id}_v{index:03d}_{traffic}_{load}",
        'generate_all_combinations': True
    }
    generator = ScenarioVariantGenerator(traffic_gen, load_sim, config, logger)

    # Test data
    base_sample_id = "starlink_t000"
    test_satellites = ["SAT001", "SAT002", "SAT003", "SAT004", "SAT005"]

    print(f"\n📋 Configuration:")
    print(f"   Base sample ID: {base_sample_id}")
    print(f"   Satellites: {len(test_satellites)}")
    print(f"   Expected variants per sample: {generator.expected_variants_per_sample}")

    # Generate variants
    print(f"\n🎲 Generating scenario variants...\n")
    variants = generator.generate_variants(
        base_sample_id=base_sample_id,
        satellite_ids=test_satellites,
        timestamp_index=0
    )

    # Display statistics
    stats = generator.get_variant_statistics(variants)

    print(f"\n📊 Variant Statistics:")
    print(f"   Total variants: {stats['total_variants']}")
    print(f"   Traffic types: {stats['traffic_type_counts']}")
    print(f"   Load patterns: {stats['load_pattern_counts']}")

    # Validate coverage
    print(f"\n✅ Coverage Validation:")
    is_valid = generator.validate_variant_coverage(variants)
    print(f"   Coverage complete: {is_valid}")

    # Show sample variants
    print(f"\n📝 Sample Variants (first 6):\n")
    for variant in variants[:6]:
        print(f"   {variant.variant_index:2d}. {variant.get_summary()}")

    # Show one detailed variant
    print(f"\n🔍 Detailed Variant Example (Variant 1):\n")
    example = variants[0]
    print(f"   ID: {example.variant_id}")
    print(f"   Traffic: {example.traffic_profile['type']} - {example.traffic_profile['description']}")
    print(f"   QoS Requirements:")
    print(f"     - Max Delay: {example.traffic_profile['max_delay_ms']} ms")
    print(f"     - Min Bandwidth: {example.traffic_profile['min_bandwidth_kbps']} kbps")
    print(f"     - Min Reliability: {example.traffic_profile['min_reliability']*100:.1f}%")
    print(f"   Load Pattern: {example.get_load_pattern()}")
    print(f"   Satellites: {len(example.satellite_loads)} satellites")

    # Show load distribution for first 3 satellites
    print(f"\n   Satellite Load Distribution:")
    for load in example.satellite_loads[:3]:
        print(
            f"     {load['satellite_id']}: {load['current_users']}/{load['capacity']} users "
            f"({load['utilization']:.1%}) - {load['load_state']}"
        )

    print(f"\n✅ Example completed successfully\n")
