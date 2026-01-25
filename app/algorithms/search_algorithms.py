"""
Module chứa các thuật toán tìm kiếm

Mỗi thuật toán có signature:
    def algorithm(initial_state: State, grid_size: int) -> SearchResult

Bạn có thể tạo thuật toán tùy chỉnh với signature tương tự.
"""

import time
from collections import deque
import heapq
from typing import Callable, Dict

from app.models import State, Action, SearchResult
from app.core import VacuumWorld


class SearchAlgorithms:
    """Các giải thuật tìm kiếm mẫu"""
    
    @staticmethod
    def heuristic(state: State, grid_size: int) -> int:
        """
        Heuristic: Manhattan distance đến ô bụi gần nhất + số ô bụi còn lại
        
        Args:
            state: Trạng thái hiện tại
            grid_size: Kích thước lưới (không dùng nhưng giữ để thống nhất signature)
            
        Returns:
            Giá trị heuristic
        """
        if not state.dirt_set:
            return 0
        
        x, y = state.robot_pos
        min_distance = float('inf')
        
        for dx, dy in state.dirt_set:
            distance = abs(x - dx) + abs(y - dy)
            min_distance = min(min_distance, distance)
        
        return int(min_distance) + len(state.dirt_set) - 1
    
    @staticmethod
    def bfs(initial_state: State, grid_size: int) -> SearchResult:
        """
        Breadth-First Search - Tìm kiếm theo chiều rộng
        
        Uninformed search, đảm bảo tìm được đường đi ngắn nhất (theo số bước).
        """
        start_time = time.time()
        
        frontier = deque([(initial_state, [])])
        explored = {initial_state}
        nodes_expanded = 0
        max_frontier_size = 1
        
        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            state, path = frontier.popleft()
            nodes_expanded += 1
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="BFS"
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                if next_state not in explored:
                    explored.add(next_state)
                    frontier.append((next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "BFS")
    
    @staticmethod
    def dfs(initial_state: State, grid_size: int, max_depth: int = 100) -> SearchResult:
        """
        Depth-First Search - Tìm kiếm theo chiều sâu
        
        Uninformed search, không đảm bảo tối ưu, có giới hạn độ sâu.
        """
        start_time = time.time()
        
        frontier = [(initial_state, [])]
        explored = set()
        nodes_expanded = 0
        max_frontier_size = 1
        
        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            state, path = frontier.pop()
            
            if len(path) > max_depth:
                continue
            
            if state in explored:
                continue
            
            explored.add(state)
            nodes_expanded += 1
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="DFS"
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                if next_state not in explored:
                    frontier.append((next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "DFS")
    
    @staticmethod
    def ucs(initial_state: State, grid_size: int) -> SearchResult:
        """
        Uniform Cost Search - Tìm kiếm chi phí đều
        
        Uninformed search, đảm bảo tối ưu khi chi phí không âm.
        """
        start_time = time.time()
        
        counter = 0
        frontier = [(0, counter, initial_state, [])]
        explored = {}
        nodes_expanded = 0
        max_frontier_size = 1
        
        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            cost, _, state, path = heapq.heappop(frontier)
            
            if state in explored and explored[state] <= cost:
                continue
            
            explored[state] = cost
            nodes_expanded += 1
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="UCS"
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                new_cost = cost + 1
                if next_state not in explored or explored[next_state] > new_cost:
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "UCS")
    
    @staticmethod
    def greedy(initial_state: State, grid_size: int) -> SearchResult:
        """
        Greedy Best-First Search
        
        Informed search, sử dụng heuristic, không đảm bảo tối ưu.
        """
        start_time = time.time()
        
        counter = 0
        h = SearchAlgorithms.heuristic(initial_state, grid_size)
        frontier = [(h, counter, initial_state, [])]
        explored = set()
        nodes_expanded = 0
        max_frontier_size = 1
        
        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            _, _, state, path = heapq.heappop(frontier)
            
            if state in explored:
                continue
            
            explored.add(state)
            nodes_expanded += 1
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="Greedy"
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                if next_state not in explored:
                    counter += 1
                    h = SearchAlgorithms.heuristic(next_state, grid_size)
                    heapq.heappush(frontier, (h, counter, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "Greedy")
    
    @staticmethod
    def astar(initial_state: State, grid_size: int) -> SearchResult:
        """
        A* Search
        
        Informed search, kết hợp chi phí thực và heuristic, đảm bảo tối ưu
        nếu heuristic admissible.
        """
        start_time = time.time()
        
        counter = 0
        h = SearchAlgorithms.heuristic(initial_state, grid_size)
        frontier = [(h, counter, 0, initial_state, [])]
        explored = {}
        nodes_expanded = 0
        max_frontier_size = 1
        
        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            f, _, g, state, path = heapq.heappop(frontier)
            
            if state in explored and explored[state] <= g:
                continue
            
            explored[state] = g
            nodes_expanded += 1
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="A*"
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                new_g = g + 1
                if next_state not in explored or explored[next_state] > new_g:
                    counter += 1
                    h = SearchAlgorithms.heuristic(next_state, grid_size)
                    heapq.heappush(frontier, (new_g + h, counter, new_g, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "A*")


# Dict các thuật toán mặc định
DEFAULT_ALGORITHMS: Dict[str, Callable] = {
    "BFS": SearchAlgorithms.bfs,
    "DFS": SearchAlgorithms.dfs,
    "UCS": SearchAlgorithms.ucs,
    "Greedy": SearchAlgorithms.greedy,
    "A*": SearchAlgorithms.astar,
}
