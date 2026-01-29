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
from .greedy_nn import greedy_nearest_neighbor

# Limits for search-tree visualization
TREE_EDGE_LIMIT = 20000

# Performance limits to prevent infinite search on large boards
MAX_TIME_SECONDS = 30.0  # Maximum time allowed for search
MAX_NODES = 1000000  # Maximum nodes to expand


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
    def bfs(initial_state: State, grid_size: int, progress=None) -> SearchResult:
        """
        Breadth-First Search - Tìm kiếm theo chiều rộng
        
        Uninformed search, đảm bảo tìm được đường đi ngắn nhất (theo số bước).
        Cấu trúc dữ liệu: Hàng đợi (Queue - FIFO)
        """
        start_time = time.time()
        
        # Kiểm tra nếu trạng thái ban đầu đã là đích
        if initial_state.is_goal():
            return SearchResult(
                path=[],
                nodes_expanded=0,
                time_taken=time.time() - start_time,
                memory_used=1,
                success=True,
                algorithm_name="BFS"
            )
        
        frontier = deque([(initial_state, [])])  # Hàng đợi (FIFO)
        frontier_set = {initial_state}  # Để kiểm tra child not in frontier
        explored = set()  # Tập trạng thái đã duyệt
        nodes_expanded = 0
        max_frontier_size = 1
        search_tree = []  # List of (parent_pos, action, child_pos)
        tree_node_limit = TREE_EDGE_LIMIT  # Capture more edges for larger boards
        
        while frontier:
            # Check timeout and node limit
            if time.time() - start_time > MAX_TIME_SECONDS:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "BFS (timeout)")
            if nodes_expanded > MAX_NODES:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "BFS (node limit)",
                                  explored_nodes=[s.robot_pos for s in explored],
                                  search_tree=search_tree)
            
            max_frontier_size = max(max_frontier_size, len(frontier))
            state, path = frontier.popleft()
            frontier_set.remove(state)
            
            explored.add(state)
            nodes_expanded += 1
            
            # Update progress every 100 nodes
            if progress and nodes_expanded % 100 == 0:
                progress.update(nodes_expanded, len(frontier))
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                if len(search_tree) < tree_node_limit:
                    search_tree.append((state, action, next_state, len(path) + 1))
                
                if next_state not in explored and next_state not in frontier_set:
                    if next_state.is_goal():
                        return SearchResult(
                            path=path + [action],
                            nodes_expanded=nodes_expanded,
                            time_taken=time.time() - start_time,
                            memory_used=max_frontier_size,
                            success=True,
                            algorithm_name="BFS",
                            explored_nodes=[s.robot_pos for s in explored],
                            search_tree=search_tree
                        )
                    frontier.append((next_state, path + [action]))
                    frontier_set.add(next_state)
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "BFS", 
                          explored_nodes=[s.robot_pos for s in explored],
                          search_tree=search_tree)
    
    @staticmethod
    def dfs(initial_state: State, grid_size: int, progress=None, max_depth: int = 100) -> SearchResult:
        """
        Depth-First Search - Tìm kiếm theo chiều sâu
        
        Uninformed search, không đảm bảo tối ưu, có giới hạn độ sâu.
        Cấu trúc dữ liệu: Ngăn xếp (Stack - LIFO)
        """
        start_time = time.time()
        
        # Kiểm tra nếu trạng thái ban đầu đã là đích
        if initial_state.is_goal():
            return SearchResult(
                path=[],
                nodes_expanded=0,
                time_taken=time.time() - start_time,
                memory_used=1,
                success=True,
                algorithm_name="DFS"
            )
        
        frontier = [(initial_state, [])]  # Ngăn xếp (LIFO)
        frontier_set = {initial_state}  # Để kiểm tra child not in frontier
        explored = set()  # Tập trạng thái đã duyệt
        nodes_expanded = 0
        max_frontier_size = 1
        search_tree = []
        tree_node_limit = TREE_EDGE_LIMIT
        
        while frontier:
            # Check timeout and node limit
            if time.time() - start_time > MAX_TIME_SECONDS:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "DFS (timeout)",
                                  explored_nodes=[s.robot_pos for s in explored])
            if nodes_expanded > MAX_NODES:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "DFS (node limit)",
                                  explored_nodes=[s.robot_pos for s in explored])
            
            max_frontier_size = max(max_frontier_size, len(frontier))
            state, path = frontier.pop()
            frontier_set.discard(state)
            
            if len(path) > max_depth:
                continue
            
            explored.add(state)
            nodes_expanded += 1
            
            # Update progress every 100 nodes
            if progress and nodes_expanded % 100 == 0:
                progress.update(nodes_expanded, len(frontier))
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="DFS",
                    explored_nodes=[s.robot_pos for s in explored],
                    search_tree=search_tree
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                if len(search_tree) < tree_node_limit:
                    search_tree.append((state, action, next_state, len(path) + 1))
                    
                if next_state not in explored and next_state not in frontier_set:
                    frontier.append((next_state, path + [action]))
                    frontier_set.add(next_state)
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "DFS")
    
    @staticmethod
    def ucs(initial_state: State, grid_size: int, progress=None) -> SearchResult:
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
        search_tree = []
        tree_node_limit = TREE_EDGE_LIMIT
        
        while frontier:
            # Check timeout and node limit
            if time.time() - start_time > MAX_TIME_SECONDS:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "UCS (timeout)",
                                  explored_nodes=[s.robot_pos for s in explored],
                                  search_tree=search_tree)
            if nodes_expanded > MAX_NODES:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "UCS (node limit)",
                                  explored_nodes=[s.robot_pos for s in explored],
                                  search_tree=search_tree)
            
            max_frontier_size = max(max_frontier_size, len(frontier))
            cost, _, state, path = heapq.heappop(frontier)
            
            if state in explored and explored[state] <= cost:
                continue
            
            explored[state] = cost
            nodes_expanded += 1
            
            # Update progress every 100 nodes
            if progress and nodes_expanded % 100 == 0:
                progress.update(nodes_expanded, len(frontier))
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="UCS",
                    explored_nodes=[s.robot_pos for s in explored],
                    search_tree=search_tree
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                new_cost = cost + 1
                if len(search_tree) < tree_node_limit:
                    search_tree.append((state, action, next_state, new_cost))
                if next_state not in explored or explored[next_state] > new_cost:
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "UCS",
                          explored_nodes=[s.robot_pos for s in explored],
                          search_tree=search_tree)
    
    @staticmethod
    def greedy(initial_state: State, grid_size: int, progress=None) -> SearchResult:
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
        search_tree = []
        tree_node_limit = TREE_EDGE_LIMIT
        
        while frontier:
            # Check timeout and node limit
            if time.time() - start_time > MAX_TIME_SECONDS:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "Greedy (timeout)")
            if nodes_expanded > MAX_NODES:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "Greedy (node limit)")
            
            max_frontier_size = max(max_frontier_size, len(frontier))
            _, _, state, path = heapq.heappop(frontier)
            
            if state in explored:
                continue
            
            explored.add(state)
            nodes_expanded += 1
            
            # Update progress every 100 nodes
            if progress and nodes_expanded % 100 == 0:
                progress.update(nodes_expanded, len(frontier))
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="Greedy",
                    explored_nodes=[s.robot_pos for s in explored],
                    search_tree=search_tree
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                h = SearchAlgorithms.heuristic(next_state, grid_size)
                if len(search_tree) < tree_node_limit:
                    search_tree.append((state, action, next_state, h))
                if next_state not in explored:
                    counter += 1
                    heapq.heappush(frontier, (h, counter, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "Greedy",
                          explored_nodes=[s.robot_pos for s in explored],
                          search_tree=search_tree)
    
    @staticmethod
    def astar(initial_state: State, grid_size: int, progress=None) -> SearchResult:
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
        search_tree = []
        tree_node_limit = TREE_EDGE_LIMIT
        
        while frontier:
            # Check timeout and node limit
            if time.time() - start_time > MAX_TIME_SECONDS:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "A* (timeout)",
                                  explored_nodes=[s.robot_pos for s in explored],
                                  search_tree=search_tree)
            if nodes_expanded > MAX_NODES:
                return SearchResult([], nodes_expanded, time.time() - start_time, 
                                  max_frontier_size, False, "A* (node limit)",
                                  explored_nodes=[s.robot_pos for s in explored],
                                  search_tree=search_tree)
            
            max_frontier_size = max(max_frontier_size, len(frontier))
            f, _, g, state, path = heapq.heappop(frontier)
            
            if state in explored and explored[state] <= g:
                continue
            
            explored[state] = g
            nodes_expanded += 1
            
            # Update progress every 100 nodes
            if progress and nodes_expanded % 100 == 0:
                progress.update(nodes_expanded, len(frontier))
            
            if state.is_goal():
                return SearchResult(
                    path=path,
                    nodes_expanded=nodes_expanded,
                    time_taken=time.time() - start_time,
                    memory_used=max_frontier_size,
                    success=True,
                    algorithm_name="A*",
                    explored_nodes=[s.robot_pos for s in explored],
                    search_tree=search_tree
                )
            
            for action, next_state in VacuumWorld.get_successors(state, grid_size):
                new_g = g + 1
                h = SearchAlgorithms.heuristic(next_state, grid_size)
                if len(search_tree) < tree_node_limit:
                    search_tree.append((state, action, next_state, new_g + h))
                if next_state not in explored or explored[next_state] > new_g:
                    counter += 1
                    h = SearchAlgorithms.heuristic(next_state, grid_size)
                    heapq.heappush(frontier, (new_g + h, counter, new_g, next_state, path + [action]))
        
        return SearchResult([], nodes_expanded, time.time() - start_time, 
                          max_frontier_size, False, "A*",
                          explored_nodes=[s.robot_pos for s in explored],
                          search_tree=search_tree)


# Dict các thuật toán mặc định
DEFAULT_ALGORITHMS: Dict[str, Callable] = {
    "BFS": SearchAlgorithms.bfs,
    "DFS": SearchAlgorithms.dfs,
    "UCS": SearchAlgorithms.ucs,
    "Greedy": SearchAlgorithms.greedy,
    "A*": SearchAlgorithms.astar,
    "Nearest Neighbor": greedy_nearest_neighbor,
}
