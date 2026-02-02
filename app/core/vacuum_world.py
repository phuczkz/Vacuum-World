"""
Module chứa logic môi trường Vacuum World
"""

import random
from typing import Set, Tuple, List

from app.models import Action, State


# Cấu hình mặc định
DEFAULT_GRID_SIZE = 5
MIN_GRID_SIZE = 2
MAX_GRID_SIZE = 10


class VacuumWorld:
    """Môi trường Vacuum World"""
    
    def __init__(self, grid_size: int = DEFAULT_GRID_SIZE):
        self.grid_size = grid_size
        self.robot_pos = (0, 0)
        self.dirt_set: Set[Tuple[int, int]] = set()
        self.action_history: List[Action] = []
        self.path_history: List[Tuple[int, int]] = []
        self.total_cost = 0
        self.performance_points = 0
        
    def reset(self):
        """Reset môi trường"""
        self.robot_pos = (0, 0)
        self.dirt_set = set()
        self.action_history = []
        self.path_history = [(0, 0)]
        self.total_cost = 0
        self.performance_points = 0
    
    def set_robot_position(self, pos: Tuple[int, int]):
        """Đặt vị trí robot"""
        if 0 <= pos[0] < self.grid_size and 0 <= pos[1] < self.grid_size:
            self.robot_pos = pos
            self.path_history = [pos]
            self.performance_points = 0
    
    def add_dirt(self, pos: Tuple[int, int]):
        """Thêm bụi"""
        if 0 <= pos[0] < self.grid_size and 0 <= pos[1] < self.grid_size:
            self.dirt_set.add(pos)
    
    def remove_dirt(self, pos: Tuple[int, int]):
        """Xóa bụi"""
        self.dirt_set.discard(pos)
    
    def toggle_dirt(self, pos: Tuple[int, int]):
        """Bật/tắt bụi"""
        if pos in self.dirt_set:
            self.remove_dirt(pos)
        else:
            self.add_dirt(pos)
    
    def random_dirt(self, probability: float = 0.3):
        """Phân bỏ bụi ngẫu nhiên"""
        self.dirt_set.clear()
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if random.random() < probability:
                    self.dirt_set.add((x, y))
        self.performance_points = 0
    
    def get_valid_actions(self) -> List[Action]:
        """Lấy danh sách hành động hợp lệ"""
        actions = []
        x, y = self.robot_pos
        
        if y > 0:
            actions.append(Action.UP)
        if y < self.grid_size - 1:
            actions.append(Action.DOWN)
        if x > 0:
            actions.append(Action.LEFT)
        if x < self.grid_size - 1:
            actions.append(Action.RIGHT)
        actions.append(Action.SUCK)
        
        return actions
    
    def execute_action(self, action: Action) -> bool:
        """
        Thực hiện hành động - Transition Function
        
        Returns:
            True nếu môi trường đã sạch (goal state)
        """
        x, y = self.robot_pos
        new_x, new_y = x, y
        points_gained = -1 # Mọi hành động đều tốn 1 điểm
        
        if action == Action.UP:
            new_y = max(0, y - 1)
        elif action == Action.DOWN:
            new_y = min(self.grid_size - 1, y + 1)
        elif action == Action.LEFT:
            new_x = max(0, x - 1)
        elif action == Action.RIGHT:
            new_x = min(self.grid_size - 1, x + 1)
        elif action == Action.SUCK:
            if self.robot_pos in self.dirt_set:
                self.dirt_set.remove(self.robot_pos)
                points_gained += 10 # Hút bụi thành công được +10 điểm
        
        old_pos = self.robot_pos
        self.robot_pos = (new_x, new_y)
        
        self.action_history.append(action)
        if self.robot_pos != old_pos:
            self.path_history.append(self.robot_pos)
        self.total_cost += 1
        self.performance_points += points_gained
        
        return len(self.dirt_set) == 0
    
    def get_state(self) -> State:
        """Lấy trạng thái hiện tại"""
        return State(self.robot_pos, self.dirt_set)
    
    def get_state_path(self, path: List[Action], start_state: State = None) -> List[State]:
        """
        Lấy danh sách các trạng thái đi qua dựa trên chuỗi hành động.
        
        Args:
            path: Danh sách các hành động
            start_state: Trạng thái bắt đầu (mặc định là trạng thái hiện tại)
            
        Returns:
            List các State
        """
        if start_state is None:
            start_state = self.get_state()
            
        states = [start_state]
        current_state = start_state
        
        for action in path:
            successors = VacuumWorld.get_successors(current_state, self.grid_size)
            # Tìm trạng thái tương ứng với hành động
            found = False
            for act, next_state in successors:
                if act == action:
                    current_state = next_state
                    states.append(current_state)
                    found = True
                    break
            if not found:
                # Nếu không tìm thấy (hành động lỗi), giữ nguyên trạng thái
                states.append(current_state)
                
        return states
    
    def set_grid_size(self, size: int):
        """Thay đổi kích thước lưới"""
        self.grid_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, size))
        # Xóa bụi ngoài phạm vi mới
        self.dirt_set = {(x, y) for x, y in self.dirt_set 
                         if x < self.grid_size and y < self.grid_size}
        # Điều chỉnh vị trí robot nếu cần
        rx, ry = self.robot_pos
        self.robot_pos = (min(rx, self.grid_size - 1), min(ry, self.grid_size - 1))
        self.path_history = [self.robot_pos]
    
    @staticmethod
    def get_successors(state: State, grid_size: int) -> List[Tuple[Action, State]]:
        """
        Sinh các trạng thái kế tiếp - dùng cho thuật toán tìm kiếm
        
        Args:
            state: Trạng thái hiện tại
            grid_size: Kích thước lưới
            
        Returns:
            List các tuple (action, next_state)
        """
        successors = []
        x, y = state.robot_pos
        
        # Các hành động di chuyển
        moves = [
            (Action.UP, (x, y - 1)),
            (Action.DOWN, (x, y + 1)),
            (Action.LEFT, (x - 1, y)),
            (Action.RIGHT, (x + 1, y))
        ]
        
        for action, (nx, ny) in moves:
            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                new_state = State((nx, ny), state.dirt_set)
                successors.append((action, new_state))
        
        # Hành động hút bụi (chỉ khi có bụi tại vị trí hiện tại)
        if state.robot_pos in state.dirt_set:
            new_dirt = set(state.dirt_set) - {state.robot_pos}
            new_state = State(state.robot_pos, new_dirt)
            successors.append((Action.SUCK, new_state))
        
        return successors
