"""
core/regex_rules.py

Rule engine that decides whether a crafted item's text counts as a
"success". Two building blocks:

- SingleRule: must match on its own. Combined with everything else via AND.
- GroupRule: holds several patterns; matching ANY ONE of them counts as
  the whole group matching (OR inside the group).

A RuleSet is a list of SingleRule/GroupRule nodes. It matches only when
EVERY node in it matches (AND across nodes, whether single or group) -
this mirrors "rule lẻ + group phải AND với nhau, group thì OR nội bộ".
"""

import re
from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class SingleRule:
    pattern: str
    case_sensitive: bool = False
    label: str = ""

    def is_match(self, text: str) -> bool:
        flags = re.MULTILINE if self.case_sensitive else (re.MULTILINE | re.IGNORECASE)
        return re.search(self.pattern, text, flags) is not None

    def to_dict(self) -> dict:
        return {
            "type": "single",
            "pattern": self.pattern,
            "case_sensitive": self.case_sensitive,
            "label": self.label,
        }


@dataclass
class GroupRule:
    patterns: List[SingleRule] = field(default_factory=list)
    label: str = ""

    def is_match(self, text: str) -> bool:
        if not self.patterns:
            return False
        return any(p.is_match(text) for p in self.patterns)

    def to_dict(self) -> dict:
        return {
            "type": "group",
            "label": self.label,
            "patterns": [p.to_dict() for p in self.patterns],
        }


RuleNode = Union[SingleRule, GroupRule]


def rule_node_from_dict(d: dict) -> RuleNode:
    if d["type"] == "single":
        return SingleRule(
            pattern=d["pattern"],
            case_sensitive=d.get("case_sensitive", False),
            label=d.get("label", ""),
        )
    if d["type"] == "group":
        return GroupRule(
            patterns=[
                SingleRule(
                    pattern=p["pattern"],
                    case_sensitive=p.get("case_sensitive", False),
                    label=p.get("label", ""),
                )
                for p in d["patterns"]
            ],
            label=d.get("label", ""),
        )
    raise ValueError(f"Unknown rule node type: {d['type']!r}")


@dataclass
class RuleSet:
    nodes: List[RuleNode] = field(default_factory=list)

    def is_match(self, text: str) -> bool:
        """Overall match = every node matches (AND). Empty rule set never
        auto-matches, so the loop just runs until max_attempts instead of
        silently 'succeeding' with nothing configured."""
        if not self.nodes:
            return False
        return all(node.is_match(text) for node in self.nodes)

    def add_single(self, pattern: str, case_sensitive: bool = False, label: str = "") -> SingleRule:
        rule = SingleRule(pattern=pattern, case_sensitive=case_sensitive, label=label)
        self.nodes.append(rule)
        return rule

    def add_group(self, patterns: List[str], label: str = "") -> GroupRule:
        group = GroupRule(patterns=[SingleRule(pattern=p) for p in patterns], label=label)
        self.nodes.append(group)
        return group

    def remove_at(self, index: int) -> None:
        if 0 <= index < len(self.nodes):
            del self.nodes[index]

    def to_dict(self) -> dict:
        return {"nodes": [n.to_dict() for n in self.nodes]}

    @staticmethod
    def from_dict(d: dict) -> "RuleSet":
        return RuleSet(nodes=[rule_node_from_dict(n) for n in d.get("nodes", [])])
