"""Find new visible bubbles using a suffix/prefix overlap window."""
from __future__ import annotations


def new_bubble_keys(previous: list[str], current: list[str]) -> list[str]:
    for size in range(min(len(previous), len(current)), 0, -1):
        if previous[-size:] == current[:size]:
            return current[size:]
    return list(current)
