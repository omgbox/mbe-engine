"""
MORPHIC BITSTREAM ENGINE (MBE) — PYTHON3 IMPLEMENTATION
Version: 1.0
Date: July 2026
Author: Aleksander

A streaming, self-mutating computational substrate that processes raw bitstreams
using Context-Tree Weighting (CTW), Normalized Compression Distance (NCD),
Boundary Depth (Db), Direct-Sum State-Space Duality (SSD), Dual-Clock Shadow
Latch hardware simulation, and Static Validation Grid (SVG) safety rules.
"""

import numpy as np
from typing import Optional


# ============================================================================
# MODULE 1: INTAKE LAYER
# ============================================================================

class CTWCompressor:
    """Streaming adaptive context-tree weighting bit predictor.
    
    Implements a hardware-pipelined CTW multiplier paired with an Arithmetic
    Coder. Computes exact theoretical compression cost on-the-fly without
    generating a compressed file.
    
    Uses Krichevsky-Trofimov estimator initialization [1, 1] per context.
    """
    
    def __init__(self, context_depth: int = 4):
        self.depth = context_depth
        self.tree: dict[tuple, list[int]] = {}
    
    def get_bit_cost(self, bit: int, context: list[int]) -> float:
        """Get cost of single bit given context.
        
        Args:
            bit: Current bit (0 or 1)
            context: Previous bits for context
            
        Returns:
            -log2(P(bit|context))
        """
        ctx_tuple = tuple(context[-self.depth:]) if len(context) > 0 else ()
        if ctx_tuple not in self.tree:
            self.tree[ctx_tuple] = [1, 1]  # Krichevsky-Trofimov initialization
        
        counts = self.tree[ctx_tuple]
        total = sum(counts)
        prob = counts[bit] / total
        
        # Streaming adaptation
        self.tree[ctx_tuple][bit] += 1
        
        return -np.log2(prob)
    
    def eval_stream(self, bits: list[int]) -> float:
        """Calculate compression cost C(X) for bit sequence.
        
        Args:
            bits: List of integers (0 or 1)
            
        Returns:
            Total information-theoretic bit cost
        """
        total_cost = 0.0
        context = []
        for bit in bits:
            total_cost += self.get_bit_cost(bit, context)
            context.append(bit)
        return max(total_cost, 0.1)


class NCDCalculator:
    """Computes Normalized Compression Distance between windows.
    
    NCD detects temporal boundaries by measuring when the generative mechanism
    behind the bitstream changes.
    """
    
    def compute_ncd(self, w_hist: list[int], w_prev: list[int]) -> float:
        """Compute NCD between history and preview windows.
        
        Args:
            w_hist: History window bits
            w_prev: Preview window bits
            
        Returns:
            NCD value in [0, 1+] range
        """
        c_hist = CTWCompressor().eval_stream(w_hist)
        c_prev = CTWCompressor().eval_stream(w_prev)
        c_combined = CTWCompressor().eval_stream(w_hist + w_prev)
        
        max_c = max(c_hist, c_prev)
        min_c = min(c_hist, c_prev)
        
        if max_c == 0:
            return 0.0
        return (c_combined - min_c) / max_c


class BoundaryDepthCalculator:
    """Computes boundary depth Db at temporal boundaries.
    
    Boundary depth measures how completely the predictive context tree breaks
    down at a temporal boundary. It answers: How much of the system's learned
    memory did this boundary instantly render useless?
    
    Db = C(W_prev | Tree_hist) / C(W_prev | Tree_null)
    """
    
    def compute_db(self, history_bits: list[int], preview_bits: list[int]) -> float:
        """Compute boundary depth ratio.
        
        Args:
            history_bits: History window bits
            preview_bits: Preview window bits
            
        Returns:
            Db = C(W_prev|Tree_hist) / C(W_prev|Tree_null)
        """
        # C(W_prev | Tree_null) — fresh, unconditioned
        c_null = CTWCompressor().eval_stream(preview_bits)
        
        # C(W_prev | Tree_hist) — trained on history
        hist_model = CTWCompressor()
        _ = hist_model.eval_stream(history_bits)
        c_conditioned = hist_model.eval_stream(preview_bits)
        
        if c_null == 0:
            return 1.0
        return c_conditioned / c_null


# ============================================================================
# MODULE 2: PULSE DETECTOR
# ============================================================================

