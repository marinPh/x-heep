from nbformat import ValidationError
from .Pad import Pad, PadMapping
from .PadDef import PadDef, RangePad, MultiplexedPad, PadGroup, Layout
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


def as_bool(v, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return default


def get_nested(d, path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def coerce_enum(enum_cls, raw, default=None):
    if raw is None:
        return default
    if isinstance(raw, enum_cls):
        return raw
    try:
        if isinstance(raw, str):
            s = raw.strip(",").strip()
            # Try name match (TOP/Right/etc.) then value match ("top"/"right"/…)
            try:
                return enum_cls[s.upper()]
            except KeyError:
                return enum_cls(s.lower())
        return enum_cls(raw)
    except Exception:
        return default  # or raise if you prefer strictness


class PadRing:
    def __init__(self, pad_group: PadGroup):
        self.pad_group: PadGroup = pad_group

    def build(self):
        pads_attributes_bits = self.pad_group.bits

        if not pads_attributes_bits:
            self.pads_attributes = None
            pads_attributes_bits = "-1:0"

        # Read HJSON description of External Pads

        pad_objs: List[Pad] = []
        external_pad_list = []

        pad_constant_driver_assign = ""
        pad_mux_process = ""
        bondpad_offsets = None
        if self.pad_group.fp_dim is not None:
            bondpad_offsets = prepare_pads_for_layout(self.pad_group)

        pad_muxed_list = self.pad_group.get_multiplexed_pads()
        (
            pad_objs,
            muxed,
            pad_constant_driver_assign,
            pad_mux_process,
        ) = build_pads_from_block(
            pad_group=self.pad_group,
            pads_attributes_present=(self.pad_group.bits is not None),
            pads_attributes_bits=pads_attributes_bits,
            default_constant_attribute=False,
            always_emit_ring=False,  # respect keep_internal for internal pads
        )

        # external pads (continue indexing, always emit ring)
        # merge, totals
        total_pad = len(pad_objs)
        total_pad_muxed = len(pad_muxed_list)

        # max mux selector width (0 if none)
        max_total_pad_mux_bitlengh = 0
        if pad_muxed_list:
            max_total_pad_mux_bitlengh = max(
                (len(p.alts) - 1).bit_length() for p in pad_muxed_list
            )

        # remove trailing comma from last PAD io_interface (kept to preserve behavior)
        if pad_objs:
            last_pad = pad_objs.pop()
            last_pad.remove_comma_io_interface()
            pad_objs.append(last_pad)

        # Separate pads by mapping (top, bottom, left, right)
        pad_lists = separate_and_sort_pads(pad_objs, sort_by_layout_index=False)
        top_pad_list = pad_lists[PadMapping.TOP]
        bottom_pad_list = pad_lists[PadMapping.BOTTOM]
        left_pad_list = pad_lists[PadMapping.LEFT]
        right_pad_list = pad_lists[PadMapping.RIGHT]
        bondpad_offsets = bondpad_offsets

        self.pad_list = pad_objs
        self.total_pad_list = pad_objs
        self.pad_muxed_list = muxed
        self.total_pad = total_pad
        self.total_pad_muxed = total_pad_muxed
        self.max_total_pad_mux_bitlengh = max_total_pad_mux_bitlengh
        self.top_pad_list = top_pad_list
        self.bottom_pad_list = bottom_pad_list
        self.left_pad_list = left_pad_list
        self.right_pad_list = right_pad_list
        self.bondpad_offsets = bondpad_offsets
        self.physical_attributes = self.pad_group.get_physical_attributes()
        self.external_pad_list = external_pad_list
        self.pad_constant_driver_assign = pad_constant_driver_assign
        self.pad_mux_process = pad_mux_process
        self.pads_attributes = self.pad_group.pad_attribute


def pad_subset(pad_list: List[PadDef], all_pads: List[Pad]) -> List[Pad]:

    subset = []
    pad_dict = {pad.name: pad for pad in all_pads}
    for pad_def in pad_list:
        if pad_def.name in pad_dict:
            subset.append(pad_dict[pad_def.name])
    return subset


def _get_pad_cell_width(pad, pad_name=None):
    """
    Extract pad cell width with proper error handling.

    :param pad: Pad object with layout attribute
    :param str pad_name: Optional pad name for error messages (defaults to pad.name)
    :return: Pad cell width as float
    :rtype: float
    :raises ValueError: If pad cell is not defined or width is missing
    """
    if pad_name is None:
        pad_name = getattr(pad, "name", "unknown")

    # Get pad cell from layout
    pad_cell = getattr(pad.layout, "cell_pad", None) if hasattr(pad, "layout") else None

    if pad_cell is None:
        raise ValueError(f"Pad cell not defined for pad '{pad_name}'")

    # Extract width with error handling
    try:
        return float(pad_cell.width)
    except (AttributeError, KeyError) as e:
        raise ValueError(f"Width not defined for pad cell of pad '{pad_name}'") from e


def separate_and_sort_pads(pads, sort_by_layout_index=False):
    """
    Separate pads by their mapping (top, bottom, left, right) and optionally sort by layout index.

    :param pads: List of pad objects (Pad or PadDef)
    :param bool sort_by_layout_index: Whether to sort pads by their layout_index attribute
    :return: Dictionary with PadMapping keys and lists of pads as values
    :rtype: dict
    """
    pad_lists = {
        PadMapping.TOP: [],
        PadMapping.BOTTOM: [],
        PadMapping.RIGHT: [],
        PadMapping.LEFT: [],
    }

    for pad in pads:
        # Handle both 'mapping' and 'pad_mapping' attributes
        pad_mapping = getattr(pad, "mapping", getattr(pad, "pad_mapping", None))

        if pad_mapping in pad_lists:
            pad_lists[pad_mapping].append(pad)

    # Sort pads by layout index if requested
    if sort_by_layout_index:
        for mapping in pad_lists:
            pad_lists[mapping].sort(key=lambda x: x.layout_index)

    return pad_lists


def prepare_pads_for_layout(pad_group: PadGroup):
    """
    Separate pads into pad lists for the top, bottom, left, and right pads and order them according to their layout_index attribute, and set their positions on the floorplan.
    """

    # Separate pads according to side and order by layout index
    pad_lists = separate_and_sort_pads(pad_group.get_pads(), sort_by_layout_index=True)
    top_pad_list = pad_lists[PadMapping.TOP]
    bottom_pad_list = pad_lists[PadMapping.BOTTOM]
    left_pad_list = pad_lists[PadMapping.LEFT]
    right_pad_list = pad_lists[PadMapping.RIGHT]

    # Calculate pad offsets and check wheth
    ## Conver lists of PadDef to lists of Pad objects

    bondpad_offset_top = set_pad_positions(pad_group, top_pad_list)
    bondpad_offset_bottom = set_pad_positions(pad_group, bottom_pad_list)
    bondpad_offset_left = set_pad_positions(pad_group, left_pad_list)
    bondpad_offset_right = set_pad_positions(pad_group, right_pad_list)

    bondpad_offsets = {
        "top": bondpad_offset_top,
        "bottom": bondpad_offset_bottom,
        "left": bondpad_offset_left,
        "right": bondpad_offset_right,
    }

    return bondpad_offsets


def build_mux_list(
    block: MultiplexedPad,
    pad_mapping,
    pads_attributes_present: bool,
    pads_attributes_bits: str,
    pad_constant_attribute: bool,
    pad_layout: Layout = None,
):

    mux_list = []
    if pad_layout is not None:
        pad_layout.skip = None
        pad_layout.offset = None

    for mux_name, entry in block.alts:
        mux = Pad(
            mux_name,
            "",
            entry.type,
            pad_mapping,
            0,
            block.layout_index,
            entry.active,
            as_bool(entry.driven_manually, False),
            as_bool(entry.skip, False),
            [],
            pads_attributes_present,
            pads_attributes_bits,
            pad_constant_attribute,
            pad_layout,
            orient=entry.orient,
        )
        mux_list.append(mux)
    return mux_list


def set_pad_positions(pad_group: PadGroup, pad_list: List[PadDef]):
    """Calculate the `offset` and `skip` attributes of the pads such that the bondpads are centered on each side and the pads are aligned with their respective bondpads.
    Perform checks to make sure the pads can all fit on the requested side without violating design constraints or exceeding layout margins.
    """
    # FIXME: what do we give if no pad on this side
    if len(pad_list) == 0:
        return 0.0

    # Ensure the physical attributes were properly set in the pad config file
    try:
        fp = pad_group.fp_dim
        if fp is None:
            raise ValidationError("PadGroup.fp_dim is not set")

        fp_length = float(fp.length) if fp.length is not None else float(fp.width)
        fp_width = float(fp.width)
        edge_to_bp = float(pad_group.bondpad_edge_offset)
        edge_to_pad = float(pad_group.pad_edge_offset)
        bp_spacing = float(pad_group.bp_spacing)
    except (AttributeError, TypeError, ValueError) as e:
        raise ValidationError(
            "Please set all mandatory physical_attributes in PadGroup"
        ) from e

    # Determine which dimension we are dealing with
    side = pad_list[0].mapping

    if side in (PadMapping.TOP, PadMapping.BOTTOM):
        side_length = fp_width
    elif side in (PadMapping.LEFT, PadMapping.RIGHT):
        side_length = fp_length
    else:
        print("ERROR: Invalid pad mapping {0}".format(side))
        raise ValueError("Invalid pad mapping")

    # Calculate space occupied by bondpads on the designated side of the chip
    # Simple correction to consider only pads that have bondpads defined
    widths = np.array([pad.layout.bond_pad.width for pad in pad_list if pad.layout.bond_pad])
    bp_space = float(np.sum(widths))
    bp_space += bp_spacing * (len(pad_list) - 1)
    # Check if the bondpads are able to fit on the side
    extra_space = side_length - bp_space - 2 * edge_to_bp

    if extra_space < 0:
        print(
            "ERROR: Bondpads cannot fit on side {0}. Either reduce bondpad spacing or move some pads to another side".format(
                side
            )
        )
        raise ValueError("Bondpads cannot fit on side {0}".format(side))

    # Calculate distance from edge to first bondpad (i.e. bondpad offset) to center the pads
    bp_offset = extra_space / 2

    # Calculate skip parameter between one pad and the next to center the pads
    for i, pad in enumerate(pad_list):

        # Get bondpad width from physical attributes
        bp_cell = pad.layout.bond_pad
        bp_width = bp_cell.width

        if i > 0:
            last_bp_cell = pad_list[i - 1].layout
            last_bp_width = last_bp_cell.bond_pad.width

        # Get pad cell width using helper function
        pad_width = _get_pad_cell_width(pad)

        # Get previous pad width if not first pad
        if i > 0:
            last_pad_width = _get_pad_cell_width(pad_list[i - 1])
        if (i == 0) and (pad.layout.offset is None):
            # First pad: set offset to align with bondpad
            pad.layout.offset = (
                bp_offset
                - (edge_to_pad - edge_to_bp)
                + (bp_width / 2)
                - (pad_width / 2)
            )

        # If the layout/skip of the pads is not predefined, calculate automatically
        if (pad.layout.skip is None) and (pad.layout.offset is None):
            pad.layout.skip = (
                (last_bp_width + bp_width) / 2
                + bp_spacing
                - (last_pad_width + pad_width) / 2
            )
    return bp_offset


def build_pads_from_block(
    pad_group: PadGroup,
    pads_attributes_present: bool,
    pads_attributes_bits: str,
    default_constant_attribute: bool,
    always_emit_ring: bool,
) -> Tuple[List[Pad], List[Pad], str, str]:
    pad_list: List[Pad] = []
    pad_muxed_list: List[Pad] = []
    const_assign_parts = []
    mux_process_parts = []

    for i, block in enumerate(pad_group.get_pads()):

        pad_type = block.type

        pad_active = block.active
        pad_mapping = coerce_enum(PadMapping, block.mapping, None)

        pad_driven_manually = as_bool(block.driven_manually, False)
        pad_skip_declaration = as_bool(block.skip, False)
        pad_keep_internal = as_bool(block.keep_internal, False)
        pad_constant_attribute: bool = (
            default_constant_attribute
            if not block.constant_attribute
            else block.constant_attribute
        )

        # layout (optional)
        pad_layout = block.layout

        # mux list
        pad_mux_list = []

        if isinstance(block, MultiplexedPad):
            pad_mux_list = build_mux_list(
                block,
                pad_mapping,
                pads_attributes_present,
                pads_attributes_bits,
                pad_constant_attribute,
                pad_layout.copy() if pad_layout is not None else None,
            )
        pad_obj = Pad(
            block.name,
            f"pad_{block.name}_i",
            pad_type,
            pad_mapping,
            i,
            block.layout_index,
            pad_active,
            pad_driven_manually,
            pad_skip_declaration,
            pad_mux_list,
            pads_attributes_present,
            pads_attributes_bits,
            pad_constant_attribute,
            pad_layout,
            block.orient,
        )

        # build sections (internal can skip ring; external always emits ring)
        emit_ring = always_emit_ring or not pad_keep_internal
        if emit_ring:
            pad_obj.create_pad_ring()
        pad_obj.create_core_v_mini_mcu_ctrl()
        if emit_ring:
            pad_obj.create_pad_ring_bonding()
        pad_obj.create_internal_signals()
        pad_obj.create_constant_driver_assign()
        pad_obj.create_multiplexers()
        pad_obj.create_core_v_mini_mcu_bonding()

        pad_list.append(pad_obj)
        const_assign_parts.append(pad_obj.constant_driver_assign)
        mux_process_parts.append(pad_obj.mux_process)
        if pad_obj.is_muxed:
            pad_muxed_list.append(pad_obj)

    return (
        pad_list,
        pad_muxed_list,
        "".join(const_assign_parts),
        "".join(mux_process_parts),
    )
