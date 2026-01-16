"""
Complete working pad configuration using PadConfig interface.

This demonstrates a minimal but complete pad configuration that can be used with mcu_gen.
"""

import sys
from pathlib import Path

# Add util to path for imports
sys.path.append(str(Path(__file__).parent.parent / "util"))

from x_heep_gen.pads.pin import (
    Input, Output, Inout, DVdd, DVss,
    PadConfig, PadMapping,
    space_by_pitch
)
from x_heep_gen.pads.PadDef import PadGroup, Dimension
from x_heep_gen.pads.PadRing import PadRing


def config() -> PadRing:
    """
    Configuration function called by load_config.load_pad_cfg().

    Must return a built PadRing instance.
    """

    # ==========================================================================
    # 1. Create pins with physical attributes
    # ==========================================================================

    pins = {}

    # System pins
    pins["clk"] = Input("clk", [], {"driven_manually": True})
    pins["rst"] = Input("rst", [], {"active": "low", "driven_manually": True})

    # Supply pins
    pins["VSS"] = DVss("VSS", [], {"default": True})
    pins["VDD"] = DVdd("VDD", [])

    # UART pins
    pins["uart_rx"] = Input("uart_rx", [])
    pins["uart_tx"] = Output("uart_tx", [])

    # GPIO pins (just 4 for this minimal example)
    for i in range(4):
        pins[f"gpio_{i}"] = Inout(f"gpio_{i}", [])

    # ==========================================================================
    # 2. Configure pad layout using PadConfig
    # ==========================================================================

    # Create configuration: 92 pads, 23 per side
    cfg = PadConfig(pad_qty=92, sides=[23, 23, 23, 23])

    # LEFT SIDE - System and supplies
    cfg.place(pins["clk"], side=PadMapping.LEFT, position=0)
    cfg.place(pins["rst"], side=PadMapping.LEFT, position=4)
    cfg.place_multiple(pins["VSS"], side=PadMapping.LEFT, positions=[2, 5, 10, 15, 20])
    cfg.place_multiple(pins["VDD"], side=PadMapping.LEFT, positions=[3, 11])

    # BOTTOM SIDE - UART
    cfg.place(pins["uart_tx"], side=PadMapping.BOTTOM, position=0)
    cfg.place(pins["uart_rx"], side=PadMapping.BOTTOM, position=1)
    cfg.place_multiple(pins["VSS"], side=PadMapping.BOTTOM, positions=[5, 12, 19])
    cfg.place(pins["VDD"], side=PadMapping.BOTTOM, position=13)

    # RIGHT SIDE - Supplies
    cfg.place_multiple(pins["VSS"], side=PadMapping.RIGHT, positions=[10, 15, 20])
    cfg.place(pins["VDD"], side=PadMapping.RIGHT, position=11)

    # TOP SIDE - GPIOs
    for i in range(4):
        cfg.place(pins[f"gpio_{i}"], side=PadMapping.TOP, position=i)
    cfg.place_multiple(pins["VSS"], side=PadMapping.TOP, positions=[10, 15, 20])
    cfg.place(pins["VDD"], side=PadMapping.TOP, position=16)

    # Set default pin for unassigned pads
    cfg.set_default(pins["VSS"])

    # Validate and build
    if not cfg.validate():
        raise ValueError("Pad configuration validation failed")

    pads = cfg.build()

    # ==========================================================================
    # 3. Calculate physical spacing (optional - for ASIC layout)
    # ==========================================================================

    # Extract pads by side
    left_pads = [p for p in pads[1:] if p.mapping == PadMapping.LEFT]
    bottom_pads = [p for p in pads[1:] if p.mapping == PadMapping.BOTTOM]
    right_pads = [p for p in pads[1:] if p.mapping == PadMapping.RIGHT]
    top_pads = [p for p in pads[1:] if p.mapping == PadMapping.TOP]

    # Configure spacing per side
    ring_margins = [0, 0, 12.2, 24, 95]  # [empty, sealring, CDU, bondpad, pad]
    for side_pads in [left_pads, bottom_pads, right_pads, top_pads]:
        if side_pads:  # Only if side has pads
            space_by_pitch(side_pads, margins=ring_margins, space_from_corner=20, pitch=65)

    # ==========================================================================
    # 4. Create PadGroup and PadRing
    # ==========================================================================

    pad_group = PadGroup(
        name="x_heep_top",
        fp_dim=Dimension(width=2000, length=2000),
    )

    # Add all pads to group
    for pad in pads[1:]:
        pad_group.add_pad(pad)

    # Build and return PadRing
    padring = PadRing(pad_group)
    padring.build()

    return padring


# Allow testing standalone
if __name__ == "__main__":
    print("Building pad configuration...")
    padring = config()
    print(f"✓ PadRing built successfully")
    print(f"  - Total pads: {len(padring.pad_list)}")
    print(f"  - Muxed pads: {len(padring.pad_muxed_list)}")
    print(f"  - Top: {len(padring.top_pad_list)}, Right: {len(padring.right_pad_list)}")
    print(f"  - Bottom: {len(padring.bottom_pad_list)}, Left: {len(padring.left_pad_list)}")
