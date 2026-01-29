"""
Fast Greedy Nearest Neighbor algorithm for large boards
"""

import time
from typing import Set, List, Tuple
from app.models import State, Action, SearchResult
from app.core import VacuumWorld


def greedy_nearest_neighbor(initial_state: State, grid_size: int, progress=None) -> SearchResult:
    """
    Greedy Nearest Neighbor - Fast non-optimal algorithm
    
    Always moves to the nearest dirt cell and sucks it.
    Guaranteed to complete quickly even on large boards.
    Time complexity: O(k²·n²) where k=dirt count, n=grid size.
    """
    start_time = time.time()
    
    current_state = initial_state
    remaining_dirt = set(initial_state.dirt_set)
    path = []
    nodes_expanded = 0
    explored_nodes = []
    search_tree = []
    
    while remaining_dirt:
        # Find nearest dirt using Manhattan distance
        curr_x, curr_y = current_state.robot_pos
        nearest_dirt = None
        min_distance = float('inf')
        
        for dirt_pos in remaining_dirt:
            distance = abs(curr_x - dirt_pos[0]) + abs(curr_y - dirt_pos[1])
            if distance < min_distance:
                min_distance = distance
                nearest_dirt = dirt_pos
        
        # Move to nearest dirt using simple Manhattan pathfinding
        target_x, target_y = nearest_dirt
        
        # Helper to record a step
        def record_step(action, next_s):
            nonlocal current_state, nodes_expanded
            # Add all possible actions to tree for visualization
            for act, succ in VacuumWorld.get_successors(current_state, grid_size):
                # Distance to the target dirt for this successor
                dist = abs(succ.robot_pos[0] - target_x) + abs(succ.robot_pos[1] - target_y)
                search_tree.append((current_state, act, succ, dist))
            
            explored_nodes.append(current_state.robot_pos)
            current_state = next_s
            path.append(action)
            nodes_expanded += 1
            if progress and nodes_expanded % 10 == 0:
                progress.update(nodes_expanded, len(remaining_dirt))

        # Move horizontally first
        while current_state.robot_pos[0] != target_x:
            cx, cy = current_state.robot_pos
            if cx < target_x:
                action = Action.RIGHT
                next_pos = (cx + 1, cy)
            else:
                action = Action.LEFT
                next_pos = (cx - 1, cy)
            next_state = State(next_pos, current_state.dirt_set)
            record_step(action, next_state)
        
        # Then move vertically
        while current_state.robot_pos[1] != target_y:
            cx, cy = current_state.robot_pos
            if cy < target_y:
                action = Action.DOWN
                next_pos = (cx, cy + 1)
            else:
                action = Action.UP
                next_pos = (cx, cy - 1)
            next_state = State(next_pos, current_state.dirt_set)
            record_step(action, next_state)
        
        # Suck the dirt
        new_dirt = set(current_state.dirt_set) - {current_state.robot_pos}
        next_state = State(current_state.robot_pos, new_dirt)
        record_step(Action.SUCK, next_state)
        
        remaining_dirt.discard(current_state.robot_pos)
    
    return SearchResult(
        path=path,
        nodes_expanded=nodes_expanded,
        time_taken=time.time() - start_time,
        memory_used=len(initial_state.dirt_set),
        success=True,
        algorithm_name="Nearest Neighbor",
        explored_nodes=explored_nodes,
        search_tree=search_tree
    )