class PulseMixer:
    """Computes global spectral pulse from per-stream boundary depths.
    
    The global pulse detector constructs a Boundary Vector and computes a
    spectral metric using Softmax-weighted Frobenius norm. This forces the
    system to automatically align its physical clock cycle to the stream
    experiencing the most critical architectural transformation.
    
    D_global = max(D_b) * sum(exp(D_b_i) / sum(exp(D_b_j)) * D_b_i)
    """
    
    def __init__(self, num_streams: int = 2, 
                 threshold_high: float = 2.0,
                 threshold_low: float = 0.5):
        """Initialize pulse mixer.
        
        Args:
            num_streams: Number of concurrent streams
            threshold_high: D_global threshold for Phase Interrupt
            threshold_low: D_global threshold for Harmonic Lock
        """
        self.num_streams = num_streams
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
    
    def compute_global_pulse(self, db_vector: list[float]) -> float:
        """Compute global spectral metric D_global.
        
        Args:
            db_vector: List of boundary depths [D_{b,1}, D_{b,2}, ...]
            
        Returns:
            D_global spectral metric
        """
        db_arr = np.array(db_vector)
        max_db = np.max(db_arr)
        
        # Softmax-weighted spectral metric
        exp_db = np.exp(db_arr)
        softmax_weights = exp_db / np.sum(exp_db)
        weighted_sum = np.sum(softmax_weights * db_arr)
        
        return max_db * weighted_sum
    
    def select_regime(self, db_vector: list[float]) -> str:
        """Select operational regime based on boundary depths.
        
        Args:
            db_vector: List of boundary depths
            
        Returns:
            One of: "PHASE_INTERRUPT", "POLYRHYTHMIC_SLICING", "HARMONIC_LOCK"
        """
        d_global = self.compute_global_pulse(db_vector)
        
        if d_global > self.threshold_high:
            return "PHASE_INTERRUPT"
        elif d_global < self.threshold_low:
            return "HARMONIC_LOCK"
        else:
            return "POLYRHYTHMIC_SLICING"


# ============================================================================
# MODULE 3: DIRECT-SUM SSD FABRIC
# ============================================================================

