# pad_cfg.py
# Python form of your HJSON, with a tiny DSL and validation.
from typing import Dict, Tuple, Iterable, Optional

# ---- DSL + validation -------------------------------------------------------

VALID_TYPES = {
    "input", "output", "inout",
    "bypass_input", "bypass_output", "bypass_inout",
}
VALID_MAPPING = {"top", "right", "bottom", "left"}

PadsDict = Dict[str, Dict]

def pad(name: str,
        type: str,
        *,
        active: Optional[str] = None,
        driven_manually: bool = False,
        mapping: Optional[str] = None,
        layout_attributes: Optional[Dict] = None) -> Tuple[str, Dict]:
    """Single (non-range) pad -> always num: 1."""
    _assert_type(type, f"{name}")
    if mapping: _assert_mapping(mapping, name)
    d: Dict = {"type": type, "num": 1}
    if active: d["active"] = active
    if driven_manually: d["driven_manually"] = True
    if mapping: d["mapping"] = mapping
    if layout_attributes: d["layout_attributes"] = layout_attributes
    return name, d

def rng(base: str,
        count: int,
        type: str,
        *,
        offset: int = 0,
        mapping: Optional[str] = None,
        layout_attributes: Optional[Dict] = None) -> Tuple[str, Dict]:
    """Range pad (e.g., gpio_0..gpio_13)."""
    _assert_type(type, f"{base}[range]")
    if mapping: _assert_mapping(mapping, base)
    d: Dict = {"type": type, "num": count, "num_offset": offset}
    if mapping: d["mapping"] = mapping
    if layout_attributes: d["layout_attributes"] = layout_attributes
    return base, d

def mux(name: str,
        type: str,
        alts: Iterable[Tuple[str, str]],
        *,
        active: Optional[str] = None,
        driven_manually: bool = False,
        mapping: Optional[str] = None,
        layout_attributes: Optional[Dict] = None) -> Tuple[str, Dict]:
    """Muxed single pad -> num: 1."""
    _assert_type(type, f"{name}")
    if mapping: _assert_mapping(mapping, name)
    entry: Dict = {"type": type, "num": 1, "mux": {}}
    if active: entry["active"] = active
    if driven_manually: entry["driven_manually"] = True
    if mapping: entry["mapping"] = mapping
    if layout_attributes: entry["layout_attributes"] = layout_attributes
    for sig, t in alts:
        _assert_type(t, f"{name}.mux[{sig}]")
        entry["mux"][sig] = {"type": t}
    return name, entry

def _assert_type(t: str, where: str) -> None:
    if t not in VALID_TYPES:
        raise ValueError(f"{where}: invalid type '{t}'. Valid: {sorted(VALID_TYPES)}")

def _assert_mapping(m: str, where: str) -> None:
    if m not in VALID_MAPPING:
        raise ValueError(f"{where}: invalid mapping '{m}'. Valid: {sorted(VALID_MAPPING)}")

def _mk_cfg(items: Iterable[Tuple[str, Dict]], physical_attributes: Optional[Dict] = None) -> Dict:
    pads: PadsDict = {}
    for k, v in items:
        if k in pads:
            raise ValueError(f"Duplicate pad name '{k}'")
        if "num" not in v:
            v["num"] = 1  # safety
        pads[k] = v
    cfg = {"pads": pads}
    if physical_attributes:
        cfg["physical_attributes"] = physical_attributes
    _validate(cfg)
    return cfg

def _validate(cfg: Dict) -> None:
    pads: PadsDict = cfg.get("pads", {})
    for name, desc in pads.items():
        t = desc.get("type")
        _assert_type(t, name)

        # num must exist and be >=1
        if "num" not in desc or not isinstance(desc["num"], int) or desc["num"] < 1:
            raise ValueError(f"{name}: 'num' must be an integer >= 1")

        if "num_offset" in desc and not isinstance(desc["num_offset"], int):
            raise ValueError(f"{name}: 'num_offset' must be an integer")

        # ranges with mux not supported (only single entries may mux)
        if "mux" in desc and desc.get("num", 1) != 1:
            raise ValueError(f"{name}: 'num' (range>1) and 'mux' cannot be combined.")

        if "active" in desc and desc["active"] not in ("low", "high"):
            raise ValueError(f"{name}: active must be 'low' or 'high'")

        if "mapping" in desc:
            _assert_mapping(desc["mapping"], name)

        if "mux" in desc:
            for alt_sig, alt_desc in desc["mux"].items():
                _assert_type(alt_desc.get("type", ""), f"{name}.mux[{alt_sig}]")

# ---- Physical attributes (copied from HJSON) --------------------------------
