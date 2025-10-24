#!/usr/bin/env python3
"""
Temporal Analysis of D2 vs A4 Strategies - Version 2
===================================================

This version analyzes the signal_analysis time-series data directly,
simulating A4 vs D2 handover strategies at each time point.

Compares:
- A4 Strategy: Select satellite with best instant RSRP
- D2 Strategy: Select satellite with best distance (closest)

Then evaluates connection stability over the next 10 minutes.

Author: Claude (Anthropic AI)
Date: 2025-10-24
Version: 2.0.0
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SatelliteCandidate:
    """Satellite candidate at a specific time"""
    satellite_id: int
    rsrp_dbm: float
    distance_km: float
    is_connectable: bool


class TemporalComparison:
    """Compare A4 vs D2 strategies using temporal stability analysis"""

    def __init__(self, rsrp_threshold_dbm: float = -95.0):
        self.rsrp_threshold = rsrp_threshold_dbm

    def analyze(self, stage6_file: Path) -> Dict:
        """Main analysis entry point"""
        logger.info(f"📊 Loading Stage 6 data: {stage6_file}")

        with open(stage6_file) as f:
            data = json.load(f)

        signal_analysis = data.get('signal_analysis', {})

        # Get time series for all satellites
        time_series_data = self._extract_time_series(signal_analysis)

        logger.info(f"   Found {len(time_series_data)} timestamps")
        logger.info(f"   Satellites tracked: {len(signal_analysis)}")

        # Analyze each time point
        comparisons = []
        for i, timestamp in enumerate(time_series_data['timestamps']):
            # Get available candidates at this time
            candidates = self._get_candidates_at_time(
                timestamp=timestamp,
                time_index=i,
                signal_analysis=signal_analysis
            )

            if len(candidates) < 2:
                continue

            # Simulate A4 and D2 choices
            a4_choice = max(candidates, key=lambda c: c.rsrp_dbm)
            d2_choice = min(candidates, key=lambda c: c.distance_km)

            # If same satellite, record but note it
            same_choice = (a4_choice.satellite_id == d2_choice.satellite_id)

            # Evaluate temporal stability
            a4_stability = self._evaluate_stability(
                satellite_id=a4_choice.satellite_id,
                start_time_index=i,
                signal_analysis=signal_analysis
            )

            d2_stability = self._evaluate_stability(
                satellite_id=d2_choice.satellite_id,
                start_time_index=i,
                signal_analysis=signal_analysis
            )

            if a4_stability and d2_stability:
                comparison = {
                    'timestamp': timestamp,
                    'num_candidates': len(candidates),
                    'same_satellite_chosen': same_choice,
                    'a4_satellite_id': a4_choice.satellite_id,
                    'a4_instant_rsrp': a4_choice.rsrp_dbm,
                    'a4_instant_distance': a4_choice.distance_km,
                    'a4_connection_duration_sec': a4_stability['duration_sec'],
                    'a4_average_rsrp': a4_stability['avg_rsrp'],
                    'd2_satellite_id': d2_choice.satellite_id,
                    'd2_instant_rsrp': d2_choice.rsrp_dbm,
                    'd2_instant_distance': d2_choice.distance_km,
                    'd2_connection_duration_sec': d2_stability['duration_sec'],
                    'd2_average_rsrp': d2_stability['avg_rsrp']
                }
                comparisons.append(comparison)

        # Generate summary
        summary = self._generate_summary(comparisons)

        return {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'source_file': str(stage6_file),
                'rsrp_threshold_dbm': self.rsrp_threshold,
                'total_comparisons': len(comparisons)
            },
            'comparisons': comparisons,
            'summary': summary
        }

    def _extract_time_series(self, signal_analysis: Dict) -> Dict:
        """Extract common timestamps from signal analysis"""
        # Get timestamps from first satellite
        first_sat = list(signal_analysis.values())[0]
        timestamps = [entry['timestamp'] for entry in first_sat['time_series']]

        return {
            'timestamps': timestamps,
            'interval_seconds': 30  # Known from Stage 5/6 config
        }

    def _get_candidates_at_time(
        self,
        timestamp: str,
        time_index: int,
        signal_analysis: Dict
    ) -> List[SatelliteCandidate]:
        """Get all visible/connectable satellites at a specific time"""
        candidates = []

        for sat_id_str, sat_data in signal_analysis.items():
            time_series = sat_data.get('time_series', [])

            if time_index >= len(time_series):
                continue

            entry = time_series[time_index]

            # Verify timestamp matches
            if entry.get('timestamp') != timestamp:
                continue

            is_connectable = entry.get('is_connectable', False)
            if not is_connectable:
                continue

            signal_quality = entry.get('signal_quality', {})
            physical_params = entry.get('physical_parameters', {})

            rsrp = signal_quality.get('rsrp_dbm', -140.0)
            distance = physical_params.get('distance_km', 999999.0)

            # Filter by RSRP threshold
            if rsrp < self.rsrp_threshold:
                continue

            candidates.append(SatelliteCandidate(
                satellite_id=int(sat_id_str),
                rsrp_dbm=rsrp,
                distance_km=distance,
                is_connectable=is_connectable
            ))

        return candidates

    def _evaluate_stability(
        self,
        satellite_id: int,
        start_time_index: int,
        signal_analysis: Dict
    ) -> Optional[Dict]:
        """Evaluate connection stability over next 10 minutes"""
        sat_data = signal_analysis.get(str(satellite_id), {})
        time_series = sat_data.get('time_series', [])

        if start_time_index >= len(time_series):
            return None

        rsrp_values = []
        duration_sec = 0

        for i in range(start_time_index, len(time_series)):
            entry = time_series[i]
            rsrp = entry.get('signal_quality', {}).get('rsrp_dbm', -140.0)

            if rsrp >= self.rsrp_threshold:
                rsrp_values.append(rsrp)
                duration_sec = (i - start_time_index) * 30
            else:
                break

        if not rsrp_values:
            return None

        return {
            'duration_sec': duration_sec,
            'avg_rsrp': sum(rsrp_values) / len(rsrp_values),
            'min_rsrp': min(rsrp_values),
            'max_rsrp': max(rsrp_values)
        }

    def _generate_summary(self, comparisons: List[Dict]) -> Dict:
        """Generate summary statistics"""
        if not comparisons:
            return {
                'total_comparisons': 0,
                'error': 'No valid comparisons found'
            }

        n = len(comparisons)
        same_choice_count = sum(1 for c in comparisons if c['same_satellite_chosen'])

        # Calculate advantages
        total_duration_gain = sum(
            c['d2_connection_duration_sec'] - c['a4_connection_duration_sec']
            for c in comparisons
        )

        total_rsrp_diff = sum(
            c['d2_average_rsrp'] - c['a4_average_rsrp']
            for c in comparisons
        )

        # Determine winners
        d2_wins = sum(1 for c in comparisons if c['d2_connection_duration_sec'] > c['a4_connection_duration_sec'] + 60)
        a4_wins = sum(1 for c in comparisons if c['a4_connection_duration_sec'] > c['d2_connection_duration_sec'] + 60)
        ties = n - d2_wins - a4_wins

        # Calculate instant RSRP disadvantage for D2
        instant_rsrp_penalty = sum(
            c['a4_instant_rsrp'] - c['d2_instant_rsrp']
            for c in comparisons
        )

        return {
            'total_comparisons': n,
            'same_satellite_chosen': same_choice_count,
            'same_satellite_rate': same_choice_count / n * 100,
            'different_satellite_count': n - same_choice_count,
            'winner_distribution': {
                'd2_wins': d2_wins,
                'a4_wins': a4_wins,
                'ties': ties,
                'd2_win_rate': d2_wins / n * 100,
                'a4_win_rate': a4_wins / n * 100
            },
            'average_metrics': {
                'd2_connection_duration_gain_sec': total_duration_gain / n,
                'd2_average_rsrp_diff_db': total_rsrp_diff / n,
                'd2_instant_rsrp_penalty_db': instant_rsrp_penalty / n
            },
            'interpretation': self._interpret(d2_wins, a4_wins, n, total_duration_gain, instant_rsrp_penalty)
        }

    def _interpret(self, d2_wins, a4_wins, n, total_duration_gain, instant_rsrp_penalty):
        """Interpret results"""
        d2_win_rate = d2_wins / n * 100 if n > 0 else 0
        avg_duration_gain = total_duration_gain / n if n > 0 else 0
        avg_rsrp_penalty = instant_rsrp_penalty / n if n > 0 else 0

        if d2_win_rate > 60:
            return (
                f"✅ D2 (distance-based) strategy wins {d2_win_rate:.1f}% of cases. "
                f"D2 provides {avg_duration_gain:.0f}s longer connections on average, "
                f"despite {avg_rsrp_penalty:.1f} dB lower instant RSRP. "
                "This validates predictive handover for LEO networks."
            )
        elif d2_win_rate > 40:
            return (
                f"⚖️ Strategies perform similarly (D2: {d2_win_rate:.1f}%, A4: {a4_wins/n*100:.1f}%). "
                f"D2 gains {avg_duration_gain:.0f}s duration but pays {avg_rsrp_penalty:.1f} dB RSRP penalty. "
                "Trade-off between instant quality and future stability."
            )
        else:
            return (
                f"❌ A4 (RSRP-based) strategy wins {a4_wins/n*100:.1f}% of cases. "
                f"D2's {avg_rsrp_penalty:.1f} dB instant RSRP penalty is not compensated by {avg_duration_gain:.0f}s duration gain. "
                "Instant optimization outperforms predictive in this scenario."
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Temporal A4 vs D2 Analysis')
    parser.add_argument('--input', help='Stage 6 output file')
    parser.add_argument('--rsrp-threshold', type=float, default=-95.0)
    parser.add_argument('--output', default='data/outputs/temporal_analysis/d2_temporal_v2.json')
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

    logger.info(f"🎯 Temporal D2 vs A4 Analysis (v2)")
    logger.info(f"   Input: {stage6_file}")

    analyzer = TemporalComparison(rsrp_threshold_dbm=args.rsrp_threshold)
    results = analyzer.analyze(stage6_file)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Analysis complete: {output_path}")

    # Print summary
    summary = results['summary']
    print("\n" + "="*80)
    print("📊 TEMPORAL D2 vs A4 ANALYSIS - RESULTS")
    print("="*80)

    if 'error' in summary:
        print(f"\n❌ {summary['error']}")
    else:
        print(f"\nTotal comparisons: {summary['total_comparisons']}")
        print(f"\nStrategy Agreement:")
        print(f"   Same satellite: {summary['same_satellite_rate']:.1f}% ({summary['same_satellite_chosen']} cases)")
        print(f"   Different satellites: {summary['different_satellite_count']} cases")
        print(f"\nWinner Distribution:")
        print(f"   D2 wins: {summary['winner_distribution']['d2_wins']} ({summary['winner_distribution']['d2_win_rate']:.1f}%)")
        print(f"   A4 wins: {summary['winner_distribution']['a4_wins']} ({summary['winner_distribution']['a4_win_rate']:.1f}%)")
        print(f"   Ties: {summary['winner_distribution']['ties']}")
        print(f"\nAverage Metrics:")
        print(f"   D2 connection duration gain: {summary['average_metrics']['d2_connection_duration_gain_sec']:.1f} seconds")
        print(f"   D2 average RSRP diff: {summary['average_metrics']['d2_average_rsrp_diff_db']:.2f} dB")
        print(f"   D2 instant RSRP penalty: {summary['average_metrics']['d2_instant_rsrp_penalty_db']:.2f} dB")
        print(f"\n{summary['interpretation']}")

    print("="*80 + "\n")


if __name__ == '__main__':
    main()
