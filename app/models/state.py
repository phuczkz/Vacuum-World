"""
Module chứa các class State và SearchResult
"""

from enum import Enum
from typing import Set, Tuple, List


class Action(Enum):
    """Các hành động của robot"""
    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"
    SUCK = "Suck"


class State:
    """Trạng thái trong bài toán Vacuum World"""
    
    def __init__(self, robot_pos: Tuple[int, int], dirt_set: Set[Tuple[int, int]]):
        self.robot_pos = robot_pos
        self.dirt_set = frozenset(dirt_set)
    
    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.robot_pos == other.robot_pos and self.dirt_set == other.dirt_set
    
    def __hash__(self):
        return hash((self.robot_pos, self.dirt_set))
    
    def __repr__(self):
        return f"State(Robot: {self.robot_pos}, Dirt: {set(self.dirt_set)})"
    
    def is_goal(self) -> bool:
        """Kiểm tra trạng thái đích (không còn bụi)"""
        return len(self.dirt_set) == 0


class SearchResult:
    """Kết quả tìm kiếm"""
    
    def __init__(self, path: List[Action], nodes_expanded: int, 
                 time_taken: float, memory_used: int, success: bool,
                 algorithm_name: str = "Unknown"):
        self.path = path
        self.nodes_expanded = nodes_expanded
        self.time_taken = time_taken
        self.memory_used = memory_used
        self.success = success
        self.algorithm_name = algorithm_name
    
    def __repr__(self):
        return (f"SearchResult(algo={self.algorithm_name}, success={self.success}, "
                f"steps={len(self.path)}, nodes={self.nodes_expanded})")
