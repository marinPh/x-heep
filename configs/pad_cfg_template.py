"""
Template for pad configuration using PadConfig interface.

This file should be passed to mcu_gen.py via --pads_cfg argument.
The config() function must return a PadRing instance.
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

    # TODO: Add your peripheral pins here
    # Example:
    # pins["uart_rx"] = Input("uart_rx", [])
    # pins["uart_tx"] = Output("uart_tx", [])

    # ==========================================================================
    # 2. Configure pad layout using PadConfig
    # ==========================================================================

    # Create configuration: adjust pad_qty and sides for your chip
    cfg = PadConfig(pad_qty=92, sides=[23, 23, 23, 23])

    # Place pins on sides
    # TODO: Configure your pad placement here
    # Example:
    # cfg.place(pins["clk"], side=PadMapping.LEFT, position=0)
    # cfg.place(pins["rst"], side=PadMapping.LEFT, position=4)
    # cfg.place_multiple(pins["VSS"], side=PadMapping.LEFT, positions=[2, 5, 10, 15])

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
    # TODO: Adjust margins, space_from_corner, and pitch for your technology
    ring_margins = [0, 0, 12.2, 24, 95]  # [empty, sealring, CDU, bondpad, pad]
    for side_pads in [left_pads, bottom_pads, right_pads, top_pads]:
        if side_pads:  # Only if side has pads
            space_by_pitch(side_pads, margins=ring_margins, space_from_corner=20, pitch=65)

    # ==========================================================================
    # 4. Create PadGroup and PadRing
    # ==========================================================================

    # TODO: Adjust floorplan dimensions for your chip
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
