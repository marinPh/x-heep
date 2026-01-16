"""
PadRing Module (PadRing.py)

This module bridges configuration and generation by transforming PadGroup
(configuration-time) into physical Pad objects (generation-time).

Key responsibilities:
    - Assign physical positions and indices to pads
    - Apply layout rules (offsets, spacing, banks)
    - Generate Pad objects for template consumption
    - Validate global constraints

Main class:
    PadRing: Builder that consumes PadGroup and produces List[Pad]
"""

from nbformat import ValidationError
from .Pad import Pad, PadMapping
from .PadDef import PadDef, RangePad, MultiplexedPad, PadGroup, Layout
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


def as_bool(v, default: bool = False) -> bool:
    """
    Convert value to boolean with flexible string parsing.

    :param v: Value to convert
    :param bool default: Default value if conversion fails
    :return: Boolean value
    :rtype: bool
    """
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
    """
    Safely access nested dictionary value.

    :param d: Dictionary to traverse
    :param path: List of keys forming path
    :param default: Default value if path not found
    :return: Value at path or default
    """
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def coerce_enum(enum_cls, raw, default=None):
    """
    Flexibly convert raw value to enum instance.

    Tries both name matching (TOP/Right) and value matching ("top"/"right").

    :param enum_cls: Enum class to convert to
    :param raw: Raw value to convert
    :param default: Default if conversion fails
    :return: Enum instance or default
    """
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
    """
    Builder that transforms PadGroup into physical Pad objects.

    This is the bridge between configuration time (PadDef/PadGroup) and
    generation time (Pad objects). It:
        - Assigns physical indices to pads
        - Applies layout rules (offsets, spacing)
        - Generates template-ready Pad objects
        - Validates constraints

    Usage:
        pad_group = PadGroup(...)  # from config
        pad_ring = PadRing(pad_group)
        pad_ring.build()
        pads = pad_ring.pad_list  # use in templates

    Attributes (after build()):
        pad_list: List of all Pad objects
        total_pad: Total number of pads
        total_pad_muxed: Number of multiplexed pads
        top_pad_list, bottom_pad_list, left_pad_list, right_pad_list:
            Pads grouped by side
        bondpad_offsets: Physical offsets for each side
        physical_attributes: Physical properties dictionary
    """

    def __init__(self, pad_group: PadGroup):
        """
        Initialize PadRing with a PadGroup configuration.

        :param PadGroup pad_group: Configuration to build from
        """
        self.pad_group: PadGroup = pad_group

    def build(self):
        """
        Build Pad objects from PadGroup configuration.

        This supports two modes:
        1. Old model: Build from PadDef instances in pad_group
        2. New model: Use already-built Pad objects from generate_padlist()

        After calling build(), the pad_list and related attributes
        are populated and ready for template consumption.
        """
        pads_attributes_bits = self.pad_group.bits
        if not pads_attributes_bits:
            self.pads_attributes = None
            pads_attributes_bits = "-1:0"

        # Check if pads are already built (new pin-based model)
        # In the new model, pads are generated via generate_padlist() and added to pad_group
        from .pin import Pad as PinPad
        pads_from_pins = [p for p in self.pad_group.pads if isinstance(p, PinPad)]

        if pads_from_pins:
            # New pin-based model: pads are already built
            pad_objs = pads_from_pins
            external_pad_list = []
            pad_constant_driver_assign = ""
            pad_mux_process = ""
            bondpad_offsets = None

            # Separate by side
            pad_lists = separate_and_sort_pads(pad_objs, sort_by_layout_index=False)
            top_pad_list = pad_lists[PadMapping.TOP]
            bottom_pad_list = pad_lists[PadMapping.BOTTOM]
            left_pad_list = pad_lists[PadMapping.LEFT]
            right_pad_list = pad_lists[PadMapping.RIGHT]

            # Calculate statistics
            total_pad = len(pad_objs)
            pad_muxed_list = [p for p in pad_objs if p.is_muxed]
            total_pad_muxed = len(pad_muxed_list)

            # Max mux selector width
            max_total_pad_mux_bitlengh = 0
            if pad_muxed_list:
                max_total_pad_mux_bitlengh = max(
                    (len(p.alts) - 1).bit_length() for p in pad_muxed_list
                )

        else:
            # Old PadDef-based model
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

        # Store results (common to both models)
        self.pad_list = pad_objs
        self.total_pad_list = pad_objs
        self.pad_muxed_list = pad_muxed_list
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
    """
    Extract subset of Pad objects matching PadDef names.

    :param pad_list: List of PadDef to match
    :param all_pads: List of all Pad objects
    :return: Subset of Pad objects with matching names
    :rtype: List[Pad]
    """
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
    """
    Build list of Pad objects for mux alternatives in a multiplexed pad.

    :param MultiplexedPad block: Multiplexed pad with alternatives
    :param pad_mapping: Physical mapping for the pad
    :param bool pads_attributes_present: Whether attributes are present
    :param str pads_attributes_bits: Attribute bit range
    :param bool pad_constant_attribute: Whether attributes are constant
    :param Layout pad_layout: Optional layout information
    :return: List of Pad objects for each mux alternative
    :rtype: list
    """
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