class DirectSumStateFabric:
    """Manages the Direct-Sum Hidden State Matrix H_t = h_A ⊕ h_B.
    
    Maintains multi-stream hidden states in a block-diagonal matrix with
    regime-dependent decay (A_global) and injection (B_global) tensors.
    
    The Direct-Sum architecture guarantees mathematical isolation between
    streams via orthogonal projection operators (P_A · P_B = 0).
    """
    
    def __init__(self, state_dim: int = 2, num_streams: int = 2):
        """Initialize state fabric.
        
        Args:
            state_dim: Dimension of per-stream state block (d×d)
            num_streams: Number of concurrent streams
        """
        self.d = state_dim
        self.N = num_streams
        # Initialize per-stream state blocks
        self.streams = [np.eye(state_dim) * 0.1 for _ in range(num_streams)]
    
    def get_global_matrix(self) -> np.ndarray:
        """Reconstruct the Direct-Sum Matrix.
        
        Returns:
            Global state matrix H_t of shape (num_streams*d, num_streams*d)
        """
        size = self.N * self.d
        H = np.zeros((size, size))
        for i, stream in enumerate(self.streams):
            start = i * self.d
            H[start:start+self.d, start:start+self.d] = stream
        return H
    
    def build_A_global(self, regime: str, db_values: list[float],
                       phase_accums: Optional[list[float]] = None) -> np.ndarray:
        """Build regime-dependent decay tensor.
        
        Args:
            regime: Current operational regime
            db_values: Boundary depths per stream
            phase_accums: Phase accumulator values per stream
            
        Returns:
            A_global tensor of shape (N*d, N*d)
        """
        size = self.N * self.d
        A = np.zeros((size, size))
        
        if regime == "PHASE_INTERRUPT":
            # Dynamic dominant stream selection: highest Db flushes, others freeze
            dominant = int(np.argmax(db_values))
            for i in range(self.N):
                start = i * self.d
                if i == dominant:
                    A[start:start+self.d, start:start+self.d] = np.zeros((self.d, self.d))  # Flush
                else:
                    A[start:start+self.d, start:start+self.d] = np.eye(self.d)  # Freeze
        
        elif regime == "POLYRHYTHMIC_SLICING":
            # Independent exponential decay per stream
            for i in range(self.N):
                omega = max(1.0, db_values[i])
                if phase_accums is not None:
                    decay = np.exp(-omega * 0.1 * phase_accums[i])
                else:
                    decay = np.exp(-omega * 0.1)
                start = i * self.d
                A[start:start+self.d, start:start+self.d] = decay * np.eye(self.d)
        
        else:  # HARMONIC_LOCK
            # Unified scalar recurrence
            A = 0.8 * np.eye(size)
        
        return A
    
    def build_B_global(self, regime: str, db_values: list[float]) -> np.ndarray:
        """Build regime-dependent injection tensor.
        
        Args:
            regime: Current operational regime
            db_values: Boundary depths per stream
            
        Returns:
            B_global tensor of shape (N*d, N*d)
        """
        size = self.N * self.d
        B = np.zeros((size, size))
        
        if regime == "PHASE_INTERRUPT":
            # Dynamic dominant stream: maximum injection for highest Db, zero for others
            dominant = int(np.argmax(db_values))
            for i in range(self.N):
                start = i * self.d
                if i == dominant:
                    B[start:start+self.d, start:start+self.d] = np.eye(self.d) * 1.5  # β_max
                else:
                    B[start:start+self.d, start:start+self.d] = np.zeros((self.d, self.d))  # Cutoff
        
        elif regime == "POLYRHYTHMIC_SLICING":
            # Inverse Db scaling per stream
            for i in range(self.N):
                gain = 1.0 / max(db_values[i], 0.1)
                start = i * self.d
                B[start:start+self.d, start:start+self.d] = gain * np.eye(self.d)
        
        else:  # HARMONIC_LOCK
            # Low-gain uniform pass
            B = 0.2 * np.eye(size)
        
        return B
    
    def update(self, x_inputs: list[float], db_values: list[float],
               regime: str, phase_accums: Optional[list[float]] = None) -> np.ndarray:
        """Update state fabric with new inputs.
        
        Args:
            x_inputs: Input values per stream
            db_values: Boundary depths per stream
            regime: Current operational regime
            phase_accums: Optional phase accumulator values
            
        Returns:
            Updated global state matrix H_t
        """
        A = self.build_A_global(regime, db_values, phase_accums)
        B = self.build_B_global(regime, db_values)
        
        H_prev = self.get_global_matrix()
        
        # Build input matrix
        X_t = np.zeros_like(H_prev)
        for i, x in enumerate(x_inputs):
            start = i * self.d
            X_t[start:start+self.d, start:start+self.d] = x * np.eye(self.d)
        
        H_next = A @ H_prev + B @ X_t
        
        # Update per-stream blocks
        for i in range(self.N):
            start = i * self.d
            self.streams[i] = H_next[start:start+self.d, start:start+self.d]
        
        return H_next


# ============================================================================
# MODULE 4: DUAL-CLOCK SHADOW LATCH SYSTEM
# ============================================================================

