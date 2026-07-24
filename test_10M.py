"""10M bit test for the Morphic Bitstream Engine."""

from mbe_engine import MorphicBitstreamEngine
import time
import random

random.seed(42)

def run_10m_test():
    """Run 10M bit test and collect statistics."""
    engine = MorphicBitstreamEngine(window_size=8)
    
    print("=" * 130)
    print("MBE 10M BIT TEST")
    print("=" * 130)
    
    # Generate 10M bits per stream
    print("\nGenerating 10M bit streams...")
    
    # Stream A: Realistic mixed patterns
    stream_A = []
    for i in range(1250000):  # 10,000,000 bits
        pattern_type = i % 100
        if pattern_type < 30:  # 30% - text-like
            stream_A.extend([0,1,0,1,0,1,0,1])
        elif pattern_type < 50:  # 20% - padding
            stream_A.extend([0,0,0,0,0,0,0,0])
        elif pattern_type < 70:  # 20% - signal
            stream_A.extend([1,1,1,1,1,1,1,1])
        elif pattern_type < 85:  # 15% - structured
            stream_A.extend([0,0,0,0,1,1,1,1])
        else:  # 15% - noise
            stream_A.extend([random.randint(0, 1) for _ in range(8)])
    
    # Stream B: Slow drift with noise
    stream_B = []
    for i in range(1250000):  # 10,000,000 bits
        if i < 250000:
            stream_B.extend([0,0,0,0,0,0,0,0])
        elif i < 500000:
            stream_B.extend([0,0,0,0,0,0,0,1])
        elif i < 750000:
            stream_B.extend([0,0,0,0,1,1,1,1])
        elif i < 1000000:
            stream_B.extend([1,1,1,1,1,1,1,1])
        else:
            stream_B.extend([random.randint(0, 1) for _ in range(8)])
    
    print(f"Stream A: {len(stream_A):,} bits")
    print(f"Stream B: {len(stream_B):,} bits")
    print(f"Total bits: {len(stream_A) + len(stream_B):,}")
    print()
    
    # Statistics
    regime_counts = {"PHASE_INTERRUPT": 0, "POLYRHYTHMIC_SLICING": 0, "HARMONIC_LOCK": 0}
    regime_changes = []
    prev_regime = None
    
    # Process in chunks
    print("Processing...")
    start_time = time.time()
    total_ticks = 0
    progress_interval = 100000  # Report every 100K ticks
    
    chunk_size = 8
    for tick in range(0, min(len(stream_A), len(stream_B)), chunk_size):
        chunk_A = stream_A[tick:tick+chunk_size]
        chunk_B = stream_B[tick:tick+chunk_size]
        
        if len(chunk_A) < chunk_size or len(chunk_B) < chunk_size:
            break
        
        result = engine.step([chunk_A, chunk_B])
        
        regime = result['regime']
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        if regime != prev_regime:
            regime_changes.append((tick // chunk_size, regime, result['db_values'][:]))
            prev_regime = regime
        
        total_ticks += 1
        
        # Progress report
        if total_ticks % progress_interval == 0:
            elapsed = time.time() - start_time
            bits_processed = total_ticks * chunk_size * 2
            bits_per_sec = bits_processed / elapsed
            print(f"  Tick {total_ticks:>10,} | Bits: {bits_processed:>13,} | Rate: {bits_per_sec:>10,.0f} bits/sec | Time: {elapsed:.1f}s")
    
    elapsed = time.time() - start_time
    bits_processed = total_ticks * chunk_size * 2
    bits_per_sec = bits_processed / elapsed
    
    # Print summary
    print(f"\n{'='*130}")
    print("RESULTS SUMMARY")
    print(f"{'='*130}")
    
    print(f"\n{'REGIME DISTRIBUTION':<50}")
    print(f"{'-'*50}")
    for regime, count in regime_counts.items():
        pct = 100 * count / total_ticks if total_ticks > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {regime:<30} {count:>10} ({pct:>5.1f}%) {bar}")
    
    print(f"\n{'REGIME CHANGES':<50}")
    print(f"{'-'*50}")
    print(f"  Total regime changes: {len(regime_changes):,}")
    print(f"  First 10 changes:")
    for tick, regime, db_vals in regime_changes[:10]:
        print(f"    Tick {tick:>9,}: {regime:<30} Db=[{db_vals[0]:.2f}, {db_vals[1]:.2f}]")
    if len(regime_changes) > 10:
        print(f"    ... and {len(regime_changes) - 10:,} more")
    
    print(f"\n{'PERFORMANCE':<50}")
    print(f"{'-'*50}")
    print(f"  Total ticks: {total_ticks:,}")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Throughput: {total_ticks/elapsed:,.0f} ticks/sec")
    print(f"  Bits processed: {bits_processed:,}")
    print(f"  Bit rate: {bits_per_sec:,.0f} bits/sec")
    print(f"  Bit rate: {bits_per_sec/1000:,.1f} Kbits/sec")
    print(f"  Bit rate: {bits_per_sec/1000000:,.3f} Mbits/sec")
    
    # Throughput analysis
    print(f"\n{'THROUGHPUT ANALYSIS':<50}")
    print(f"{'-'*50}")
    
    target_gb_per_day = 100
    target_bits_per_day = target_gb_per_day * 1024 * 1024 * 1024 * 8
    target_bits_per_sec = target_bits_per_day / (24 * 3600)
    
    measured_gb_per_day = bits_per_sec * 24 * 3600 / (1024 * 1024 * 1024 * 8)
    speedup_needed = target_bits_per_sec / bits_per_sec
    
    print(f"  Target: {target_gb_per_day} GB/day = {target_bits_per_sec:,.0f} bits/sec")
    print(f"  Measured: {measured_gb_per_day:,.4f} GB/day = {bits_per_sec:,.0f} bits/sec")
    print(f"  Speedup needed: {speedup_needed:,.0f}x")
    
    print(f"\n{'HARDWARE PROJECTIONS':<50}")
    print(f"{'-'*50}")
    
    speedups = {
        "C/C++": 50,
        "FPGA": 1000,
        "Custom ASIC": 10000,
        "MBE Hardware": 100000,
    }
    
    for hw, speedup in speedups.items():
        hw_bits_per_sec = bits_per_sec * speedup
        hw_gb_per_day = hw_bits_per_sec * 24 * 3600 / (1024 * 1024 * 1024 * 8)
        meets = "YES" if hw_gb_per_day >= target_gb_per_day else "NO"
        print(f"  {hw:<20} {speedup:>8}x -> {hw_gb_per_day:>14,.2f} GB/day [{meets}]")
    
    print(f"\n{'='*130}")
    print("TEST COMPLETE")
    print(f"{'='*130}")

if __name__ == "__main__":
    run_10m_test()