def _get_effective_bp_spacing(pad: Optional[PadDef], default_spacing: float) -> float:
    """
    Resolve bondpad spacing using three-level hierarchy.

    Priority (highest to lowest):
        1. Per-pad: pad.layout.bp_spacing
        2. Per-side/Global: default_spacing (already resolved by caller)

    :param pad: Pad to get spacing from (None for first pad)
    :param float default_spacing: Default spacing (per-side or global)
    :return: Effective bondpad spacing
    :rtype: float
    """
    if pad is not None and pad.layout.bp_spacing is not None:
        return float(pad.layout.bp_spacing)
    return default_spacing


def _calculate_total_bondpad_space(
    pad_list: List[PadDef], default_spacing: float
) -> float:
    """
    Calculate total space occupied by bondpads including spacing.

    :param pad_list: List of pads on this side
    :param float default_spacing: Default bondpad spacing
    :return: Total space in micrometers
    :rtype: float
    """
    # Sum bondpad widths
    widths = np.array(
        [pad.layout.bond_pad.width for pad in pad_list if pad.layout is not None]
    )
    total_space = float(np.sum(widths))

    # Add spacing between bondpads (n-1 gaps for n pads)
    # Use pad[i+1].bp_spacing for the gap before pad i+1 (consistent with skip convention)
    for i in range(1, len(pad_list)):
        spacing = _get_effective_bp_spacing(pad_list[i], default_spacing)
        total_space += spacing

    return total_space


def _calculate_first_pad_offset(
    bp_offset: float,
    edge_to_pad: float,
    edge_to_bp: float,
    bp_width: float,
    pad_width: float,
) -> float:
    """
    Calculate offset for first pad to align with bondpad.

    :param float bp_offset: Bondpad offset from edge
    :param float edge_to_pad: Distance from edge to pad cells
    :param float edge_to_bp: Distance from edge to bondpads
    :param float bp_width: Bondpad width
    :param float pad_width: Pad cell width
    :return: Calculated offset
    :rtype: float
    """
    return bp_offset - (edge_to_pad - edge_to_bp) + (bp_width / 2) - (pad_width / 2)


def _calculate_pad_skip(
    last_bp_width: float,
    bp_width: float,
    bp_spacing: float,
    last_pad_width: float,
    pad_width: float,
) -> float:
    """
    Calculate skip between two pads based on bondpad and cell dimensions.

    :param float last_bp_width: Previous bondpad width
    :param float bp_width: Current bondpad width
    :param float bp_spacing: Spacing between bondpads
    :param float last_pad_width: Previous pad cell width
    :param float pad_width: Current pad cell width
    :return: Calculated skip value
    :rtype: float
    """
    return (
        (last_bp_width + bp_width) / 2 + bp_spacing - (last_pad_width + pad_width) / 2
    )


