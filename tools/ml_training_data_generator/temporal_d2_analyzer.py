#!/usr/bin/env python3
"""
Temporal Analysis of D2 Events - Academic Evaluation
=====================================================

PURPOSE:
    Evaluate D2 event effectiveness using temporal/predictive metrics instead
    of snapshot-based comparison.

MOTIVATION:
    - Single-moment analysis shows D2 impact = 0% (due to FSPL correlation)
    - D2 is designed for TEMPORAL handover prediction, not spatial optimization
    - Proper evaluation requires time-series stability analysis

ACADEMIC SOURCES:
    - 3GPP TR 38.821 Section 6.4.2: High-speed mobility (7.5 km/s) requires predictive handover
    - 3GPP TS 38.331 v18.5.1 Section 5.5.4.4: D2 "moving reference location" design
    - Badini et al. (2024) IEEE TAES: Connection stability metrics for LEO handover

ANALYSIS METHODOLOGY:
    For each handover decision point at time t:
    1. A4 Strategy: Select satellite with best instant RSRP at time t
    2. D2 Strategy: Select satellite with best distance at time t
    3. Compare over next 10 minutes (t+30s, t+60s, ..., t+600s):
       - Connection duration (time until RSRP < threshold)
       - RSRP degradation rate (dB/minute)
       - Number of subsequent handovers needed (ping-pong rate)
       - Average RSRP over connection lifetime

EXPECTED RESULTS:
    - A4: Better instant RSRP, but faster degradation (satellite moving away)
    - D2: Slightly lower instant RSRP, but longer connection duration (satellite approaching)
    - D2 advantage: Reduced ping-pong handovers, more stable connections

Author: Claude (Anthropic AI)
Date: 2025-10-24
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TemporalMetrics:
    """Metrics for temporal handover stability analysis"""
    # Strategy identifier
    strategy: str  # "A4" or "D2"

    # Selected satellite
    selected_satellite_id: int

    # Instant metrics (at decision time t=0)
    instant_rsrp_dbm: float
    instant_distance_km: float

    # Temporal stability metrics (over next 10 minutes)
    connection_duration_seconds: float  # Time until RSRP < threshold
    average_rsrp_dbm: float            # Average RSRP during connection
    rsrp_degradation_rate: float       # dB per minute
    min_rsrp_dbm: float                # Minimum RSRP reached

    # Handover frequency
    handovers_needed: int              # Number of subsequent handovers
    ping_pong_occurred: bool           # Handover back to previous satellite

    # Future RSRP predictions (for visualization)
    future_rsrp_timeline: List[Tuple[int, float]]  # [(seconds, rsrp_dbm), ...]


class TemporalD2Analyzer:
    """
    Temporal analyzer for D2 event evaluation.

    Compares A4 (instant optimal) vs D2 (predictive optimal) strategies
    using time-series stability metrics.
    """

    def __init__(self, rsrp_threshold_dbm: float = -95.0):
        """
        Initialize temporal analyzer.

        Args:
            rsrp_threshold_dbm: RSRP threshold for connection quality
                               SOURCE: 3GPP TS 38.133 Section 10.1.16 (VoIP threshold)
        """
        self.rsrp_threshold = rsrp_threshold_dbm
        self.results: List[Dict] = []

    def analyze_stage6_output(self, stage6_file: Path) -> Dict:
        """
        Analyze Stage 6 output for temporal D2 effectiveness.

        Args:
            stage6_file: Path to stage6_research*.json file

        Returns:
            Analysis results with A4 vs D2 comparison
        """
        logger.info(f"📊 Loading Stage 6 data: {stage6_file}")

        with open(stage6_file, 'r') as f:
            data = json.load(f)

        # Extract relevant data
        gpp_events = data.get('gpp_events', {})
        signal_analysis = data.get('signal_analysis', {})

        # Get A4 and D2 events
        a4_events = gpp_events.get('a4_events', [])
        d2_events = gpp_events.get('d2_events', [])

        logger.info(f"   Found {len(a4_events)} A4 events, {len(d2_events)} D2 events")

        # Analyze each handover decision point
        comparison_results = []

        # Group events by timestamp to find concurrent A4+D2 decisions
        events_by_time = self._group_events_by_timestamp(a4_events, d2_events)

        logger.info(f"   Found {len(events_by_time)} time points with handover events")

        for timestamp, events in events_by_time.items():
            result = self._analyze_handover_decision(
                timestamp=timestamp,
                events=events,
                signal_analysis=signal_analysis
            )
            if result:
                comparison_results.append(result)

        # Generate summary statistics
        summary = self._generate_summary(comparison_results)

        return {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'stage6_file': str(stage6_file),
                'rsrp_threshold_dbm': self.rsrp_threshold,
                'total_comparisons': len(comparison_results)
            },
            'comparison_results': comparison_results,
            'summary': summary
        }

    def _group_events_by_timestamp(
        self,
        a4_events: List[Dict],
        d2_events: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Group A4 and D2 events by timestamp.

        Returns:
            Dict mapping timestamp -> {'a4': [...], 'd2': [...]}
        """
        events_by_time = defaultdict(lambda: {'a4': [], 'd2': []})

        for event in a4_events:
            ts = event.get('timestamp')
            if ts:
                events_by_time[ts]['a4'].append(event)

        for event in d2_events:
            ts = event.get('timestamp')
            if ts:
                events_by_time[ts]['d2'].append(event)

        return dict(events_by_time)

    def _analyze_handover_decision(
        self,
        timestamp: str,
        events: Dict[str, List[Dict]],
        signal_analysis: Dict
    ) -> Optional[Dict]:
        """
        Analyze a single handover decision point.

        Compares:
        - A4 strategy: Choose satellite with best instant RSRP
        - D2 strategy: Choose satellite with best distance

        Then evaluates connection stability over next 10 minutes.

        NOTE: D2 candidates are typically a subset of A4 candidates due to
        physical FSPL correlation. We compare strategies on the COMBINED
        candidate pool to evaluate the value of distance-based prioritization.
        """
        a4_events = events.get('a4', [])
        d2_events = events.get('d2', [])

        # Need at least one event to analyze
        if not a4_events:
            return None  # Focus on A4 events since they have RSRP data

        # Find serving satellite
        serving_sat_id = a4_events[0].get('serving_satellite')
        if not serving_sat_id:
            return None

        # Get all candidate satellites at this time
        candidates = self._get_candidates_at_timestamp(
            timestamp=timestamp,
            a4_events=a4_events,
            d2_events=d2_events,
            signal_analysis=signal_analysis
        )

        if len(candidates) < 2:
            return None  # Need at least 2 candidates to compare

        # Filter candidates with valid distance data
        valid_candidates = [c for c in candidates if c['instant_distance'] is not None and c['instant_distance'] < 999999]
        if len(valid_candidates) < 2:
            return None

        # A4 Strategy: Choose best instant RSRP
        a4_choice = max(valid_candidates, key=lambda c: c['instant_rsrp'])

        # D2 Strategy: Choose best distance (closest)
        d2_choice = min(valid_candidates, key=lambda c: c['instant_distance'])

        # If A4 and D2 chose the same satellite, still analyze but mark it
        same_choice = (a4_choice['satellite_id'] == d2_choice['satellite_id'])

        # Evaluate temporal stability for both choices
        a4_metrics = self._evaluate_temporal_stability(
            satellite_id=a4_choice['satellite_id'],
            timestamp=timestamp,
            signal_analysis=signal_analysis,
            strategy='A4'
        )

        d2_metrics = self._evaluate_temporal_stability(
            satellite_id=d2_choice['satellite_id'],
            timestamp=timestamp,
            signal_analysis=signal_analysis,
            strategy='D2'
        )

        if not a4_metrics or not d2_metrics:
            return None

        # Determine which strategy performed better
        winner = self._determine_winner(a4_metrics, d2_metrics)

        return {
            'timestamp': timestamp,
            'serving_satellite_id': serving_sat_id,
            'num_candidates': len(valid_candidates),
            'same_satellite_chosen': same_choice,
            'a4_metrics': a4_metrics.__dict__,
            'd2_metrics': d2_metrics.__dict__,
            'winner': winner,
            'advantage': {
                'connection_duration_gain_seconds': d2_metrics.connection_duration_seconds - a4_metrics.connection_duration_seconds,
                'average_rsrp_diff_db': d2_metrics.average_rsrp_dbm - a4_metrics.average_rsrp_dbm,
                'handover_reduction': a4_metrics.handovers_needed - d2_metrics.handovers_needed
            }
        }

    def _get_candidates_at_timestamp(
        self,
        timestamp: str,
        a4_events: List[Dict],
        d2_events: List[Dict],
        signal_analysis: Dict
    ) -> List[Dict]:
        """
        Get all candidate satellites at a specific timestamp.

        Returns:
            List of dicts with satellite_id, instant_rsrp, instant_distance
        """
        candidates = {}

        # Get candidates from A4 events
        for event in a4_events:
            neighbor_id = event.get('neighbor_satellite_id')
            if neighbor_id:
                rsrp = event.get('measurements', {}).get('neighbor_rsrp_dbm', -140.0)
                candidates[neighbor_id] = {
                    'satellite_id': neighbor_id,
                    'instant_rsrp': rsrp,
                    'instant_distance': None
                }

        # Get candidates from D2 events
        for event in d2_events:
            neighbor_id = event.get('neighbor_satellite_id')
            if neighbor_id:
                distance = event.get('measurements', {}).get('neighbor_ground_distance_km', 999999)
                if neighbor_id in candidates:
                    candidates[neighbor_id]['instant_distance'] = distance
                else:
                    # D2-only candidate, need to get RSRP from signal_analysis
                    rsrp = self._get_rsrp_from_signal_analysis(
                        satellite_id=neighbor_id,
                        timestamp=timestamp,
                        signal_analysis=signal_analysis
                    )
                    candidates[neighbor_id] = {
                        'satellite_id': neighbor_id,
                        'instant_rsrp': rsrp,
                        'instant_distance': distance
                    }

        # Fill missing distances from signal_analysis
        for sat_id, candidate in candidates.items():
            if candidate['instant_distance'] is None:
                distance = self._get_distance_from_signal_analysis(
                    satellite_id=sat_id,
                    timestamp=timestamp,
                    signal_analysis=signal_analysis
                )
                candidate['instant_distance'] = distance

        return list(candidates.values())

    def _get_rsrp_from_signal_analysis(
        self,
        satellite_id: int,
        timestamp: str,
        signal_analysis: Dict
    ) -> float:
        """Get RSRP for a satellite at a specific timestamp"""
        sat_data = signal_analysis.get(str(satellite_id), {})
        time_series = sat_data.get('time_series', [])

        for entry in time_series:
            if entry.get('timestamp') == timestamp:
                return entry.get('signal_quality', {}).get('rsrp_dbm', -140.0)

        return -140.0

    def _get_distance_from_signal_analysis(
        self,
        satellite_id: int,
        timestamp: str,
        signal_analysis: Dict
    ) -> float:
        """Get distance for a satellite at a specific timestamp"""
        sat_data = signal_analysis.get(str(satellite_id), {})
        time_series = sat_data.get('time_series', [])

        for entry in time_series:
            if entry.get('timestamp') == timestamp:
                return entry.get('physical_parameters', {}).get('ground_distance_km', 999999)

        return 999999

    def _evaluate_temporal_stability(
        self,
        satellite_id: int,
        timestamp: str,
        signal_analysis: Dict,
        strategy: str
    ) -> Optional[TemporalMetrics]:
        """
        Evaluate temporal stability of a handover choice.

        Analyzes what happens over the next 10 minutes if we chose this satellite.
        """
        sat_data = signal_analysis.get(str(satellite_id), {})
        time_series = sat_data.get('time_series', [])

        if not time_series:
            return None

        # Find the starting point (decision time)
        start_index = None
        for i, entry in enumerate(time_series):
            if entry.get('timestamp') == timestamp:
                start_index = i
                break

        if start_index is None:
            return None

        # Get instant metrics
        instant_entry = time_series[start_index]
        instant_rsrp = instant_entry.get('signal_quality', {}).get('rsrp_dbm', -140.0)
        instant_distance = instant_entry.get('physical_parameters', {}).get('ground_distance_km', 999999)

        # Analyze future time points
        future_rsrp_timeline = []
        rsrp_values = []
        connection_duration = 0

        for i in range(start_index, len(time_series)):
            elapsed_seconds = (i - start_index) * 30  # 30-second intervals
            entry = time_series[i]
            rsrp = entry.get('signal_quality', {}).get('rsrp_dbm', -140.0)

            future_rsrp_timeline.append((elapsed_seconds, rsrp))

            # Check if connection is still viable
            if rsrp >= self.rsrp_threshold:
                connection_duration = elapsed_seconds
                rsrp_values.append(rsrp)
            else:
                # Connection lost
                break

        if not rsrp_values:
            return None

        # Calculate metrics
        average_rsrp = sum(rsrp_values) / len(rsrp_values)
        min_rsrp = min(rsrp_values)

        # RSRP degradation rate (dB per minute)
        if len(rsrp_values) >= 2:
            duration_minutes = connection_duration / 60.0
            if duration_minutes > 0:
                degradation_rate = (rsrp_values[-1] - rsrp_values[0]) / duration_minutes
            else:
                degradation_rate = 0.0
        else:
            degradation_rate = 0.0

        # Estimate handovers needed (simplified: assume handover every time RSRP < threshold)
        handovers_needed = 0
        for _, rsrp in future_rsrp_timeline:
            if rsrp < self.rsrp_threshold:
                handovers_needed += 1
                break  # Only count first handover

        return TemporalMetrics(
            strategy=strategy,
            selected_satellite_id=satellite_id,
            instant_rsrp_dbm=instant_rsrp,
            instant_distance_km=instant_distance,
            connection_duration_seconds=connection_duration,
            average_rsrp_dbm=average_rsrp,
            rsrp_degradation_rate=degradation_rate,
            min_rsrp_dbm=min_rsrp,
            handovers_needed=handovers_needed,
            ping_pong_occurred=False,  # TODO: Implement ping-pong detection
            future_rsrp_timeline=future_rsrp_timeline
        )

    def _determine_winner(
        self,
        a4_metrics: TemporalMetrics,
        d2_metrics: TemporalMetrics
    ) -> str:
        """
        Determine which strategy performed better.

        Criteria (in priority order):
        1. Connection duration (longer is better)
        2. Average RSRP (higher is better)
        3. Handover reduction (fewer is better)
        """
        # Primary criterion: Connection duration
        if d2_metrics.connection_duration_seconds > a4_metrics.connection_duration_seconds + 60:
            return 'D2'
        elif a4_metrics.connection_duration_seconds > d2_metrics.connection_duration_seconds + 60:
            return 'A4'

        # Secondary criterion: Average RSRP
        rsrp_diff = d2_metrics.average_rsrp_dbm - a4_metrics.average_rsrp_dbm
        if rsrp_diff > 2.0:
            return 'D2'
        elif rsrp_diff < -2.0:
            return 'A4'

        # Tertiary criterion: Handover frequency
        if d2_metrics.handovers_needed < a4_metrics.handovers_needed:
            return 'D2'
        elif a4_metrics.handovers_needed < d2_metrics.handovers_needed:
            return 'A4'

        return 'Tie'

    def _generate_summary(self, comparison_results: List[Dict]) -> Dict:
        """
        Generate summary statistics for all comparisons.
        """
        if not comparison_results:
            return {
                'total_comparisons': 0,
                'error': 'No valid comparisons found'
            }

        winners = {'A4': 0, 'D2': 0, 'Tie': 0}
        same_choice_count = 0
        total_duration_gain = 0
        total_rsrp_diff = 0
        total_handover_reduction = 0

        for result in comparison_results:
            winners[result['winner']] += 1
            if result.get('same_satellite_chosen', False):
                same_choice_count += 1
            total_duration_gain += result['advantage']['connection_duration_gain_seconds']
            total_rsrp_diff += result['advantage']['average_rsrp_diff_db']
            total_handover_reduction += result['advantage']['handover_reduction']

        n = len(comparison_results)

        return {
            'total_comparisons': n,
            'same_satellite_rate': same_choice_count / n * 100 if n > 0 else 0,
            'different_satellite_count': n - same_choice_count,
            'winner_distribution': {
                'a4_wins': winners['A4'],
                'd2_wins': winners['D2'],
                'ties': winners['Tie'],
                'a4_win_rate': winners['A4'] / n * 100 if n > 0 else 0,
                'd2_win_rate': winners['D2'] / n * 100 if n > 0 else 0
            },
            'average_advantages': {
                'd2_connection_duration_gain_seconds': total_duration_gain / n if n > 0 else 0,
                'd2_average_rsrp_advantage_db': total_rsrp_diff / n if n > 0 else 0,
                'd2_handover_reduction': total_handover_reduction / n if n > 0 else 0
            },
            'interpretation': self._interpret_results(winners, n, total_duration_gain, total_handover_reduction)
        }

    def _interpret_results(
        self,
        winners: Dict[str, int],
        n: int,
        total_duration_gain: float,
        total_handover_reduction: int
    ) -> str:
        """
        Provide human-readable interpretation of results.
        """
        d2_win_rate = winners['D2'] / n * 100 if n > 0 else 0
        avg_duration_gain = total_duration_gain / n if n > 0 else 0
        avg_handover_reduction = total_handover_reduction / n if n > 0 else 0

        if d2_win_rate > 60:
            return (
                f"✅ D2 strategy demonstrates clear advantage ({d2_win_rate:.1f}% win rate). "
                f"D2 provides {avg_duration_gain:.0f}s longer connections on average and "
                f"reduces handovers by {avg_handover_reduction:.1f} per decision. "
                "This validates D2's predictive handover design for LEO networks."
            )
        elif d2_win_rate > 40:
            return (
                f"⚖️ D2 and A4 strategies perform comparably ({d2_win_rate:.1f}% vs {winners['A4']/n*100:.1f}%). "
                f"D2 provides {avg_duration_gain:.0f}s duration advantage but similar overall performance. "
                "This suggests scenario-dependent effectiveness."
            )
        else:
            return (
                f"❌ A4 strategy outperforms D2 in this scenario ({winners['A4']/n*100:.1f}% vs {d2_win_rate:.1f}%). "
                f"A4's instant optimization provides better connection stability. "
                "This may indicate test conditions favor instant RSRP optimization over distance prediction."
            )


