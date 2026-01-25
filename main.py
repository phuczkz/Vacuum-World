"""
Entry point chính để chạy ứng dụng Vacuum World

Chạy: python main.py
"""

import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import VacuumWorldGUI


def main():
    """Hàm chính để chạy ứng dụng"""
    print("=" * 60)
    print("VACUUM WORLD - Robot Hút Bụi")
    print("=" * 60)
    print("\nHướng dẫn:")
    print("  - Click chuột vào ô để thêm/xóa bụi")
    print("  - Phím mũi tên: Di chuyển robot")
    print("  - Phím S: Hút bụi")
    print("  - Phím R: Random bụi")
    print("  - Phím C: Xóa tất cả bụi")
    print("  - Phím Space: Tìm đường")
    print("  - Phím Enter: Bước tiếp")
    print("  - Phím A: Bật/tắt tự động")
    print("\nĐang khởi động giao diện...")
    
    # Ví dụ thêm thuật toán tùy chỉnh:
    # from app import State, SearchResult
    # 
    # def my_search(state: State, grid_size: int) -> SearchResult:
    #     return SearchResult([], 0, 0, 0, False, "MySearch")
    # 
    # app = VacuumWorldGUI(custom_algorithms={"MySearch": my_search})
    
    app = VacuumWorldGUI()
    app.run()


if __name__ == "__main__":
    main()
