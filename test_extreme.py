"""Extreme test for the Morphic Bitstream Engine - testing Phase Interrupt."""

from mbe_engine import MorphicBitstreamEngine, CTWCompressor, BoundaryDepthCalculator

# First, let's understand what Db values we're getting
db_calc = BoundaryDepthCalculator()

# Test with extreme pattern shifts
tests = [
    ("Alternating -> All 1s", [0,1,0,1,0,1,0,1], [1,1,1,1,1,1,1,1]),
    ("All 0s -> All 1s", [0,0,0,0,0,0,0,0], [1,1,1,1,1,1,1,1]),
    ("Pattern A -> Pattern B", [1,0,1,0,1,0,1,0], [0,1,0,1,0,1,0,1]),
    ("Structured -> Random-like", [0,0,0,0,1,1,1,1], [1,0,1,0,0,1,0,1]),
    ("Long history -> Short preview", [0,1] * 16, [1,1,1,1,1,1,1,1]),
]

print("=" * 70)
print("BOUNDARY DEPTH ANALYSIS")
print("=" * 70)
print()

for name, hist, prev in tests:
    db = db_calc.compute_db(hist, prev)
    print(f"{name:<35} | Db = {db:.4f}")

print()
print("=" * 70)
print("TESTING WITH EXTREMELY LONG STREAMS")
print("=" * 70)
print()

# Create engine with smaller window to detect boundaries faster
engine = MorphicBitstreamEngine(window_size=4)

# Extreme pattern: very predictable -> very chaotic
stream_A = [0,1,0,1] * 100 + [1,0,1,1,0,0,1,0] * 100  # 800 bits
stream_B = [0,0,0,0] * 200  # 800 bits

print(f"Stream A: {len(stream_A)} bits (alternating to chaotic)")
print(f"Stream B: {len(stream_B)} bits (steady zeros)")
print()

# Track regime changes
prev_regime = None
regime_changes = []

for tick in range(0, min(len(stream_A), len(stream_B)), 4):
    chunk_A = stream_A[tick:tick+4]
    chunk_B = stream_B[tick:tick+4]
    
    if len(chunk_A) < 4 or len(chunk_B) < 4:
        break
    
    result = engine.step([chunk_A, chunk_B])
    regime = result['regime']
    
    if regime != prev_regime:
        regime_changes.append((tick//4, regime, result['db_values']))
        prev_regime = regime

print(f"Total ticks: {len(stream_A) // 4}")
print(f"Regime changes: {len(regime_changes)}")
print()

for tick, regime, db_vals in regime_changes:
    print(f"  Tick {tick:>4}: {regime:<25} | Db = [{db_vals[0]:.2f}, {db_vals[1]:.2f}]")