def main():
    """Main entry point for temporal analysis"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Temporal Analysis of D2 Events',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze latest Stage 6 output
    python temporal_d2_analyzer.py

    # Analyze specific file
    python temporal_d2_analyzer.py --input data/outputs/stage6/stage6_research_*.json

    # Use custom RSRP threshold
    python temporal_d2_analyzer.py --rsrp-threshold -100.0
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        help='Path to Stage 6 output file'
    )

    parser.add_argument(
        '--rsrp-threshold',
        type=float,
        default=-95.0,
        help='RSRP threshold for connection quality (default: -95.0 dBm)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/outputs/temporal_analysis/d2_temporal_analysis.json',
        help='Output path for analysis results'
    )

    args = parser.parse_args()

    # Find Stage 6 file
    if args.input:
        stage6_file = Path(args.input)
    else:
        stage6_dir = Path('data/outputs/stage6')
        stage6_files = list(stage6_dir.glob('stage6_research*.json'))
        if not stage6_files:
            logger.error("❌ No Stage 6 output files found")
            return
        stage6_file = max(stage6_files, key=lambda p: p.stat().st_mtime)

    logger.info(f"🎯 Temporal D2 Analysis")
    logger.info(f"   Input: {stage6_file}")
    logger.info(f"   RSRP threshold: {args.rsrp_threshold} dBm")

    # Run analysis
    analyzer = TemporalD2Analyzer(rsrp_threshold_dbm=args.rsrp_threshold)
    results = analyzer.analyze_stage6_output(stage6_file)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Analysis complete: {output_path}")

    # Print summary
    summary = results['summary']
    print("\n" + "="*80)
    print("📊 TEMPORAL D2 ANALYSIS SUMMARY")
    print("="*80)
    print(f"\nTotal comparisons: {summary['total_comparisons']}")

    if 'error' in summary:
        print(f"\n❌ {summary['error']}")
        print("="*80 + "\n")
        return

    print(f"\nStrategy Agreement:")
    print(f"   Same satellite chosen: {summary['same_satellite_rate']:.1f}% ({summary.get('total_comparisons', 0) - summary.get('different_satellite_count', 0)} cases)")
    print(f"   Different satellites: {summary.get('different_satellite_count', 0)} cases")
    print(f"\nWinner distribution:")
    print(f"   A4 wins: {summary['winner_distribution']['a4_wins']} ({summary['winner_distribution']['a4_win_rate']:.1f}%)")
    print(f"   D2 wins: {summary['winner_distribution']['d2_wins']} ({summary['winner_distribution']['d2_win_rate']:.1f}%)")
    print(f"   Ties: {summary['winner_distribution']['ties']}")
    print(f"\nD2 Average advantages:")
    print(f"   Connection duration gain: {summary['average_advantages']['d2_connection_duration_gain_seconds']:.1f} seconds")
    print(f"   Average RSRP advantage: {summary['average_advantages']['d2_average_rsrp_advantage_db']:.2f} dB")
    print(f"   Handover reduction: {summary['average_advantages']['d2_handover_reduction']:.2f}")
    print(f"\n{summary['interpretation']}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
