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
    fp_dim = Dimension(width=2000, height=1500, name="floorplan")

    # edge offsets and spacing
    edge_to_bp = 20    # edge_offset.bondpad
    edge_to_pad = 90   # edge_offset.pad
    bp_spacing = 25    # spacing.bondpad
    # there is no explicit pad/cell spacing in the JSON; keep None or set if known
    cell_spacing = None

    # -------------------------------------------------------------------------
    # Layouts & per-cell / per-bondpad dimensions (from "dimensions")
    # -------------------------------------------------------------------------
    # BONDPAD1: 50, PAD1: 40
    bondpad1_dim = Dimension(width=50, height=None, name="BONDPAD1")
    pad1_dim     = Dimension(width=40, height=None, name="PAD1")
    pad1_layout  = Layout(name="PAD1", bond_pad=bondpad1_dim, cell_pad=pad1_dim)

    # BONDPAD2: 60, PAD2: 45
    bondpad2_dim = Dimension(width=60, height=None, name="BONDPAD2")
    pad2_dim     = Dimension(width=45, height=None, name="PAD2")
    pad2_layout  = Layout(name="PAD2", bond_pad=bondpad2_dim, cell_pad=pad2_dim)

    # BONDPAD3: 70, PAD3: 50
    bondpad3_dim = Dimension(width=70, height=None, name="BONDPAD3")
    pad3_dim     = Dimension(width=50, height=None, name="PAD3")
    pad3_layout  = Layout(name="PAD3", bond_pad=bondpad3_dim, cell_pad=pad3_dim)

    # BONDPAD4: 80, PAD4: 55
    bondpad4_dim = Dimension(width=80, height=None, name="BONDPAD4")
    pad4_dim     = Dimension(width=55, height=None, name="PAD4")
    pad4_layout  = Layout(name="PAD4", bond_pad=bondpad4_dim, cell_pad=pad4_dim)

    # -------------------------------------------------------------------------
    # PadGroup that will own all pads and physical attributes
    # -------------------------------------------------------------------------
    pad_group = PadGroup(
        name="x_heep_top",
        edge_to_bp=edge_to_bp,
        edge_to_pad=edge_to_pad,
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
        type="input",
        mapping=PadMapping("right"),
        layout=pad1_layout,
        orient=orient("r90"),
    )
    pad_group.add_pad(clk)

    # "rst": active="low", driven_manually, mapping="right", cell=PAD2, orient="r90"
    rst = SinglePad(
        name="rst",
        type="input",
        mapping=PadMapping("right"),
        layout=pad2_layout,
        orient=orient("r90"),
        driven_manually=True,
        properties={"active": "low"},
    )
    pad_group.add_pad(rst)

    # "boot_select": mapping="right", cell=PAD4, orient="mx90"
    boot_select = SinglePad(
        name="boot_select",
        type="input",
        mapping=PadMapping("right"),
        layout=pad4_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(boot_select)

    # "jtag_tms": mapping="right", cell=PAD1, orient="mx90"
    jtag_tms = SinglePad(
        name="jtag_tms",
        type="input",
        mapping=PadMapping("right"),
        layout=pad1_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(jtag_tms)

    # "jtag_tdo": mapping="right", cell=PAD2, orient="mx90", type="output"
    jtag_tdo = SinglePad(
        name="jtag_tdo",
        type="output",
        mapping=PadMapping("right"),
        layout=pad2_layout,
        orient=orient("mx90"),
    )
    pad_group.add_pad(jtag_tdo)

    # "execute_from_flash": mapping="bottom", cell=PAD4, orient="mx"
    execute_from_flash = SinglePad(
        name="execute_from_flash",
        type="input",
        mapping=PadMapping("bottom"),
        layout=pad4_layout,
        orient=orient("mx"),
    )
    pad_group.add_pad(execute_from_flash)

    # "jtag_tck": mapping="bottom", cell=PAD1, orient="mx"
    jtag_tck = SinglePad(
        name="jtag_tck",
        type="input",
        mapping=PadMapping("bottom"),
        layout=pad1_layout,
        orient=orient("mx"),
    )
    pad_group.add_pad(jtag_tck)

    # "jtag_trst": active="low", mapping="bottom", cell=PAD2, orient="mx"
    jtag_trst = SinglePad(
        name="jtag_trst",
        type="input",
        mapping=PadMapping("bottom"),
        layout=pad2_layout,
        orient=orient("mx"),
        properties={"active": "low"},
    )
    pad_group.add_pad(jtag_trst)

    # "jtag_tdi": mapping="top", cell=PAD3, orient="r0"
    jtag_tdi = SinglePad(
        name="jtag_tdi",
        type="input",
        mapping=PadMapping("top"),
        layout=pad3_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(jtag_tdi)

    # "uart_rx": mapping="top", cell=PAD1, orient="r0"
    uart_rx = SinglePad(
        name="uart_rx",
        type="input",
        mapping=PadMapping("top"),
        layout=pad1_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(uart_rx)

    # "uart_tx": mapping="top", cell=PAD2, orient="r0", type="output"
    uart_tx = SinglePad(
        name="uart_tx",
        type="output",
        mapping=PadMapping("top"),
        layout=pad2_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(uart_tx)

    # "exit_valid": mapping="top", cell=PAD4, orient="r0", type="output"
    exit_valid = SinglePad(
        name="exit_valid",
        type="output",
        mapping=PadMapping("top"),
        layout=pad4_layout,
        orient=orient("r0"),
    )
    pad_group.add_pad(exit_valid)

    # -------------------------------------------------------------------------
    # Multiplexed pads
    # -------------------------------------------------------------------------

    # "pdm2pcm_clk": mapping="right", cell=PAD3, orient="r90",
    # mux: { "pdm2pcm_clk": "inout", "gpio_19": "inout" }
    pdm2pcm_clk = MultiplexedPad(
        name="pdm2pcm_clk",
        type="inout",
        mapping=PadMapping("right"),
        layout=pad3_layout,
        orient=orient("r90"),
    )
    # store the mux alts in properties or a dedicated field, depending on how you extend MultiplexedPad
    pdm2pcm_clk.properties["alts"] = [
        ("pdm2pcm_clk", "inout"),
        ("gpio_19", "inout"),
    ]
    pad_group.add_pad(pdm2pcm_clk)

    # "pdm2pcm_pdm": mapping="top", cell=PAD3, orient="r0",
    # mux: { "pdm2pcm_pdm": "inout", "gpio_18": "inout" }
    pdm2pcm_pdm = MultiplexedPad(
        name="pdm2pcm_pdm",
        type="inout",
        mapping=PadMapping("top"),
        layout=pad3_layout,
        orient=orient("r0"),
    )
    pdm2pcm_pdm.properties["alts"] = [
        ("pdm2pcm_pdm", "inout"),
        ("gpio_18", "inout"),
    ]
    pad_group.add_pad(pdm2pcm_pdm)

    # -------------------------------------------------------------------------
    # Range pad for "gpio" (num: 14, num_offset: 0 -> gpio_0 .. gpio_13)
    # -------------------------------------------------------------------------
    gpio_range = RangePad(
        name="gpio",
        type="inout",
        mapping=PadMapping("left"),
        layout=pad3_layout,
        start_index=0,
        end_index=13,   # 14 pads -> 0..13
        step=1,
    )
    pad_group.add_pad(gpio_range)
    # RangePad.add_pad() will expand to gpio_0 ... gpio_13 and assign indices

    # -------------------------------------------------------------------------
    # Wrap everything in a PadRing
    # -------------------------------------------------------------------------
    pad_ring = PadRing(pad_group)
    return pad_ring
