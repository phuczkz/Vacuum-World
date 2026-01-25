"""
Giao diện đồ họa chính cho Vacuum World
"""

import pygame
import random
from typing import List, Optional, Callable, Dict, Tuple

from app.models import Action, State, SearchResult
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
        
        # Lưu vị trí bụi cố định để vẽ
        self.dirt_positions: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
        
        # Message
        self.message = ""
        self.message_time = 0
        
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
        
        self.window_width = grid_area + SIDEBAR_WIDTH + 40
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
        
        # Điều khiển môi trường
        env_buttons = [
            ('random_dirt', "Random Bụi", COLORS['BROWN']),
            ('clear_dirt', "Xóa Bụi", COLORS['DARK_GRAY']),
            ('place_robot', "Đặt Robot", COLORS['BLUE']),
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
        
        # Điều khiển chạy
        run_buttons = [
            ('solve', "Tìm Đường", COLORS['GREEN']),
            ('step', "Bước Tiếp", COLORS['BLUE']),
            ('auto_run', "Tự Động", COLORS['PURPLE']),
            ('stop', "Dừng", COLORS['RED']),
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
    
    def draw_robot(self):
        """Vẽ robot hút bụi"""
        rx, ry = self.world.robot_pos
        center_x = self.grid_offset_x + rx * self.cell_size + self.cell_size // 2
        center_y = self.grid_offset_y + ry * self.cell_size + self.cell_size // 2
        
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
        
        title = self.font_large.render("VACUUM WORLD - Robot Hút Bụi", True, COLORS['BLUE'])
        self.screen.blit(title, (self.grid_offset_x, 12))
        
        if self.placing_robot:
            hint = self.font_medium.render("Click vào ô để đặt robot", True, COLORS['RED'])
        else:
            hint = self.font_small.render(
                "Click: Bật/tắt bụi | Phím mũi tên: Di chuyển | S: Hút | Space: Tìm đường", 
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
        
        # Dòng 1: Trạng thái
        if info_width < 280:
            status_text = f"({self.world.robot_pos[0]},{self.world.robot_pos[1]}) | Bụi:{len(self.world.dirt_set)} | B:{self.world.total_cost}"
        else:
            status_text = f"Robot: {self.world.robot_pos} | Bụi: {len(self.world.dirt_set)} | Bước: {self.world.total_cost} | Algo: {self.selected_algorithm}"
        text = self.font_small.render(status_text, True, COLORS['BLACK'])
        self.screen.blit(text, (self.grid_offset_x + 5, bottom_y))
        
        # Dòng 2: Kết quả tìm kiếm
        if self.search_result:
            result_y = bottom_y + 18
            if self.search_result.success:
                if info_width < 280:
                    result_text = f"{len(self.search_result.path)}b | N:{self.search_result.nodes_expanded} | {self.search_result.time_taken*1000:.0f}ms"
                else:
                    result_text = (f"Tìm thấy: {len(self.search_result.path)} bước | "
                                 f"Nodes: {self.search_result.nodes_expanded} | "
                                 f"Time: {self.search_result.time_taken*1000:.1f}ms")
                color = COLORS['GREEN']
            else:
                result_text = "Không tìm thấy!" if info_width < 280 else "Không tìm thấy đường đi!"
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
        """Vẽ toàn bộ giao diện"""
        self.screen.fill(COLORS['WHITE'])
        
        self.draw_top_bar()
        self.draw_grid()
        self.draw_path()
        self.draw_dirt()
        self.draw_robot()
        self.draw_sidebar()
        self.draw_bottom_bar()
        
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
                self.show_message(f"Đã đặt robot tại ({x}, {y})")
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
                self.show_message(f"Lưới: {self.world.grid_size}x{self.world.grid_size}")
        
        elif name == 'size_down':
            if self.world.grid_size > MIN_GRID_SIZE:
                self.world.set_grid_size(self.world.grid_size - 1)
                self.resize_window()
                self.show_message(f"Lưới: {self.world.grid_size}x{self.world.grid_size}")
        
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
            self.show_message("Đã reset!")
        
        elif name.startswith('algo_'):
            algo_name = name[5:]
            self.selected_algorithm = algo_name
            for btn_name in self.buttons:
                if btn_name.startswith('algo_'):
                    is_selected = (btn_name == name)
                    self.buttons[btn_name].color = COLORS['GREEN'] if is_selected else COLORS['DARK_GRAY']
            self.show_message(f"Đã chọn: {algo_name}")
        
        elif name == 'solve':
            self.solve()
        
        elif name == 'step':
            self.step_forward()
        
        elif name == 'auto_run':
            if self.solution_path:
                self.auto_running = not self.auto_running
                self.buttons['auto_run'].color = COLORS['ORANGE'] if self.auto_running else COLORS['PURPLE']
            else:
                self.show_message("Hãy tìm đường trước!")
        
        elif name == 'stop':
            self.auto_running = False
            self.buttons['auto_run'].color = COLORS['PURPLE']
        
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
                self.show_message("Hoàn thành! Môi trường đã sạch!")
    
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
    
    def solve(self, algorithm_func: Callable = None):
        """Chạy giải thuật tìm kiếm"""
        initial_state = self.world.get_state()
        
        if initial_state.is_goal():
            self.show_message("Môi trường đã sạch!")
            return
        
        if algorithm_func is None:
            algorithm_func = self.algorithms.get(self.selected_algorithm)
        
        if algorithm_func:
            self.search_result = algorithm_func(initial_state, self.world.grid_size)
            
            if self.search_result.success:
                self.solution_path = self.search_result.path
                self.current_step = 0
                self.show_message(f"Tìm thấy đường đi: {len(self.solution_path)} bước!")
            else:
                self.solution_path = []
                self.show_message("Không tìm thấy đường đi!")
    
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
                self.show_message("Hoàn thành!")
                self.auto_running = False
    
    def update(self):
        """Cập nhật trạng thái mỗi frame"""
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
    
    def set_algorithm(self, name: str, func: Callable):
        """Thêm hoặc cập nhật thuật toán"""
        self.algorithms[name] = func
        if name not in self.algorithm_names:
            self.algorithm_names.append(name)
            self.update_button_positions()
    
    def run_with_algorithm(self, algorithm_func: Callable):
        """Chạy tìm kiếm với thuật toán được truyền vào"""
        self.solve(algorithm_func)
