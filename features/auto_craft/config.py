"""
features/auto_craft/config.py

Data model for one auto-craft setup - kept separate from engine/ui so
it's easy to serialize (JSON profiles) and reason about on its own.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from core.position import Position
from core.regex_rules import RuleSet


@dataclass
class CraftStep:
    """One entry in the spam loop: the currency to right-click for this step."""

    currency_pos: Optional[Position] = None
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "pos": self.currency_pos.to_dict() if self.currency_pos else None,
            "label": self.label,
        }

    @staticmethod
    def from_dict(d: dict) -> "CraftStep":
        return CraftStep(
            currency_pos=Position.from_dict(d["pos"]) if d.get("pos") else None,
            label=d.get("label", ""),
        )


@dataclass
class CraftTarget:
    """The item/map being crafted. Modeled as its own small object (not a
    bare x, y) so a future 'multiple targets' feature only has to grow
    CraftConfig.targets from holding 1 item to holding N - code that
    already loops over `targets` won't need to change."""

    pos: Optional[Position] = None
    label: str = ""

    def to_dict(self) -> dict:
        return {"pos": self.pos.to_dict() if self.pos else None, "label": self.label}

    @staticmethod
    def from_dict(d: dict) -> "CraftTarget":
        return CraftTarget(
            pos=Position.from_dict(d["pos"]) if d.get("pos") else None,
            label=d.get("label", ""),
        )


@dataclass
class CraftConfig:
    steps: List[CraftStep] = field(default_factory=list)
    targets: List[CraftTarget] = field(default_factory=list)  # UI today only fills in 1
    rules: RuleSet = field(default_factory=RuleSet)
    max_attempts: int = 100

    @property
    def target(self) -> CraftTarget:
        """Convenience accessor while the UI only supports a single target."""
        return self.targets[0]

    def to_dict(self) -> dict:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "targets": [t.to_dict() for t in self.targets],
            "rules": self.rules.to_dict(),
            "max_attempts": self.max_attempts,
        }

    @staticmethod
    def from_dict(d: dict) -> "CraftConfig":
        return CraftConfig(
            steps=[CraftStep.from_dict(s) for s in d.get("steps", [])],
            targets=[CraftTarget.from_dict(t) for t in d.get("targets", [])],
            rules=RuleSet.from_dict(d.get("rules", {})),
            max_attempts=d.get("max_attempts", 100),
        )
