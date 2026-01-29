"""
Giao diện đồ họa chính cho Vacuum World
"""

import pygame
import random
import os
import threading
from collections import defaultdict, deque
from typing import List, Optional, Callable, Dict, Tuple, Set

from app.models import Action, State, SearchResult, SearchProgress
from app.core import VacuumWorld, DEFAULT_GRID_SIZE, MIN_GRID_SIZE, MAX_GRID_SIZE
from app.algorithms import SearchAlgorithms, DEFAULT_ALGORITHMS
from .config import (COLORS, MIN_CELL_SIZE, MAX_CELL_SIZE, SIDEBAR_WIDTH, 
                     TOP_BAR_HEIGHT, BOTTOM_BAR_HEIGHT, MIN_INFO_WIDTH,
                     BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING)
from .components import Button


class VacuumWorldGUI:
    """
    Giao diện đồ họa chính cho Vacuum World.
    
    Hỗ trợ truyền các thuật toán tùy chỉnh thông qua parameter `custom_algorithms`.
    
    Ví dụ sử dụng:
    ```python
    def my_custom_search(initial_state: State, grid_size: int) -> SearchResult:
        # Implement thuật toán của bạn
        ...
        return SearchResult(path, nodes, time, memory, success, "MyAlgo")
    
    app = VacuumWorldGUI(custom_algorithms={"MyAlgo": my_custom_search})
    app.run()
    ```
    """
    
    def __init__(self, 
                 grid_size: int = DEFAULT_GRID_SIZE,
                 custom_algorithms: Dict[str, Callable] = None):
        """
        Khởi tạo GUI.
        
        Args:
            grid_size: Kích thước lưới ban đầu
            custom_algorithms: Dict các thuật toán tùy chỉnh {tên: function}
        """
        pygame.init()
        pygame.display.set_caption("Vacuum World - Robot Hút Bụi")
        
        # Thiết lập thuật toán
        self.algorithms = dict(DEFAULT_ALGORITHMS)
        if custom_algorithms:
            self.algorithms.update(custom_algorithms)
        
        self.algorithm_names = list(self.algorithms.keys())
        self.selected_algorithm_index = 0
        self.selected_algorithm = self.algorithm_names[0]
        
        # Khởi tạo world
        self.world = VacuumWorld(grid_size)
        
        # Tính toán kích thước
        self.cell_size = MAX_CELL_SIZE
        self.grid_offset_x = 15
        self.grid_offset_y = TOP_BAR_HEIGHT + 5
        self.calculate_dimensions()
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_large = pygame.font.SysFont('Arial', 22, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 16)
        self.font_small = pygame.font.SysFont('Arial', 13)
        
        # Trạng thái
        self.placing_robot = False
        self.auto_running = False
        self.solution_path: List[Action] = []
        self.current_step = 0
        self.animation_speed = 500
        self.last_step_time = 0
        self.search_result: Optional[SearchResult] = None
        self.solution_positions: Set[Tuple[int, int]] = set() # Robot positions on solution path
        self.solution_states: List[State] = [] # Sequence of states in solution

        
        # Threading state
        self.is_searching = False
        self.search_thread: Optional[threading.Thread] = None
        self.pending_search_result: Optional[SearchResult] = None
        self.algorithm_warning: Optional[str] = None 
        self.search_progress = SearchProgress()  # Progress tracking
        self.show_search_viz = True  # Toggle for search visualization
        
        # Lưu vị trí bụi cố định để vẽ
        self.dirt_positions: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
        
        # Message
        self.message = ""
        self.message_time = 0
        
        # Load hình ảnh robot
        self.robot_image = None
        self.robot_image_scaled = None
        self._load_robot_image()
        
        # Tạo buttons
        self.buttons: Dict[str, Button] = {}
        self.create_buttons()
        
        # Khởi tạo môi trường
        self.world.random_dirt(0.3)
        self.regenerate_dirt_visuals()
        self.world.path_history = [self.world.robot_pos]
    
    def calculate_dimensions(self):
        """Tính toán kích thước cửa sổ"""
        if self.world.grid_size <= 3:
            self.cell_size = MAX_CELL_SIZE
        elif self.world.grid_size <= 5:
            self.cell_size = 75
        elif self.world.grid_size <= 7:
            self.cell_size = 65
        else:
            self.cell_size = MIN_CELL_SIZE
        
        grid_area = self.world.grid_size * self.cell_size
        
        num_algo = len(self.algorithm_names) if hasattr(self, 'algorithm_names') else 5
        sidebar_height = 50 + (4 * 30) + 10 + (num_algo * 30) + 10 + (4 * 30) + 40
        
        self.window_width = grid_area + SIDEBAR_WIDTH + 600 + 100  # Even wider for massive tree
        self.window_height = max(grid_area + TOP_BAR_HEIGHT + BOTTOM_BAR_HEIGHT + 20, 
                                sidebar_height + TOP_BAR_HEIGHT + 20)
    
    def create_buttons(self):
        """Tạo tất cả các nút bấm"""
        self.buttons = {}
        self.update_button_positions()
    
    def update_button_positions(self):
        """Cập nhật vị trí các nút"""
        sidebar_x = self.world.grid_size * self.cell_size + self.grid_offset_x + 15
        y = self.grid_offset_y
        
        # Kích thước lưới
        if 'size_down' not in self.buttons:
            self.buttons['size_down'] = Button(sidebar_x, y, 35, BUTTON_HEIGHT, "-", COLORS['ORANGE'])
            self.buttons['size_up'] = Button(sidebar_x + BUTTON_WIDTH - 35, y, 35, BUTTON_HEIGHT, "+", COLORS['ORANGE'])
        else:
            self.buttons['size_down'].set_position(sidebar_x, y)
            self.buttons['size_up'].set_position(sidebar_x + BUTTON_WIDTH - 35, y)
        
        y += BUTTON_HEIGHT + BUTTON_SPACING + 8
        
        # Environment controls
        env_buttons = [
            ('random_dirt', "Random Dirt", COLORS['BROWN']),
            ('clear_dirt', "Clear Dirt", COLORS['DARK_GRAY']),
            ('place_robot', "Place Robot", COLORS['BLUE']),
            ('reset', "Reset All", COLORS['RED']),
        ]
        
        for name, text, color in env_buttons:
            if name not in self.buttons:
                self.buttons[name] = Button(sidebar_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, text, color)
            else:
                self.buttons[name].set_position(sidebar_x, y)
            y += BUTTON_HEIGHT + BUTTON_SPACING
        
        y += 6
        
        # Thuật toán
        for algo_name in self.algorithm_names:
            btn_name = f'algo_{algo_name}'
            is_selected = (algo_name == self.selected_algorithm)
            color = COLORS['GREEN'] if is_selected else COLORS['DARK_GRAY']
            
            if btn_name not in self.buttons:
                self.buttons[btn_name] = Button(sidebar_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, algo_name, color)
            else:
                self.buttons[btn_name].set_position(sidebar_x, y)
                self.buttons[btn_name].color = color
            y += BUTTON_HEIGHT + BUTTON_SPACING
        
        y += 6
        
        # Run controls
        run_buttons = [
            ('solve', "Find Path", COLORS['GREEN']),
            ('step', "Step", COLORS['BLUE']),
            ('auto_run', "Auto Run", COLORS['PURPLE']),
            ('stop', "Stop", COLORS['RED']),
        ]
        
        for name, text, color in run_buttons:
            if name not in self.buttons:
                self.buttons[name] = Button(sidebar_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, text, color)
            else:
                self.buttons[name].set_position(sidebar_x, y)
            y += BUTTON_HEIGHT + BUTTON_SPACING
        
        y += 6
        
        # Tốc độ
        if 'speed_down' not in self.buttons:
            self.buttons['speed_down'] = Button(sidebar_x, y, 35, BUTTON_HEIGHT, "-", COLORS['CYAN'])
            self.buttons['speed_up'] = Button(sidebar_x + BUTTON_WIDTH - 35, y, 35, BUTTON_HEIGHT, "+", COLORS['CYAN'])
        else:
            self.buttons['speed_down'].set_position(sidebar_x, y)
            self.buttons['speed_up'].set_position(sidebar_x + BUTTON_WIDTH - 35, y)
    
    def resize_window(self):
        """Thay đổi kích thước cửa sổ"""
        self.calculate_dimensions()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        self.update_button_positions()
        self._scale_robot_image()  # Cập nhật kích thước hình ảnh robot
    
    def regenerate_dirt_visuals(self):
        """Tạo lại vị trí random cho bụi"""
        self.dirt_positions = {}
        for pos in self.world.dirt_set:
            self.dirt_positions[pos] = [
                (random.randint(-12, 12), random.randint(-12, 12), random.randint(4, 8))
                for _ in range(6)
            ]
    
    def show_message(self, msg: str):
        """Hiển thị thông báo"""
        self.message = msg
        self.message_time = pygame.time.get_ticks()
    
    # ========================== DRAW METHODS ==========================
    
    def draw_grid(self):
        """Vẽ lưới môi trường"""
        for y in range(self.world.grid_size):
            for x in range(self.world.grid_size):
                rect_x = self.grid_offset_x + x * self.cell_size
                rect_y = self.grid_offset_y + y * self.cell_size
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)
                
                color = COLORS['LIGHT_BROWN'] if (x + y) % 2 == 0 else COLORS['WHITE']
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLORS['DARK_GRAY'], rect, 1)
                
                coord_text = self.font_small.render(f"({x},{y})", True, COLORS['DARK_GRAY'])
                self.screen.blit(coord_text, (rect_x + 3, rect_y + 2))
    
    def draw_path(self):
        """Vẽ đường đi của robot"""
        if len(self.world.path_history) > 1:
            points = []
            for pos in self.world.path_history:
                px = self.grid_offset_x + pos[0] * self.cell_size + self.cell_size // 2
                py = self.grid_offset_y + pos[1] * self.cell_size + self.cell_size // 2
                points.append((px, py))
            
            if len(points) >= 2:
                pygame.draw.lines(self.screen, COLORS['LIGHT_BLUE'], False, points, 3)
                for point in points[:-1]:
                    pygame.draw.circle(self.screen, COLORS['BLUE'], point, 5)
    
    def draw_dirt(self):
        """Vẽ bụi"""
        for pos in self.world.dirt_set:
            center_x = self.grid_offset_x + pos[0] * self.cell_size + self.cell_size // 2
            center_y = self.grid_offset_y + pos[1] * self.cell_size + self.cell_size // 2
            
            if pos not in self.dirt_positions:
                self.dirt_positions[pos] = [
                    (random.randint(-12, 12), random.randint(-12, 12), random.randint(4, 8))
                    for _ in range(6)
                ]
            
            for offset_x, offset_y, radius in self.dirt_positions[pos]:
                scale = self.cell_size / MAX_CELL_SIZE
                scaled_ox = int(offset_x * scale)
                scaled_oy = int(offset_y * scale)
                scaled_r = max(2, int(radius * scale))
                pygame.draw.circle(self.screen, COLORS['BROWN'], 
                                 (center_x + scaled_ox, center_y + scaled_oy), scaled_r)
    
    def _load_robot_image(self):
        """Load hình ảnh robot từ file PNG"""
        try:
            # Đường dẫn đến hình ảnh
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            image_path = os.path.join(base_path, "assets", "vacuum.png")
            
            if os.path.exists(image_path):
                self.robot_image = pygame.image.load(image_path).convert_alpha()
                self._scale_robot_image()
                print(f"✅ Đã tải hình ảnh robot từ: {image_path}")
            else:
                print(f"⚠️ Không tìm thấy hình ảnh tại: {image_path}")
                print("   Sử dụng robot mặc định (vẽ bằng code)")
                self.robot_image = None
        except Exception as e:
            print(f"❌ Lỗi khi tải hình ảnh: {e}")
            self.robot_image = None
    
    def _scale_robot_image(self):
        """Scale hình ảnh robot theo kích thước ô"""
        if self.robot_image:
            # Kích thước robot = 85% kích thước ô
            new_size = int(self.cell_size * 0.85)
            self.robot_image_scaled = pygame.transform.smoothscale(
                self.robot_image, (new_size, new_size)
            )
    
    def draw_robot(self):
        """Vẽ robot hút bụi"""
        rx, ry = self.world.robot_pos
        center_x = self.grid_offset_x + rx * self.cell_size + self.cell_size // 2
        center_y = self.grid_offset_y + ry * self.cell_size + self.cell_size // 2
        
        # Nếu có hình ảnh, dùng hình ảnh
        if self.robot_image_scaled:
            img_rect = self.robot_image_scaled.get_rect(center=(center_x, center_y))
            self.screen.blit(self.robot_image_scaled, img_rect)
        else:
            # Fallback: Vẽ robot bằng code nếu không có hình ảnh
            self._draw_robot_fallback(center_x, center_y)
    
    def _draw_robot_fallback(self, center_x, center_y):
        """Vẽ robot bằng code (fallback khi không có hình ảnh)"""
        scale = self.cell_size / MAX_CELL_SIZE
        
        # Thân robot
        body_r = int(28 * scale)
        inner_r = int(23 * scale)
        pygame.draw.circle(self.screen, COLORS['BLUE'], (center_x, center_y), body_r)
        pygame.draw.circle(self.screen, COLORS['LIGHT_BLUE'], (center_x, center_y), inner_r)
        
        # Mắt
        eye_offset_x = int(8 * scale)
        eye_offset_y = int(6 * scale)
        eye_r = int(6 * scale)
        pupil_r = int(3 * scale)
        
        pygame.draw.circle(self.screen, COLORS['WHITE'], 
                          (center_x - eye_offset_x, center_y - eye_offset_y), eye_r)
        pygame.draw.circle(self.screen, COLORS['WHITE'], 
                          (center_x + eye_offset_x, center_y - eye_offset_y), eye_r)
        pygame.draw.circle(self.screen, COLORS['BLACK'], 
                          (center_x - eye_offset_x, center_y - eye_offset_y), pupil_r)
        pygame.draw.circle(self.screen, COLORS['BLACK'], 
                          (center_x + eye_offset_x, center_y - eye_offset_y), pupil_r)
        
        # Miệng
        mouth_w = int(20 * scale)
        mouth_h = int(12 * scale)
        mouth_y = int(4 * scale)
        pygame.draw.arc(self.screen, COLORS['BLACK'], 
                       (center_x - mouth_w//2, center_y + mouth_y, mouth_w, mouth_h), 
                       3.14, 0, 2)
        
        # Ăng ten
        ant_h = int(12 * scale)
        ant_r = int(3 * scale)
        pygame.draw.line(self.screen, COLORS['DARK_GRAY'], 
                        (center_x - int(4*scale), center_y - body_r + int(5*scale)), 
                        (center_x - int(8*scale), center_y - body_r - ant_h), 2)
        pygame.draw.line(self.screen, COLORS['DARK_GRAY'], 
                        (center_x + int(4*scale), center_y - body_r + int(5*scale)), 
                        (center_x + int(8*scale), center_y - body_r - ant_h), 2)
        pygame.draw.circle(self.screen, COLORS['RED'], 
                          (center_x - int(8*scale), center_y - body_r - ant_h), ant_r)
        pygame.draw.circle(self.screen, COLORS['RED'], 
                          (center_x + int(8*scale), center_y - body_r - ant_h), ant_r)
    
    def draw_top_bar(self):
        """Vẽ thanh tiêu đề"""
        pygame.draw.rect(self.screen, COLORS['LIGHT_BLUE'], 
                        (0, 0, self.window_width, TOP_BAR_HEIGHT))
        
        title = self.font_large.render("VACUUM WORLD - AI Robot Cleaner", True, COLORS['BLUE'])
        self.screen.blit(title, (self.grid_offset_x, 12))
        
        if self.placing_robot:
            hint = self.font_medium.render("Click on a cell to place robot", True, COLORS['RED'])
        else:
            hint = self.font_small.render(
                "Click: Toggle dirt | Arrow keys: Move | S: Suck | Space: Find path", 
                True, COLORS['DARK_GRAY'])
        self.screen.blit(hint, (self.grid_offset_x, 38))
    
    def draw_sidebar(self):
        """Vẽ thanh sidebar"""
        sidebar_x = self.world.grid_size * self.cell_size + self.grid_offset_x + 15
        
        last_btn_bottom = self.buttons['speed_down'].rect.y + self.buttons['speed_down'].rect.height + 10
        sidebar_height = last_btn_bottom - self.grid_offset_y + 10
        
        sidebar_rect = pygame.Rect(sidebar_x - 5, self.grid_offset_y - 5, 
                                   SIDEBAR_WIDTH - 10, sidebar_height)
        pygame.draw.rect(self.screen, (248, 248, 248), sidebar_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLORS['GRAY'], sidebar_rect, 1, border_radius=6)
        
        # Label kích thước
        size_text = self.font_small.render(
            f"{self.world.grid_size}x{self.world.grid_size}", True, COLORS['BLACK'])
        text_rect = size_text.get_rect(center=(sidebar_x + 65, self.grid_offset_y + 14))
        self.screen.blit(size_text, text_rect)
        
        # Vẽ các nút
        for name, button in self.buttons.items():
            button.draw(self.screen, self.font_small)
        
        # Label tốc độ
        speed_y = self.buttons['speed_down'].rect.y
        speed_text = self.font_small.render(f"{self.animation_speed}ms", True, COLORS['BLACK'])
        text_rect = speed_text.get_rect(center=(sidebar_x + 65, speed_y + 14))
        self.screen.blit(speed_text, text_rect)
    
    def draw_bottom_bar(self):
        """Vẽ thanh thông tin phía dưới"""
        grid_bottom = self.grid_offset_y + self.world.grid_size * self.cell_size
        grid_width = self.world.grid_size * self.cell_size
        
        info_width = max(grid_width, MIN_INFO_WIDTH)
        bottom_y = grid_bottom + 8
        
        info_rect = pygame.Rect(self.grid_offset_x - 2, grid_bottom + 2, 
                                info_width + 4, BOTTOM_BAR_HEIGHT - 5)
        pygame.draw.rect(self.screen, (250, 250, 250), info_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS['GRAY'], info_rect, 1, border_radius=5)
        
        # Line 1: Status
        if info_width < 280:
            status_text = f"({self.world.robot_pos[0]},{self.world.robot_pos[1]}) | Dirt:{len(self.world.dirt_set)} | Steps:{self.world.total_cost}"
        else:
            status_text = f"Robot: {self.world.robot_pos} | Dirt: {len(self.world.dirt_set)} | Steps: {self.world.total_cost} | Algo: {self.selected_algorithm}"
        text = self.font_small.render(status_text, True, COLORS['BLACK'])
        self.screen.blit(text, (self.grid_offset_x + 5, bottom_y))
        
        # Show calculating message if searching
        if self.is_searching:
            calc_y = bottom_y + 18
            calc_text = self.font_medium.render("Calculating path...", True, COLORS['ORANGE'])
            self.screen.blit(calc_text, (self.grid_offset_x + 5, calc_y))
            
            # Show warning if there is one
            if self.algorithm_warning:
                warn_y = bottom_y + 36
                warn_text = self.font_small.render(self.algorithm_warning, True, COLORS['RED'])
                self.screen.blit(warn_text, (self.grid_offset_x + 5, warn_y))
            
            return  # Don't show other info while calculating
        
        # Line 2: Search results
        if self.search_result:
            result_y = bottom_y + 18
            if self.search_result.success:
                if info_width < 280:
                    result_text = f"{len(self.search_result.path)}s | N:{self.search_result.nodes_expanded} | {self.search_result.time_taken*1000:.0f}ms"
                else:
                    result_text = (f"Found: {len(self.search_result.path)} steps | "
                                 f"Nodes: {self.search_result.nodes_expanded} | "
                                 f"Time: {self.search_result.time_taken*1000:.1f}ms")
                color = COLORS['GREEN']
            else:
                # Check if it's a timeout or node limit
                algo_name = self.search_result.algorithm_name
                if "timeout" in algo_name:
                    result_text = "Timeout after 15s" if info_width < 280 else f"Failed: Timeout after 15s ({self.search_result.nodes_expanded} nodes)"
                elif "node limit" in algo_name:
                    result_text = "Node limit (100k)" if info_width < 280 else f"Failed: Node limit reached (100,000 nodes)"
                else:
                    result_text = "Not found!" if info_width < 280 else "Path not found!"
                color = COLORS['RED']
            
            text = self.font_small.render(result_text, True, color)
            self.screen.blit(text, (self.grid_offset_x + 5, result_y))
        
        # Dòng 3: Đường đi
        if self.solution_path:
            path_y = bottom_y + 36
            remaining = len(self.solution_path) - self.current_step
            max_actions = max(2, info_width // 60)
            path_str = "->".join([a.value for a in self.solution_path[self.current_step:self.current_step+max_actions]])
            if remaining > max_actions:
                path_str += f"(+{remaining - max_actions})"
            text = self.font_small.render(f"Path:{path_str}", True, COLORS['PURPLE'])
            self.screen.blit(text, (self.grid_offset_x + 5, path_y))
        
        # Dòng 4: Message
        if self.message and pygame.time.get_ticks() - self.message_time < 3000:
            msg_y = bottom_y + 54
            max_chars = info_width // 7
            display_msg = self.message[:max_chars] + "..." if len(self.message) > max_chars else self.message
            msg_text = self.font_small.render(display_msg, True, COLORS['ORANGE'])
            self.screen.blit(msg_text, (self.grid_offset_x + 5, msg_y))
    
    def draw(self):
        """Draw everything"""
        self.screen.fill(COLORS['WHITE'])
        
        self.draw_top_bar()
        self.draw_grid()
        self.draw_path()
        self.draw_dirt()
        self.draw_robot()
        self.draw_sidebar()
        self.draw_bottom_bar()
        self.draw_progress_panel()  # Draw live search progress and tree diagram
        
        pygame.display.flip()
    
    # ========================== EVENT HANDLERS ==========================
    
    def handle_grid_click(self, pos):
        """Xử lý click vào lưới"""
        x = (pos[0] - self.grid_offset_x) // self.cell_size
        y = (pos[1] - self.grid_offset_y) // self.cell_size
        
        if 0 <= x < self.world.grid_size and 0 <= y < self.world.grid_size:
            if self.placing_robot:
                self.world.set_robot_position((x, y))
                self.placing_robot = False
                self.buttons['place_robot'].color = COLORS['BLUE']
                self.show_message(f"Robot placed at ({x}, {y})")
            else:
                self.world.toggle_dirt((x, y))
                if (x, y) in self.world.dirt_set:
                    self.dirt_positions[(x, y)] = [
                        (random.randint(-12, 12), random.randint(-12, 12), random.randint(4, 8))
                        for _ in range(6)
                    ]
                elif (x, y) in self.dirt_positions:
                    del self.dirt_positions[(x, y)]
    
    def handle_button_click(self, name: str):
        """Xử lý click nút"""
        if name == 'size_up':
            if self.world.grid_size < MAX_GRID_SIZE:
                self.world.set_grid_size(self.world.grid_size + 1)
                self.resize_window()
                self.show_message(f"Grid: {self.world.grid_size}x{self.world.grid_size}")
        
        elif name == 'size_down':
            if self.world.grid_size > MIN_GRID_SIZE:
                self.world.set_grid_size(self.world.grid_size - 1)
                self.resize_window()
                self.show_message(f"Grid: {self.world.grid_size}x{self.world.grid_size}")
        
        elif name == 'random_dirt':
            self.world.random_dirt(0.3)
            self.regenerate_dirt_visuals()
            self.solution_path = []
            self.search_result = None
        
        elif name == 'clear_dirt':
            self.world.dirt_set.clear()
            self.dirt_positions.clear()
            self.solution_path = []
            self.search_result = None
        
        elif name == 'place_robot':
            self.placing_robot = not self.placing_robot
            self.buttons['place_robot'].color = COLORS['ORANGE'] if self.placing_robot else COLORS['BLUE']
        
        elif name == 'reset':
            self.world.reset()
            self.dirt_positions.clear()
            self.solution_path = []
            self.search_result = None
            self.auto_running = False
            self.current_step = 0
            self.show_message("Reset complete!")
        
        elif name.startswith('algo_'):
            algo_name = name[5:]
            self.selected_algorithm = algo_name
            for btn_name in self.buttons:
                if btn_name.startswith('algo_'):
                    is_selected = (btn_name == name)
                    self.buttons[btn_name].color = COLORS['GREEN'] if is_selected else COLORS['DARK_GRAY']
            self.show_message(f"Selected: {algo_name}")
        
        elif name == 'solve':
            self.solve()
        
        elif name == 'step':
            self.step_forward()
        
        elif name == 'auto_run':
            if self.solution_path:
                self.auto_running = not self.auto_running
                self.buttons['auto_run'].color = COLORS['ORANGE'] if self.auto_running else COLORS['PURPLE']
            else:
                self.show_message("Find path first!")
        
        elif name == 'stop':
            self.auto_running = False
            self.buttons['auto_run'].color = COLORS['PURPLE']
            self.show_message("Stopped.")
        
        elif name == 'speed_up':
            self.animation_speed = max(50, self.animation_speed - 50)
        
        elif name == 'speed_down':
            self.animation_speed = min(2000, self.animation_speed + 50)
    
    def handle_keyboard(self, key):
        """Xử lý phím bấm"""
        action = None
        
        if key == pygame.K_UP:
            action = Action.UP
        elif key == pygame.K_DOWN:
            action = Action.DOWN
        elif key == pygame.K_LEFT:
            action = Action.LEFT
        elif key == pygame.K_RIGHT:
            action = Action.RIGHT
        elif key == pygame.K_s:
            action = Action.SUCK
        elif key == pygame.K_r:
            self.world.random_dirt(0.3)
            self.regenerate_dirt_visuals()
        elif key == pygame.K_c:
            self.world.dirt_set.clear()
            self.dirt_positions.clear()
        elif key == pygame.K_SPACE:
            self.solve()
        elif key == pygame.K_RETURN:
            self.step_forward()
        elif key == pygame.K_a:
            self.auto_running = not self.auto_running
        
        if action:
            self.solution_path = []
            self.search_result = None
            
            completed = self.world.execute_action(action)
            
            if action == Action.SUCK and self.world.robot_pos not in self.world.dirt_set:
                if self.world.robot_pos in self.dirt_positions:
                    del self.dirt_positions[self.world.robot_pos]
            
            if completed:
                self.show_message("Complete! Environment is clean!")
    
    def handle_events(self):
        """Xử lý các sự kiện"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:
                self.window_width = max(event.w, 600)
                self.window_height = max(event.h, 500)
                self.screen = pygame.display.set_mode(
                    (self.window_width, self.window_height), pygame.RESIZABLE)
                self.update_button_positions()
            
            for name, button in self.buttons.items():
                if button.handle_event(event):
                    self.handle_button_click(name)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_end_x = self.grid_offset_x + self.world.grid_size * self.cell_size
                grid_end_y = self.grid_offset_y + self.world.grid_size * self.cell_size
                
                if (self.grid_offset_x <= event.pos[0] < grid_end_x and
                    self.grid_offset_y <= event.pos[1] < grid_end_y):
                    self.handle_grid_click(event.pos)
            
            if event.type == pygame.KEYDOWN:
                self.handle_keyboard(event.key)
        
        return True
    
    # ========================== SEARCH METHODS ==========================
    
    def _run_search_in_thread(self, algorithm_func: Callable, initial_state: State, grid_size: int):
        """Background thread to run search algorithm"""
        try:
            # Start progress tracking
            algo_name = self.selected_algorithm
            self.search_progress.start(algo_name)
            
            # Run algorithm with progress tracking
            result = algorithm_func(initial_state, grid_size, self.search_progress)
            self.pending_search_result = result
            
            # Stop progress tracking
            self.search_progress.stop()
        except Exception as e:
            print(f"Error in search: {e}")
            self.pending_search_result = SearchResult(
                path=[], nodes_expanded=0, time_taken=0,
                memory_used=0, success=False, algorithm_name="Error"
            )
            self.search_progress.stop()
        finally:
            self.is_searching = False
    
    def solve(self, algorithm_func: Callable = None):
        """Run search algorithm"""
        # Don't start new search if already searching
        if self.is_searching:
            self.show_message("Calculating...")
            return
        
        initial_state = self.world.get_state()
        
        if initial_state.is_goal():
            self.show_message("Environment is clean!")
            return
        
        if algorithm_func is None:
            algorithm_func = self.algorithms.get(self.selected_algorithm)
        
        if algorithm_func:
            # Show warning for risky combinations
            self._check_and_warn_algorithm()
            
            # Disable buttons during search
            self._set_buttons_enabled(False)
            
            # Start search in background thread
            self.is_searching = True
            self.pending_search_result = None
            self.search_thread = threading.Thread(
                target=self._run_search_in_thread,
                args=(algorithm_func, initial_state, self.world.grid_size),
                daemon=True
            )
            self.search_thread.start()
            self.show_message("Calculating path...")
    
    def step_forward(self):
        """Thực hiện một bước tiếp theo"""
        if self.solution_path and self.current_step < len(self.solution_path):
            action = self.solution_path[self.current_step]
            self.world.execute_action(action)
            self.current_step += 1
            
            if action == Action.SUCK:
                pos = self.world.robot_pos
                if pos in self.dirt_positions:
                    del self.dirt_positions[pos]
            
            if self.current_step >= len(self.solution_path):
                self.show_message("Complete!")
                self.auto_running = False
    
    def update(self):
        """Update state each frame"""
        # Check if search completed
        if self.pending_search_result is not None:
            self.search_result = self.pending_search_result
            self.pending_search_result = None
            self.algorithm_warning = None  # Clear warning after search completes
            
            # Re-enable buttons after search completes
            self._set_buttons_enabled(True)
            
            if self.search_result.success:
                self.solution_path = self.search_result.path
                self.current_step = 0
                # Pre-calculate robot positions on solution path for tree visualization
                # We need the initial state of the search, which is the current state
                state_path = self.world.get_state_path(self.solution_path)
                self.solution_states = state_path
                self.solution_positions = {s.robot_pos for s in state_path}
                self.show_message(f"Found path: {len(self.solution_path)} steps!")
            else:
                self.solution_path = []
                self.solution_states = []
                self.solution_positions = set()
                self.show_message("Path not found!")
        
        if self.auto_running and self.solution_path:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_step_time >= self.animation_speed:
                self.step_forward()
                self.last_step_time = current_time
    
    # ========================== MAIN LOOP ==========================
    
    def run(self):
        """Vòng lặp chính"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
    
    def _set_buttons_enabled(self, enabled: bool):
        """Enable or disable all buttons"""
        for button in self.buttons.values():
            button.enabled = enabled
    
    def _check_and_warn_algorithm(self):
        """Check if algorithm/board combination is risky and show warning"""
        grid_size = self.world.grid_size
        algo = self.selected_algorithm
        dirt_count = len(self.world.dirt_set)
        
        # Define risky combinations
        slow_algos = ["BFS", "DFS", "UCS"]
        
        self.algorithm_warning = None  # Clear previous warning
        
        if algo in slow_algos and grid_size >= 7:
            self.algorithm_warning = f"WARNING: {algo} may timeout on {grid_size}x{grid_size}! Consider Greedy NN."
        elif algo in slow_algos and grid_size == 6 and dirt_count > 8:
            self.algorithm_warning = f"WARNING: {algo} may be slow ({dirt_count} dirt). Try A* or Greedy NN."
        elif algo == "Greedy" and grid_size >= 7:
            self.algorithm_warning = f"WARNING: Greedy may timeout on {grid_size}x{grid_size}. Try Greedy NN."
    
    def set_algorithm(self, name: str, func: Callable):
        """Add or update algorithm"""
        self.algorithms[name] = func
        if name not in self.algorithm_names:
            self.algorithm_names.append(name)
            self.update_button_positions()
    
    def run_with_algorithm(self, algorithm_func: Callable):
        """Chạy tìm kiếm với thuật toán được truyền vào"""
        self.solve(algorithm_func)
        
    def draw_tree_diagram(self, x, y, width, height):
        """Draw a hierarchical tree diagram in the specified area"""
        if not self.search_result or not hasattr(self.search_result, 'search_tree'):
            return
            
        edges = self.search_result.search_tree
        if not edges:
            return
            
        # Group by levels for layout
        parents = {} # child -> parent
        
        # Build tree structure from edges
        # Start from initial state (level 0)
        # For visualization, we limit to first N nodes to keep it readable
        max_edges = min(len(edges), 1800)  # chú ý phần này
        visible_edges = edges[:max_edges]

        # Always keep edges that belong to the found path so late nodes stay visible
        if self.solution_positions:
            path_edges = [e for e in edges
                          if e[0] in self.solution_positions and e[2] in self.solution_positions]
            seen = set()
            merged = []
            for e in visible_edges + path_edges:
                if e not in seen:
                    merged.append(e)
                    seen.add(e)
            visible_edges = merged
        
        # Extract unique positions and their levels
        # Simplified: level is distance from root or just first encounter
        if not visible_edges:
            return
            
        root = visible_edges[0][0]

        # Build adjacency while preserving the discovery order
        children_map = defaultdict(list)
        for p, a, c in visible_edges:
            if c not in children_map[p]:
                children_map[p].append(c)

        # BFS to create tidy layers so siblings stay grouped under each parent
        levels = []  # list of lists
        queue = deque([(root, 0)])
        seen = {root}
        while queue:
            node, depth = queue.popleft()
            if len(levels) <= depth:
                levels.append([])
            levels[depth].append(node)
            for child in children_map.get(node, []):
                if child not in seen:
                    seen.add(child)
                    parents[child] = node
                    queue.append((child, depth + 1))
        
        # Calculate node positions
        node_coords = {}
        if not levels:
            return

        total_levels = len(levels)
        dy = height / max(total_levels, 1)
        min_spacing = 38  # Keep nodes separated for readability
        for depth, nodes in enumerate(levels):
            if not nodes:
                continue
            spacing = max(width / (len(nodes) + 1), min_spacing)
            used_width = spacing * (len(nodes) - 1)
            if used_width <= width:
                start_x = x + (width - used_width) / 2
            else:
                start_x = x + spacing  # fall back to left align with padding
            node_y = y + dy * depth
            for i, node in enumerate(nodes):
                node_coords[node] = (start_x + spacing * i, node_y)
                
        # Draw nodes
        for node, coord in node_coords.items():
            # Draw larger nodes for labels
            pygame.draw.circle(self.screen, COLORS['WHITE'], coord, 12)
            pygame.draw.circle(self.screen, COLORS['BLACK'], coord, 12, 1)
            
            # Draw (x,y) label with bold look
            label = self.font_small.render(f"{node[0]},{node[1]}", True, COLORS['BLACK'])
            label_rect = label.get_rect(center=(coord[0], coord[1]))
            self.screen.blit(label, label_rect)
            
        # Draw edges with actions
        for p, a, c in visible_edges:
            if p in node_coords and c in node_coords:
                # Highlight if on solution path
                is_on_path = False
                if self.solution_positions and c in self.solution_positions and p in self.solution_positions:
                     is_on_path = True
                
                # Check if this edge leads to the current robot position during playback
                is_current_step = False
                if self.solution_path and self.current_step > 0 and self.solution_states:
                    if self.current_step < len(self.solution_states):
                        curr_pos = self.solution_states[self.current_step].robot_pos
                        prev_pos = self.solution_states[self.current_step - 1].robot_pos
                        
                        if curr_pos == c and prev_pos == p:
                            is_current_step = True
                
                start_pos = node_coords[p]
                end_pos = node_coords[c]
                
                color = COLORS['RED'] if is_current_step else (COLORS['BLUE'] if is_on_path else COLORS['GRAY'])
                thickness = 4 if is_current_step else (2 if is_on_path else 1)
                pygame.draw.line(self.screen, color, start_pos, end_pos, thickness)
                
                # Draw action label on the middle of the edge
                mid_x = (start_pos[0] + end_pos[0]) // 2
                mid_y = (start_pos[1] + end_pos[1]) // 2
                
                action_text = a.name[0] if hasattr(a, 'name') else str(a)[0] # Get first letter of action
                action_label = self.font_small.render(action_text, True, color)
                # Offset slightly so it doesn't sit exactly on the line
                self.screen.blit(action_label, (mid_x + 6, mid_y - 12))

        # Re-draw active node in red if it exists
        if self.solution_path and self.current_step >= 0 and self.solution_states:
            if self.current_step < len(self.solution_states):
                current_pos = self.solution_states[self.current_step].robot_pos
                if current_pos in node_coords:
                    coord = node_coords[current_pos]
                    pygame.draw.circle(self.screen, COLORS['RED'], coord, 15, 3) # Red highlight ring

        
    def draw_search_tree(self):
        """Visualize the explored states on the grid"""
        if not self.show_search_viz or not self.search_result:
            return
            
        # Draw explored nodes (robot positions)
        if hasattr(self.search_result, 'explored_nodes') and self.search_result.explored_nodes:
            # We use a set to avoid drawing the same cell multiple times
            unique_nodes = set(self.search_result.explored_nodes)
            for x, y in unique_nodes:
                # Calculate center of the cell
                center_x = self.grid_offset_x + x * self.cell_size + self.cell_size // 2
                center_y = self.grid_offset_y + y * self.cell_size + self.cell_size // 2
                
                # Draw a small cyan dot for explored nodes
                # Pygame draw circle with slightly transparent look by using a small radius
                pygame.draw.circle(self.screen, (0, 206, 209), (center_x, center_y), self.cell_size // 8)
    def draw_progress_panel(self):
        """Draw live search progress in right panel"""
        # Panel position (right side of sidebar)
        sidebar_x = self.grid_offset_x + (self.world.grid_size * self.cell_size) + 15
        panel_x = sidebar_x + SIDEBAR_WIDTH + 10
        panel_y = TOP_BAR_HEIGHT + 20
        panel_width = 600
        panel_height = self.window_height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT - 40
        
        if panel_width < 150:
            return
        
        progress = self.search_progress.get_snapshot()
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (245, 245, 250), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['GRAY'], panel_rect, 2, border_radius=8)
        
        title_text = self.font_medium.render("SEARCH PROGRESS", True, COLORS['BLUE'])
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        y_offset = panel_y + 40
        
        if progress['is_active'] or self.is_searching:
            from app.algorithms.search_algorithms import MAX_NODES
            
            algo_text = self.font_small.render(f"Algorithm: {progress['algorithm_name']}", True, COLORS['BLACK'])
            self.screen.blit(algo_text, (panel_x + 10, y_offset))
            y_offset += 25
            
            status_text = self.font_small.render("Status: Searching...", True, COLORS['ORANGE'])
            self.screen.blit(status_text, (panel_x + 10, y_offset))
            y_offset += 35
            
            nodes_text = self.font_small.render(f"Nodes Explored: {progress['nodes_explored']:,}", True, COLORS['BLACK'])
            self.screen.blit(nodes_text, (panel_x + 10, y_offset))
            y_offset += 20
            
            frontier_text = self.font_small.render(f"Frontier Size: {progress['frontier_size']:,}", True, COLORS['BLACK'])
            self.screen.blit(frontier_text, (panel_x + 10, y_offset))
            y_offset += 20
            
            time_text = self.font_small.render(f"Time Elapsed: {progress['time_elapsed']:.2f}s", True, COLORS['BLACK'])
            self.screen.blit(time_text, (panel_x + 10, y_offset))
            y_offset += 35
            
            progress_ratio = min(1.0, progress['nodes_explored'] / MAX_NODES)
            bar_width = panel_width - 20
            bar_height = 20
            
            bar_rect = pygame.Rect(panel_x + 10, y_offset, bar_width, bar_height)
            pygame.draw.rect(self.screen, (220, 220, 220), bar_rect, border_radius=4)
            
            filled_width = int(bar_width * progress_ratio)
            if filled_width > 0:
                filled_rect = pygame.Rect(panel_x + 10, y_offset, filled_width, bar_height)
                color = COLORS['GREEN'] if progress_ratio < 0.8 else COLORS['ORANGE']
                pygame.draw.rect(self.screen, color, filled_rect, border_radius=4)
            
            pygame.draw.rect(self.screen, COLORS['GRAY'], bar_rect, 1, border_radius=4)
            
            percent_text = self.font_small.render(f"{int(progress_ratio * 100)}%", True, COLORS['BLACK'])
            self.screen.blit(percent_text, (panel_x + 10, y_offset + 25))
            y_offset += 60
            
            # --- Search Tree Diagram Section ---
            pygame.draw.line(self.screen, COLORS['GRAY'], (panel_x + 10, y_offset), (panel_x + panel_width - 10, y_offset))
            y_offset += 15
            
            tree_title = self.font_medium.render("SEARCH TREE", True, COLORS['BLUE'])
            self.screen.blit(tree_title, (panel_x + 10, y_offset))
            y_offset += 30
            
            # Draw empty tree placeholders while searching
            searching_text = self.font_small.render("Building tree...", True, COLORS['DARK_GRAY'])
            self.screen.blit(searching_text, (panel_x + 10, y_offset))
            
        elif self.search_result:
            # Show completed stats
            algo_text = self.font_small.render(f"Algorithm: {self.search_result.algorithm_name}", True, COLORS['BLACK'])
            self.screen.blit(algo_text, (panel_x + 10, y_offset))
            y_offset += 25
            
            status_text = self.font_small.render(f"Status: {'Success' if self.search_result.success else 'Failed'}", 
                                               True, COLORS['GREEN'] if self.search_result.success else COLORS['RED'])
            self.screen.blit(status_text, (panel_x + 10, y_offset))
            y_offset += 35
            
            nodes_text = self.font_small.render(f"Nodes Explored: {self.search_result.nodes_expanded:,}", True, COLORS['BLACK'])
            self.screen.blit(nodes_text, (panel_x + 10, y_offset))
            y_offset += 20
            
            time_text = self.font_small.render(f"Time Taken: {self.search_result.time_taken:.3f}s", True, COLORS['BLACK'])
            self.screen.blit(time_text, (panel_x + 10, y_offset))
            y_offset += 50
            
            # --- Search Tree Diagram ---
            pygame.draw.line(self.screen, COLORS['GRAY'], (panel_x + 10, y_offset), (panel_x + panel_width - 10, y_offset))
            y_offset += 15
            
            tree_title = self.font_medium.render("SEARCH TREE", True, COLORS['BLUE'])
            self.screen.blit(tree_title, (panel_x + 10, y_offset))
            y_offset += 30
            
            # Draw the tree diagram
            self.draw_tree_diagram(panel_x + 10, y_offset, panel_width - 20, panel_height - (y_offset - panel_y) - 10)
            
        else:
            idle_text = self.font_small.render("No search running", True, COLORS['DARK_GRAY'])
            self.screen.blit(idle_text, (panel_x + 10, y_offset))
            y_offset += 25
            
            help_text = self.font_small.render("Click 'Find Path' to start", True, COLORS['DARK_GRAY'])
            self.screen.blit(help_text, (panel_x + 10, y_offset))