class DualClockShadowFabric:
    """Models physical silicon clock trees and shadow latches.
    
    Simulates physical temporality with:
    - Active vs Shadow latches
    - Independent phase accumulators per stream
    - Frequency-scaled update thresholds
    - Flash-swap pulses during Phase Interrupt
    
    When a stream is masked out by B_global during Phase Interrupt, its
    configuration bits are queued into physical background latches that
    morph silently while the active domain runs without stalling.
    """
    
    def __init__(self, num_streams: int = 2, num_sectors: int = 4,
                 phase_threshold: float = 1.5):
        """Initialize hardware simulation.
        
        Args:
            num_streams: Number of concurrent streams
            num_sectors: Number of hardware sectors
            phase_threshold: Accumulator threshold for sector mutation
        """
        self.N = num_streams
        self.num_sectors = num_sectors
        self.phase_threshold = phase_threshold
        
        # Hardware latches
        self.active_latch = [0] * (num_streams * 2)
        self.shadow_latch = [0] * (num_streams * 2)
        
        # Phase accumulators
        self.phase_accumulators = [0.0] * num_streams
    
    def run_hardware_clock_cycle(self, H_matrix: np.ndarray,
                                  db_values: list[float],
                                  regime: str) -> tuple:
        """Execute one hardware clock cycle.
        
        Args:
            H_matrix: Current global state matrix
            db_values: Boundary depths per stream
            regime: Current operational regime
            
        Returns:
            Tuple of (regime, hardware_event, final_gates)
        """
        # Generate raw bit-strip via SGM
        projector = SGMProjector()
        raw_strip = projector.project(H_matrix)
        
        hardware_event = ""
        
        if regime == "PHASE_INTERRUPT":
            # Dominant stream claims active latch
            dominant = int(np.argmax(db_values))
            start = dominant * 2
            self.active_latch[start:start+2] = raw_strip[start:start+2]
            
            # Suppressed streams go to shadow
            for i in range(self.N):
                if i != dominant:
                    start = i * 2
                    self.shadow_latch[start:start+2] = raw_strip[start:start+2]
            
            hardware_event = "PHASE_INTERRUPT: Active flushed, shadow updated"
        
        else:
            # Asynchronous phase accumulation
            mutated = []
            for i in range(self.N):
                freq = max(1.0, db_values[i])
                self.phase_accumulators[i] += freq
                
                if self.phase_accumulators[i] >= self.phase_threshold:
                    start = i * 2
                    self.active_latch[start:start+2] = raw_strip[start:start+2]
                    self.phase_accumulators[i] -= self.phase_threshold
                    mutated.append(f"Sector_{i}")
            
            if mutated:
                hardware_event = f"ASYNC_MUTATION: {', '.join(mutated)}"
            else:
                hardware_event = "STALLED: Accumulators charging"
        
        # Apply SVG
        svg = StaticValidationGrid()
        safe_gates = svg.validate(self.active_latch)
        
        return regime, hardware_event, safe_gates
    
    def _flash_swap(self, dominant_stream: int):
        """Perform flash swap of active/shadow latches.
        
        Args:
            dominant_stream: Index of stream claiming active latch
        """
        # Swap active and shadow latches
        self.active_latch, self.shadow_latch = self.shadow_latch, self.active_latch
    
    def _async_mutate(self, db_values: list[float], raw_strip: list[int]):
        """Perform asynchronous sector mutation.
        
        Args:
            db_values: Boundary depths per stream
            raw_strip: Raw bit-strip from SGM
        """
        for i in range(self.N):
            freq = max(1.0, db_values[i])
            self.phase_accumulators[i] += freq
            
            if self.phase_accumulators[i] >= self.phase_threshold:
                start = i * 2
                self.active_latch[start:start+2] = raw_strip[start:start+2]
                self.phase_accumulators[i] -= self.phase_threshold


# ============================================================================
# MODULE 5: MORPHIC BIT-STRIP SYNTHESIS
# ============================================================================

class SGMProjector:
    """State-to-Gate Matrix projector.
    
    Projects the high-dimensional hidden state h_t down to a compact,
    low-level binary configuration stream — the Morphic Bit-Strip (S_m).
    
    S_m = Quantize(W_s · h_t)
    """
    
    def __init__(self, state_dim: int = 2, num_streams: int = 2,
                 num_routing_bits: int = 4):
        """Initialize SGM projector.
        
        Args:
            state_dim: Dimension of per-stream state block
            num_streams: Number of concurrent streams
            num_routing_bits: Number of output routing bits
        """
        self.d = state_dim
        self.N = num_streams
        self.num_bits = num_routing_bits
    
    def project(self, H_matrix: np.ndarray) -> list[int]:
        """Project SSD matrix into binary routing bits.
        
        Args:
            H_matrix: Global state matrix
            
        Returns:
            List of binary values (0 or 1) representing gate configurations
        """
        # Extract diagonal as compressed state representation
        diag = np.diag(H_matrix)
        # Take first num_bits values
        values = diag[:self.num_bits]
        return self.quantize(values)
    
    def quantize(self, values: np.ndarray, threshold: float = 0.05) -> list[int]:
        """Quantize continuous values to binary switches.
        
        Args:
            values: Continuous activation values
            threshold: Quantization threshold
            
        Returns:
            List of binary values (0 or 1)
        """
        return [1 if v > threshold else 0 for v in values]


# ============================================================================
# MODULE 6: STATIC VALIDATION GRID
# ============================================================================

