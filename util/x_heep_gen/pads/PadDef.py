# pad_cfg.py (OOP version)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple, Mapping, Any
from abc import ABC, abstractmethod

VALID_TYPES = {
    "input",
    "output",
    "inout",
    "bypass_input",
    "bypass_output",
    "bypass_inout",
}
VALID_MAPPING = {"top", "right", "bottom", "left"}

# -------------------------- Base model ---------------------------------------


class ValidationError(ValueError):
    pass


def _assert_type(t: str, where: str) -> None:
    if t not in VALID_TYPES:
        raise ValidationError(
            f"{where}: invalid type '{t}'. Valid: {sorted(VALID_TYPES)}"
        )


def _assert_mapping(m: str, where: str) -> None:
    if m not in VALID_MAPPING:
        raise ValidationError(
            f"{where}: invalid mapping '{m}'. Valid: {sorted(VALID_MAPPING)}"
        )


@dataclass(frozen=True)
class PadSpec(ABC):
    name: str
    type: str
    active: Optional[str] = None  # "low" | "high" | None
    driven_manually: bool = False
    mapping: Optional[str] = None  # "top|right|bottom|left"
    layout_attributes: Optional[Dict[str, Any]] = None

    def _validate_common(self) -> None:
        _assert_type(self.type, self.name)
        if self.active is not None and self.active not in ("low", "high"):
            raise ValidationError(f"{self.name}: active must be 'low' or 'high'")
        if self.mapping is not None:
            _assert_mapping(self.mapping, self.name)

    @abstractmethod
    def to_cfg(self) -> Tuple[str, Dict[str, Any]]: ...


@dataclass(frozen=True)
class SinglePad(PadSpec):
    """Non-range pad (always num=1)."""

    def to_cfg(self) -> Tuple[str, Dict[str, Any]]:
        self._validate_common()
        d: Dict[str, Any] = {"type": self.type, "num": 1}
        if self.active:
            d["active"] = self.active
        if self.driven_manually:
            d["driven_manually"] = True
        if self.mapping:
            d["mapping"] = self.mapping
        if self.layout_attributes:
            d["layout_attributes"] = self.layout_attributes
        return self.name, d


@dataclass(frozen=True)
class MuxPad(PadSpec):
    """Muxed non-range pad (always num=1)."""

    alts: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)  # (signal, type)

    def to_cfg(self) -> Tuple[str, Dict[str, Any]]:
        self._validate_common()
        entry: Dict[str, Any] = {"type": self.type, "num": 1, "mux": {}}
        if self.active:
            entry["active"] = self.active
        if self.driven_manually:
            entry["driven_manually"] = True
        if self.mapping:
            entry["mapping"] = self.mapping
        if self.layout_attributes:
            entry["layout_attributes"] = self.layout_attributes
        for sig, t in self.alts:
            _assert_type(t, f"{self.name}.mux[{sig}]")
            entry["mux"][sig] = {"type": t}
        return self.name, entry


@dataclass(frozen=True)
class RangePad(PadSpec):
    """Range pad (e.g., gpio_0..gpio_13)."""

    count: int = 1
    offset: int = 0

    def to_cfg(self) -> Tuple[str, Dict[str, Any]]:
        self._validate_common()
        if not isinstance(self.count, int) or self.count < 1:
            raise ValidationError(f"{self.name}: count must be integer >= 1")
        if not isinstance(self.offset, int):
            raise ValidationError(f"{self.name}: offset must be integer")
        d: Dict[str, Any] = {
            "type": self.type,
            "num": self.count,
            "num_offset": self.offset,
        }
        if self.mapping:
            d["mapping"] = self.mapping
        if self.layout_attributes:
            d["layout_attributes"] = self.layout_attributes
        return self.name, d


# -------------------------- Container / Builder ------------------------------


@dataclass
class PadConfig:
    physical_attributes: Optional[Dict[str, Any]] = None
    pads: List[PadSpec] = field(default_factory=list)

    def add(self, *pad_specs: PadSpec) -> "PadConfig":
        self.pads.extend(pad_specs)
        return self

    def build(self) -> Dict[str, Any]:
        pads_dict: Dict[str, Dict[str, Any]] = {}
        for spec in self.pads:
            key, val = spec.to_cfg()
            if key in pads_dict:
                raise ValidationError(f"Duplicate pad name '{key}'")
            # safety: enforce num presence (Single/Mux emit 1; Range emits count)
            if "num" not in val:
                val["num"] = 1
            # forbid range+mux together
            if "mux" in val and val.get("num", 1) != 1:
                raise ValidationError(
                    f"{key}: 'num' (range>1) and 'mux' cannot be combined"
                )
            pads_dict[key] = val

        cfg: Dict[str, Any] = {"pads": pads_dict}
        if self.physical_attributes:
            cfg["physical_attributes"] = self.physical_attributes
        return cfg
