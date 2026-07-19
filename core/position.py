"""
core/position.py

Simple screen-coordinate model shared by every feature. Kept dead simple
on purpose: features build richer concepts (CraftStep, CraftTarget, ...)
on top of this rather than each rolling their own (x, y) representation.
"""

from dataclasses import dataclass, asdict


@dataclass
class Position:
    x: int
    y: int
    label: str = ""

    def as_tuple(self) -> tuple:
        return (self.x, self.y)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Position":
        return Position(x=d["x"], y=d["y"], label=d.get("label", ""))