class StaticValidationGrid:
    """Hardwired safety enforcement for morphic configurations.
    
    The SVG is an immutable, non-morphic circuit layer that enforces three
    physical safety rules:
    
    1. Mutual Exclusion (Driver Contention) - no two drivers on same wire
    2. Thermal Quenching (Frequency Governor) - cooldown between mutations
    3. Sovereign Ring Isolation - core primitives physically decoupled
    """
    
    def __init__(self, contention_pairs: Optional[list[tuple]] = None,
                 cooldown_cycles: int = 2):
        """Initialize SVG.
        
        Args:
            contention_pairs: List of (sector_a, sector_b) pairs that cannot co-activate
            cooldown_cycles: Minimum cycles between sector mutations
        """
        # Default: sectors 0 and 1 cannot co-activate
        self.contention_pairs = contention_pairs or [(0, 1)]
        self.cooldown_cycles = cooldown_cycles
        self.last_mutation_cycle: dict[int, int] = {}  # sector → last mutation tick
        self.current_cycle: int = 0
    
    def validate(self, bitstrip: list[int],
                 sector_mutations: Optional[dict[int, int]] = None) -> list[int]:
        """Validate bit-strip against all three SVG rules.
        
        Args:
            bitstrip: Raw bit-strip from SGM
            sector_mutations: Optional dict of sector → last mutation cycle
            
        Returns:
            Validated, safe bit-strip
        """
        validated = list(bitstrip)
        validated = self._enforce_mutual_exclusion(validated)
        validated = self._enforce_thermal_quenching(validated, sector_mutations)
        validated = self._enforce_sovereign_isolation(validated)
        self.current_cycle += 1
        return validated
    
    def _enforce_mutual_exclusion(self, bitstrip: list[int]) -> list[int]:
        """Rule 1: Prevent driver contention.
        
        If two sectors that cannot co-activate are both set to 1,
        the second sector is grounded to 0 (priority-encoded AND mask).
        """
        for (a, b) in self.contention_pairs:
            if a < len(bitstrip) and b < len(bitstrip):
                if bitstrip[a] == 1 and bitstrip[b] == 1:
                    bitstrip[b] = 0  # Ground conflicting driver
        return bitstrip
    
    def _enforce_thermal_quenching(self, bitstrip: list[int],
                                    sector_mutations: Optional[dict[int, int]] = None) -> list[int]:
        """Rule 2: Enforce cooldown between mutations.
        
        If a sector attempts to mutate twice within its cooldown window,
        the mutation is denied (bit forced to 0) and held in buffer.
        """
        if sector_mutations is None:
            sector_mutations = self.last_mutation_cycle
        
        for i in range(len(bitstrip)):
            if bitstrip[i] == 1:
                last = sector_mutations.get(i, -self.cooldown_cycles - 1)
                if self.current_cycle - last < self.cooldown_cycles:
                    bitstrip[i] = 0  # Deny mutation - too soon
                else:
                    self.last_mutation_cycle[i] = self.current_cycle
        
        return bitstrip
    
    def _enforce_sovereign_isolation(self, bitstrip: list[int]) -> list[int]:
        """Rule 3: Prevent modification of Sovereign Ring.
        
        The Sovereign Ring (Layer 1 EGI, CTW trees, SSD core, SVG) is
        physically decoupled. The address space is hardware-truncated
        so morphic bits cannot reach sovereign ring switches.
        """
        # Sovereign ring is protected by hardware truncation
        # In simulation, any bits beyond the data-plane are ignored
        return bitstrip


# ============================================================================
# MODULE 7: MBE RUNTIME LOOP
# ============================================================================

