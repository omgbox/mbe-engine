"""Large-scale test for the Morphic Bitstream Engine."""

from mbe_engine import MorphicBitstreamEngine
import numpy as np

engine = MorphicBitstreamEngine(window_size=8)

# Larger test streams with multiple boundaries
stream_A = (
    [0,1,0,1,0,1,0,1] * 4 +   # Pattern 1: alternating (32 bits)
    [1,1,1,1,1,1,1,1] * 4 +   # Pattern 2: all ones (32 bits)
    [0,0,0,0,0,0,0,0] * 4 +   # Pattern 3: all zeros (32 bits)
    [1,0,0,1,1,0,0,1] * 4     # Pattern 4: repeating block (32 bits)
)

stream_B = (
    [0,0,0,0,0,0,0,0] * 8 +   # Steady: all zeros (64 bits)
    [1,1,1,1,1,1,1,1] * 4 +   # Shift: all ones (32 bits)
    [0,0,0,0,0,0,0,0] * 4     # Return: all zeros (32 bits)
)

print("=" * 130)
print("MBE LARGE-SCALE TEST")
print("=" * 130)
print(f"Stream A: {len(stream_A)} bits (4 pattern shifts)")
print(f"Stream B: {len(stream_B)} bits (2 pattern shifts)")
print("=" * 130)
print()

header = f"{'Tick':<5} | {'A Db':<8} | {'B Db':<8} | {'D_global':<10} | {'Regime':<25} | {'Event':<40} | {'Gates'}"
print(header)
print("-" * 140)

phase_interrupts = 0
polyrhythmic = 0
harmonic = 0
total_ticks = 0

for tick in range(0, min(len(stream_A), len(stream_B)), 8):
    chunk_A = stream_A[tick:tick+8]
    chunk_B = stream_B[tick:tick+8]
    
    if len(chunk_A) < 8 or len(chunk_B) < 8:
        break
    
    result = engine.step([chunk_A, chunk_B])
    
    regime = result['regime']
    if regime == 'PHASE_INTERRUPT':
        phase_interrupts += 1
    elif regime == 'POLYRHYTHMIC_SLICING':
        polyrhythmic += 1
    else:
        harmonic += 1
    total_ticks += 1
    
    db_a = result['db_values'][0]
    db_b = result['db_values'][1]
    d_global = result['d_global']
    event = result['hardware_event']
    gates = result['gates']
    
    print(f"{tick//8:<5} | {db_a:<8.2f} | {db_b:<8.2f} | {d_global:<10.2f} | {regime:<25} | {event:<40} | {gates}")

print()
print("=" * 130)
print("STATISTICS")
print("=" * 130)
print(f"Total ticks: {total_ticks}")
print(f"Phase Interrupts: {phase_interrupts} ({100*phase_interrupts/total_ticks:.1f}%)")
print(f"Polyrhythmic Slicing: {polyrhythmic} ({100*polyrhythmic/total_ticks:.1f}%)")
print(f"Harmonic Lock: {harmonic} ({100*harmonic/total_ticks:.1f}%)")
print()
print("STATE MATRIX (Final H_t):")
print(result['H_t'])
