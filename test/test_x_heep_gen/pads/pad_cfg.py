from typing import Dict, List, Tuple
import sys

from util.x_heep_gen.pads.Pad_domain import pad, rng, mux, _mk_cfg

_PHYS = {
    "floorplan_dimensions": {"width": 2000, "length": 1500},
    "edge_offset": {"bondpad": 20, "pad": 90},
    "spacing": {"bondpad": 25},
    "dimensions": {
        "BONDPAD1": {"width": 50},
        "BONDPAD2": {"width": 60},
        "BONDPAD3": {"width": 70},
        "BONDPAD4": {"width": 80},
        "PAD1": {"width": 40},
        "PAD2": {"width": 45},
        "PAD3": {"width": 50},
        "PAD4": {"width": 55},
    },
}

# ---- Pads (converted 1:1) ---------------------------------------------------

_ALL = [
    pad("clk", "input",
        mapping="right",
        layout_attributes={"index": 0, "cell": "PAD1", "orient": "r90", "bondpad": "BONDPAD1"}),

    pad("rst", "input",
        active="low", driven_manually=True,
        mapping="right",
        layout_attributes={"index": 1, "cell": "PAD2", "orient": "r90", "bondpad": "BONDPAD2"}),

    mux("pdm2pcm_clk", "inout",
        alts=[("pdm2pcm_clk", "inout"), ("gpio_19", "inout")],
        mapping="right",
        layout_attributes={"index": 2, "cell": "PAD3", "orient": "r90", "bondpad": "BONDPAD3"}),

    pad("boot_select", "input",
        mapping="right",
        layout_attributes={"index": 0, "cell": "PAD4", "orient": "mx90", "bondpad": "BONDPAD4"}),

    pad("jtag_tms", "input",
        mapping="right",
        layout_attributes={"index": 1, "cell": "PAD1", "orient": "mx90", "bondpad": "BONDPAD1"}),

    pad("jtag_tdo", "output",
        mapping="right",
        layout_attributes={"index": 2, "cell": "PAD2", "orient": "mx90", "bondpad": "BONDPAD2"}),

    rng("gpio", 14, "inout",
        offset=0,
        mapping="left",
        layout_attributes={"index": 3, "cell": "PAD3", "orient": "mx90", "bondpad": "BONDPAD3"}),

    pad("execute_from_flash", "input",
        mapping="bottom",
        layout_attributes={"index": 0, "cell": "PAD4", "orient": "mx", "bondpad": "BONDPAD4"}),

    pad("jtag_tck", "input",
        mapping="bottom",
        layout_attributes={"index": 1, "cell": "PAD1", "orient": "mx", "bondpad": "BONDPAD1"}),

    pad("jtag_trst", "input",
        active="low",
        mapping="bottom",
        layout_attributes={"index": 2, "cell": "PAD2", "orient": "mx", "bondpad": "BONDPAD2"}),

    pad("jtag_tdi", "input",
        mapping="top",
        layout_attributes={"index": 0, "cell": "PAD3", "orient": "r0", "bondpad": "BONDPAD3"}),

    pad("uart_rx", "input",
        mapping="top",
        layout_attributes={"index": 1, "cell": "PAD1", "orient": "r0", "bondpad": "BONDPAD1"}),

    pad("uart_tx", "output",
        mapping="top",
        layout_attributes={"index": 2, "cell": "PAD2", "orient": "r0", "bondpad": "BONDPAD2"}),

    pad("exit_valid", "output",
        mapping="top",
        layout_attributes={"index": 3, "cell": "PAD4", "orient": "r0", "bondpad": "BONDPAD4"}),

    mux("pdm2pcm_pdm", "inout",
        alts=[("pdm2pcm_pdm", "inout"), ("gpio_18", "inout")],
        mapping="top",
        layout_attributes={"index": 4, "cell": "PAD3", "orient": "r0", "bondpad": "BONDPAD3"}),
]

def config() -> Dict:
    """
    Return the full pad configuration dictionary.
    Example: config()
    """
    PAD_CFG = _mk_cfg(_ALL, _PHYS)
    return PAD_CFG