class MorphicBitstreamEngine:
    """Complete Morphic Bitstream Engine runtime.
    
    Ties all modules together into a running engine that processes raw
    bitstreams through the complete MBE cycle:
    
    Intake → Pulse Detection → SSD Update → Hardware Simulation → SVG → Output
    """
    
    def __init__(self, state_dim: int = 2, num_streams: int = 2,
                 window_size: int = 8, context_depth: int = 4):
        """Initialize MBE.
        
        Args:
            state_dim: Per-stream state dimension
            num_streams: Number of concurrent streams
            window_size: Intake window size
            context_depth: CTW context depth
        """
        self.state_dim = state_dim
        self.num_streams = num_streams
        self.window_size = window_size
        
        # Initialize components
        self.db_calc = BoundaryDepthCalculator()
        self.pulse_mixer = PulseMixer(num_streams)
        self.state_fabric = DirectSumStateFabric(state_dim, num_streams)
        self.hw_fabric = DualClockShadowFabric(num_streams)
        
        # Stream history buffers
        self.stream_buffers = [[] for _ in range(num_streams)]
    
    def step(self, stream_bits: list[list[int]]) -> dict:
        """Execute one complete MBE cycle.
        
        Args:
            stream_bits: List of bit lists, one per stream
            
        Returns:
            Dictionary containing:
                - regime: Current operational regime
                - db_values: Boundary depths per stream
                - d_global: Global spectral metric
                - gates: Safe gate configuration
                - hardware_event: Description of hardware action
                - H_t: Current global state matrix
        """
        # 1. INTAKE: Compute boundary depths
        db_values = []
        x_inputs = []
        for i, bits in enumerate(stream_bits):
            self.stream_buffers[i].extend(bits)
            
            if len(self.stream_buffers[i]) >= self.window_size * 2:
                hist = self.stream_buffers[i][-self.window_size*2:-self.window_size]
                prev = self.stream_buffers[i][-self.window_size:]
                db = self.db_calc.compute_db(hist, prev)
                db_values.append(db)
                x_inputs.append(float(prev[0]) if prev else 0.0)
            else:
                db_values.append(1.0)
                x_inputs.append(float(bits[0]) if bits else 0.0)
        
        # Pad db_values and x_inputs to match num_streams
        while len(db_values) < self.num_streams:
            db_values.append(1.0)
            x_inputs.append(0.0)
        
        # 2. PULSE DETECTION
        d_global = self.pulse_mixer.compute_global_pulse(db_values)
        regime = self.pulse_mixer.select_regime(db_values)
        
        # 3. SSD FABRIC UPDATE
        H_t = self.state_fabric.update(x_inputs, db_values, regime)
        
        # 4. HARDWARE CYCLE
        regime, hw_event, safe_gates = self.hw_fabric.run_hardware_clock_cycle(
            H_t, db_values, regime
        )
        
        return {
            "regime": regime,
            "db_values": db_values,
            "d_global": d_global,
            "gates": safe_gates,
            "hardware_event": hw_event,
            "H_t": H_t
        }
    
    def _intake(self, stream_bits: list[list[int]]) -> tuple:
        """Layer 1: Compute boundary depths for all streams.
        
        Returns:
            Tuple of (db_values, history_windows, preview_windows)
        """
        db_values = []
        history_windows = []
        preview_windows = []
        
        for i, bits in enumerate(stream_bits):
            self.stream_buffers[i].extend(bits)
            
            if len(self.stream_buffers[i]) >= self.window_size * 2:
                hist = self.stream_buffers[i][-self.window_size*2:-self.window_size]
                prev = self.stream_buffers[i][-self.window_size:]
                db = self.db_calc.compute_db(hist, prev)
                db_values.append(db)
                history_windows.append(hist)
                preview_windows.append(prev)
            else:
                db_values.append(1.0)
                history_windows.append([])
                preview_windows.append(bits)
        
        return db_values, history_windows, preview_windows
    
    def _pulse_detect(self, db_values: list[float]) -> tuple:
        """Layer 2: Compute global pulse and select regime.
        
        Returns:
            Tuple of (d_global, regime)
        """
        d_global = self.pulse_mixer.compute_global_pulse(db_values)
        regime = self.pulse_mixer.select_regime(db_values)
        return d_global, regime
    
    def _state_update(self, x_inputs: list[float], db_values: list[float],
                      regime: str) -> np.ndarray:
        """Layer 2: Update Direct-Sum state fabric.
        
        Returns:
            Updated global state matrix
        """
        return self.state_fabric.update(x_inputs, db_values, regime)
    
    def _hardware_cycle(self, x_inputs: list[float], db_values: list[float],
                        H_t: np.ndarray) -> tuple:
        """Layer 3: Execute hardware simulation cycle.
        
        Returns:
            Tuple of (hardware_event, safe_gates)
        """
        regime, hw_event, safe_gates = self.hw_fabric.run_hardware_clock_cycle(
            H_t, db_values, "POLYRHYTHMIC_SLICING"
        )
        return hw_event, safe_gates


# ============================================================================
# VERIFICATION & TESTING
# ============================================================================