def set_pad_positions(pad_group: PadGroup, pad_list: List[PadDef]):
    """
    Calculate pad positions (offset and skip) such that bondpads are centered on each die side.

    This function:
        1. Validates physical attributes and configuration
        2. Calculates total space required for bondpads (including spacing)
        3. Centers bondpads on the die edge
        4. Aligns pad cells with their corresponding bondpads
        5. Calculates skip values for relative positioning

    Bondpad spacing hierarchy (highest to lowest priority):
        1. Per-pad: pad.layout.bp_spacing (spacing from this bondpad to next)
        2. Per-side: pad_group.get_bp_spacing(side)
        3. Global: pad_group.bp_spacing

    Positioning modes:
        - Auto mode: First pad gets offset, subsequent pads get skip (relative positioning)
        - Manual offset mode: Explicit offset provided (absolute positioning)
        - Mixed mode: Some pads with offset, some with skip

    :param PadGroup pad_group: Pad configuration with physical attributes
    :param List[PadDef] pad_list: List of pads to position on one die side
    :return: Bondpad offset from edge (for centering)
    :rtype: float
    :raises ValidationError: If physical attributes are missing or invalid
    :raises ValueError: If pads don't fit on the specified side
    """
    # Early return for empty list
    if not pad_list:
        return 0.0

    # -------------------------------------------------------------------------
    # 1. Validate and extract physical attributes
    # -------------------------------------------------------------------------
    try:
        fp = pad_group.fp_dim
        if fp is None:
            raise ValidationError("PadGroup.fp_dim is not set")

        fp_length = float(fp.length) if fp.length is not None else float(fp.width)
        fp_width = float(fp.width)
    except (AttributeError, TypeError, ValueError) as e:
        raise ValidationError(
            "Please set all mandatory physical_attributes in PadGroup"
        ) from e

    side = pad_list[0].mapping

    # Get per-side edge offsets
    try:
        edge_to_bp = pad_group.get_bondpad_edge_offset(side)
        edge_to_pad = pad_group.get_pad_edge_offset(side)
        default_bp_spacing = pad_group.get_bp_spacing(side)
    except ValidationError as e:
        raise ValidationError(
            f"Physical attributes not properly defined for side '{side}': {e}"
        ) from e

    # Determine side length
    if side in (PadMapping.TOP, PadMapping.BOTTOM):
        side_length = fp_width
    elif side in (PadMapping.LEFT, PadMapping.RIGHT):
        side_length = fp_length
    else:
        raise ValueError(f"Invalid pad mapping: {side}")

    # -------------------------------------------------------------------------
    # 2. Calculate total space and check fit
    # -------------------------------------------------------------------------
    total_bp_space = _calculate_total_bondpad_space(pad_list, default_bp_spacing)
    extra_space = side_length - total_bp_space - 2 * edge_to_bp

    if extra_space < 0:
        raise ValueError(
            f"Bondpads cannot fit on side {side}. "
            f"Required: {total_bp_space + 2 * edge_to_bp:.1f}μm, "
            f"Available: {side_length:.1f}μm. "
            f"Either reduce bondpad spacing or move some pads to another side."
        )

    # Bondpad offset from edge (for centering)
    bp_offset = extra_space / 2

    # -------------------------------------------------------------------------
    # 3. Calculate positions for each pad
    # -------------------------------------------------------------------------
    for i, pad in enumerate(pad_list):
        # Extract dimensions
        bp_width = pad.layout.bond_pad.width
        pad_width = _get_pad_cell_width(pad)

        # Get previous pad dimensions (for skip calculation)
        if i > 0:
            prev_pad = pad_list[i - 1]
            prev_bp_width = prev_pad.layout.bond_pad.width
            prev_pad_width = _get_pad_cell_width(prev_pad)
        else:
            prev_pad = None
            prev_bp_width = 0.0
            prev_pad_width = 0.0

        # Set first pad offset if not manually specified
        if i == 0 and pad.layout.offset is None:
            pad.layout.offset = _calculate_first_pad_offset(
                bp_offset, edge_to_pad, edge_to_bp, bp_width, pad_width
            )

        # Calculate skip if not manually specified
        # Note: Skip not calculated if offset is manual (absolute positioning mode)
        if pad.layout.skip is None and pad.layout.offset is None:
            bp_spacing = _get_effective_bp_spacing(pad, default_bp_spacing)
            pad.layout.skip = _calculate_pad_skip(
                prev_bp_width, bp_width, bp_spacing, prev_pad_width, pad_width
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
