from x_heep_gen.xheep.pads.PadDef import PadSpec, SinglePad, MuxPad, RangePad, PadConfig
from x_heep_gen.xheep.pads.PadRing import PadRing

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

PAD_CFG = (
    PadConfig(physical_attributes=_PHYS)
    .add(
        SinglePad(
            "clk",
            "input",
            mapping="right",
            layout_attributes={
                "index": 0,
                "cell": "PAD1",
                "orient": "r90",
                "bondpad": "BONDPAD1",
            },
        ),
        SinglePad(
            "rst",
            "input",
            active="low",
            driven_manually=True,
            mapping="right",
            layout_attributes={
                "index": 1,
                "cell": "PAD2",
                "orient": "r90",
                "bondpad": "BONDPAD2",
            },
        ),
        MuxPad(
            "pdm2pcm_clk",
            "inout",
            mapping="right",
            layout_attributes={
                "index": 2,
                "cell": "PAD3",
                "orient": "r90",
                "bondpad": "BONDPAD3",
            },
            alts=(("pdm2pcm_clk", "inout"), ("gpio_19", "inout")),
        ),
        SinglePad(
            "boot_select",
            "input",
            mapping="right",
            layout_attributes={
                "index": 0,
                "cell": "PAD4",
                "orient": "mx90",
                "bondpad": "BONDPAD4",
            },
        ),
        SinglePad(
            "jtag_tms",
            "input",
            mapping="right",
            layout_attributes={
                "index": 1,
                "cell": "PAD1",
                "orient": "mx90",
                "bondpad": "BONDPAD1",
            },
        ),
        SinglePad(
            "jtag_tdo",
            "output",
            mapping="right",
            layout_attributes={
                "index": 2,
                "cell": "PAD2",
                "orient": "mx90",
                "bondpad": "BONDPAD2",
            },
        ),
        RangePad(
            "gpio",
            "inout",
            count=14,
            offset=0,
            mapping="left",
            layout_attributes={
                "index": 3,
                "cell": "PAD3",
                "orient": "mx90",
                "bondpad": "BONDPAD3",
            },
        ),
        SinglePad(
            "execute_from_flash",
            "input",
            mapping="bottom",
            layout_attributes={
                "index": 0,
                "cell": "PAD4",
                "orient": "mx",
                "bondpad": "BONDPAD4",
            },
        ),
        SinglePad(
            "jtag_tck",
            "input",
            mapping="bottom",
            layout_attributes={
                "index": 1,
                "cell": "PAD1",
                "orient": "mx",
                "bondpad": "BONDPAD1",
            },
        ),
        SinglePad(
            "jtag_trst",
            "input",
            active="low",
            mapping="bottom",
            layout_attributes={
                "index": 2,
                "cell": "PAD2",
                "orient": "mx",
                "bondpad": "BONDPAD2",
            },
        ),
        SinglePad(
            "jtag_tdi",
            "input",
            mapping="top",
            layout_attributes={
                "index": 0,
                "cell": "PAD3",
                "orient": "r0",
                "bondpad": "BONDPAD3",
            },
        ),
        SinglePad(
            "uart_rx",
            "input",
            mapping="top",
            layout_attributes={
                "index": 1,
                "cell": "PAD1",
                "orient": "r0",
                "bondpad": "BONDPAD1",
            },
        ),
        SinglePad(
            "uart_tx",
            "output",
            mapping="top",
            layout_attributes={
                "index": 2,
                "cell": "PAD2",
                "orient": "r0",
                "bondpad": "BONDPAD2",
            },
        ),
        SinglePad(
            "exit_valid",
            "output",
            mapping="top",
            layout_attributes={
                "index": 3,
                "cell": "PAD4",
                "orient": "r0",
                "bondpad": "BONDPAD4",
            },
        ),
        MuxPad(
            "pdm2pcm_pdm",
            "inout",
            mapping="top",
            layout_attributes={
                "index": 4,
                "cell": "PAD3",
                "orient": "r0",
                "bondpad": "BONDPAD3",
            },
            alts=(("pdm2pcm_pdm", "inout"), ("gpio_18", "inout")),
        ),
    )
    .build()
)


def config() -> PadRing:
    pad_ring = PadRing(PAD_CFG)
    return pad_ring