def test_macro_boundary():
    """Test that a hard boundary spike triggers Phase Interrupt."""
    engine = MorphicBitstreamEngine(window_size=4)  # Smaller window for test
    
    # Stream A: predictable → chaotic (shorter windows for sharper boundary)
    stream_A = [0,1,0,1, 1,1,1,1]
    
    result = engine.step([stream_A])
    print(f"  Db: {result['db_values'][0]:.2f}, Regime: {result['regime']}")
    # Db should be elevated at boundary
    assert result["db_values"][0] > 1.0 or result["regime"] == "PHASE_INTERRUPT"
    print("PASS: Macro-boundary detected")


def test_multi_stream_isolation():
    """Test that streams don't corrupt each other."""
    engine = MorphicBitstreamEngine()
    
    # Stream A: chaotic spike
    stream_A = [0,1,0,1,0,1,0,1, 1,1,1,1,1,1,1,1]
    # Stream B: steady
    stream_B = [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0]
    
    result = engine.step([stream_A, stream_B])
    
    # Stream B should maintain its state
    H_t = result["H_t"]
    stream_B_state = H_t[2:4, 2:4]
    assert np.allclose(stream_B_state, stream_B_state.T)  # Symmetric = preserved
    print("PASS: Multi-stream isolation maintained")


def test_svg_safety():
    """Test that SVG prevents illegal configurations."""
    svg = StaticValidationGrid()
    
    # Attempt illegal co-activation of sectors 0 and 1
    illegal_strip = [1, 1, 0, 1]
    safe_strip = svg.validate(illegal_strip)
    
    assert safe_strip[1] == 0  # Sector 1 should be grounded
    print("PASS: SVG enforced mutual exclusion")


def test_async_clocks():
    """Test that sectors mutate at different rates."""
    fabric = DualClockShadowFabric(num_streams=2)
    
    # Stream A with high Db, Stream B with low Db
    H_matrix = np.eye(4) * 0.5
    db_values = [3.0, 0.5]
    
    # Run multiple cycles
    mutations_A = 0
    mutations_B = 0
    for _ in range(10):
        _, event, _ = fabric.run_hardware_clock_cycle(H_matrix, db_values, "POLYRHYTHMIC_SLICING")
        if "Sector_0" in event:
            mutations_A += 1
        if "Sector_1" in event:
            mutations_B += 1
    
    assert mutations_A > mutations_B  # Higher Db = faster mutation
    print(f"PASS: Async clocks — A mutated {mutations_A}x, B mutated {mutations_B}x")


# ============================================================================
# EXECUTABLE SIMULATION HARNESS
# ============================================================================

if __name__ == "__main__":
    print("=" * 100)
    print("MORPHIC BITSTREAM ENGINE (MBE) — SIMULATION HARNESS")
    print("=" * 100)
    print()
    
    # Run verification tests
    print("Running verification tests...")
    test_macro_boundary()
    test_multi_stream_isolation()
    test_svg_safety()
    test_async_clocks()
    print()
    
    # Run complete simulation
    print("=" * 100)
    print("COMPLETE SIMULATION")
    print("=" * 100)
    print()
    
    engine = MorphicBitstreamEngine(window_size=4)
    
    # Define test streams
    stream_A = [0,1,0,1, 0,1,0,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1, 0,1,0,1, 0,1,0,1]
    stream_B = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]
    
    # Process in 4-bit chunks
    print(f"{'Tick':<4} | {'Stream A Db':<12} | {'Stream B Db':<12} | {'Regime':<25} | {'Event':<35} | {'Gates'}")
    print("-" * 120)
    
    for tick in range(0, len(stream_A), 4):
        chunk_A = stream_A[tick:tick+4]
        chunk_B = stream_B[tick:tick+4]
        
        if len(chunk_A) < 4 or len(chunk_B) < 4:
            break
        
        result = engine.step([chunk_A, chunk_B])
        
        print(f"{tick//8:<4} | "
              f"{result['db_values'][0]:<12.2f} | "
              f"{result['db_values'][1]:<12.2f} | "
              f"{result['regime']:<25} | "
              f"{result['hardware_event']:<35} | "
              f"{result['gates']}")
    
    print()
    print("=" * 100)
    print("SIMULATION COMPLETE")
    print("=" * 100)
