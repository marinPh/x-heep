from x_heep_gen.pads.PadDef import (
    SinglePad,
    MultiplexedPad,
    RangePad,
    PadGroup,
    Dimension,
    Layout,
)
from x_heep_gen.pads.PadRing import PadRing
from x_heep_gen.pads.Pad import PadMapping


def config() -> PadRing:
    # -------------------------------------------------------------------------
    # Floorplan / global physical attributes (from "physical_attributes")
    # -------------------------------------------------------------------------
    # "floorplan_dimensions": { "width": 2000, "length": 1500 }
    fp_dim = Dimension(width=2000, length=1500)

    # edge offsets and spacing
    bp_spacing = 25  # spacing.bondpad
    # there is no explicit pad/cell spacing in the JSON; keep None or set if known
    cell_spacing = None

    # -------------------------------------------------------------------------
    # Layouts & per-cell / per-bondpad dimensions (from "dimensions")
    # -------------------------------------------------------------------------
    # BONDPAD1: 50, PAD1: 40
    bondpad1_dim = Dimension(width=50, length=None)
    pad1_dim = Dimension(width=40, length=None)
    pad1_layout = Layout(name="PAD1", bond_pad=bondpad1_dim, cell_pad=pad1_dim)

    # BONDPAD2: 60, PAD2: 45
    bondpad2_dim = Dimension(width=60, length=None)
    pad2_dim = Dimension(width=45, length=None)
    pad2_layout = Layout(name="PAD2", bond_pad=bondpad2_dim, cell_pad=pad2_dim)

    # BONDPAD3: 70, PAD3: 50
    bondpad3_dim = Dimension(width=70, length=None)
    pad3_dim = Dimension(width=50, length=None)
    pad3_layout = Layout(name="PAD3", bond_pad=bondpad3_dim, cell_pad=pad3_dim)

    # BONDPAD4: 80, PAD4: 55
    bondpad4_dim = Dimension(width=80, length=None)
    pad4_dim = Dimension(width=55, length=None)
    pad4_layout = Layout(name="PAD4", bond_pad=bondpad4_dim, cell_pad=pad4_dim)

    offsets = Dimension(width=0, length=0)

    # -------------------------------------------------------------------------
    # PadGroup that will own all pads and physical attributes
    # -------------------------------------------------------------------------
    pad_group = PadGroup(
        name="x_heep_top",
        pad_edge_offset=90,
        bondpad_edge_offset=20,
        bp_spacing=bp_spacing,
        cell_spacing=cell_spacing,
        fp_dim=fp_dim,
    )

    # Helper for orientations (JSON uses "r90", "mx90", "mx", "r0", etc.)
    def orient(s: str) -> str:
        return s.upper()

    # -------------------------------------------------------------------------
    # Single pads (no mux)
    # -------------------------------------------------------------------------

    # "clk": mapping="right", cell=PAD1, orient="r90", bondpad=BONDPAD1
    clk = SinglePad(
        name="clk",
        layout_index=0,
        type="input",
        mapping=PadMapping.RIGHT,
        layout=pad1_layout,
        orient=orient("r90"),
    )
    pad_group.add_pad(clk)

    # "rst": active="low", driven_manually, mapping="right", cell=PAD2, orient="r90"
    rst = SinglePad(
        name="rst",
        layout_index=1,
        type="input",
        mapping=PadMapping.RIGHT,
        layout=pad2_layout,
        orient=orient("r90"),
        driven_manually=True,
        active="low",
    )
    pad_group.add_pad(rst)

    # "boot_select": mapping="right", cell=PAD4, orient="mx90"
    boot_select = SinglePad(
        name="boot_select",
        layout_index=3,
        type="input",
        mapping=PadMapping.RIGHT,
        layout=pad4_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(boot_select)

    # "jtag_tms": mapping="right", cell=PAD1, orient="mx90"
    jtag_tms = SinglePad(
        name="jtag_tms",
        layout_index=4,
        type="input",
        mapping=PadMapping.RIGHT,
        layout=pad1_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(jtag_tms)

    # "jtag_tdo": mapping="right", cell=PAD2, orient="mx90", type="output"
    jtag_tdo = SinglePad(
        name="jtag_tdo",
        layout_index=5,
        type="output",
        mapping=PadMapping.RIGHT,
        layout=pad2_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(jtag_tdo)

    # "execute_from_flash": mapping="bottom", cell=PAD4, orient="mx"
    execute_from_flash = SinglePad(
        name="execute_from_flash",
        layout_index=7,
        type="input",
        mapping=PadMapping.BOTTOM,
        layout=pad4_layout,
        orient=orient("mx"),
    )
    pad_group.add_pad(execute_from_flash)

    # "jtag_tck": mapping="bottom", cell=PAD1, orient="mx"
    jtag_tck = SinglePad(
        name="jtag_tck",
        layout_index=8,
        type="input",
        mapping=PadMapping.BOTTOM,
        layout=pad1_layout,
        orient=orient("mx"),
    )
    pad_group.add_pad(jtag_tck)

    # "jtag_trst": active="low", mapping="bottom", cell=PAD2, orient="mx"
    jtag_trst = SinglePad(
        name="jtag_trst",
        layout_index=9,
        type="input",
        mapping=PadMapping.BOTTOM,
        layout=pad2_layout,
        orient=orient("mx"),
        active="low",
    )
    pad_group.add_pad(jtag_trst)

    # "jtag_tdi": mapping="top", cell=PAD3, orient="r0"
    jtag_tdi = SinglePad(
        name="jtag_tdi",
        layout_index=10,
        type="input",
        mapping=PadMapping.TOP,
        layout=pad3_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(jtag_tdi)

    # "uart_rx": mapping="top", cell=PAD1, orient="r0"
    uart_rx = SinglePad(
        name="uart_rx",
        layout_index=11,
        type="input",
        mapping=PadMapping.TOP,
        layout=pad1_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(uart_rx)

    # "uart_tx": mapping="top", cell=PAD2, orient="r0", type="output"
    uart_tx = SinglePad(
        name="uart_tx",
        layout_index=12,
        type="output",
        mapping=PadMapping.TOP,
        layout=pad2_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(uart_tx)

    # "exit_valid": mapping="top", cell=PAD4, orient="r0", type="output"
    exit_valid = SinglePad(
        name="exit_valid",
        layout_index=13,
        type="output",
        mapping=PadMapping.TOP,
        layout=pad4_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(exit_valid)

    # -------------------------------------------------------------------------
    # Multiplexed pads
    # -------------------------------------------------------------------------

    # "pdm2pcm_clk": mapping="right", cell=PAD3, orient="r90",
    # mux: { "pdm2pcm_clk": "inout", "gpio_19": "inout" }
    alt_pdm2pcm_clk = SinglePad(
        name="pdm2pcm_clk",
        type="inout",
        mapping=PadMapping.RIGHT,
        layout=pad3_layout,
        orient=orient("r90"),
    )

    alt_gpio_19 = SinglePad(
        name="gpio_19",
        type="inout",
        mapping=PadMapping.RIGHT,
        layout=pad3_layout,
        orient=orient("r90"),
    )

    pdm2pcm_clk = MultiplexedPad(
        name="pdm2pcm_clk",
        layout_index=2,
        type="inout",
        mapping=PadMapping.RIGHT,
        layout=pad3_layout,
        orient=orient("r90"),
        alts=[("pdm2pcm_clk", alt_pdm2pcm_clk), ("gpio_19", alt_gpio_19)],
    )

    pad_group.add_pad(pdm2pcm_clk)

    # "pdm2pcm_pdm": mapping="top", cell=PAD3, orient="r0",
    # mux: { "pdm2pcm_pdm": "inout", "gpio_18": "inout" }
    alt_pdm2pcm = SinglePad(
        name="pdm2pcm_pdm",
        layout_index=14,
        type="inout",
        mapping=PadMapping.RIGHT,
        layout=pad3_layout,
        orient=orient("r0"),
    )

    # TODO: create a nicer way create alts this not ideal
    alt_gpio_18 = SinglePad(
        name="gpio_18",
        layout_index=14,
        type="inout",
        mapping=PadMapping.TOP,
        layout=pad3_layout,
        orient=orient("r0"),
    )

    pdm2pcm_pdm = MultiplexedPad(
        name="pdm2pcm_pdm",
        layout_index=14,
        type="inout",
        mapping=PadMapping.TOP,
        layout=pad3_layout,
        orient=orient("r0"),
        alts=[("pdm2pcm_pdm", alt_pdm2pcm), ("gpio_18", alt_gpio_18)],
    )

    pad_group.add_pad(pdm2pcm_pdm)

    # -------------------------------------------------------------------------
    # Range pad for "gpio" (num: 14, num_offset: 0 -> gpio_0 .. gpio_13)
    # -------------------------------------------------------------------------

    gpio_range = RangePad(
        name="gpio",
        layout_index=6,
        type="inout",
        mapping=PadMapping.LEFT,
        layout=pad3_layout,
        num=14,  # 14 pads -> 0..13
        orient=orient("mx90"),
    )
    pad_group.add_pad(gpio_range)
    # RangePad.add_pad() will expand to gpio_0 ... gpio_13 and assign indices

    # -------------------------------------------------------------------------
    # Wrap everything in a PadRing
    # -------------------------------------------------------------------------
    pad_ring = PadRing(pad_group)
    return pad_ring
