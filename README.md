# Vacuum World - Robot Hút Bụi

## Mô tả

Đồ án mô phỏng robot hút bụi trong môi trường dạng lưới n × n. Dự án bao gồm:

- Đặc tả bài toán theo mô hình PEAS
- Định nghĩa bài toán tìm kiếm
- Transition Function
- Cây tìm kiếm
- Hiện thực các giải thuật tìm kiếm
- Giao diện đồ họa

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

### Cách 1: Chạy từ file main.py

```bash
python main.py
```

### Cách 2: Nếu lệnh `python` không hoạt động

**Windows:**
```bash
py main.py
```

**macOS / Linux:**
```bash
python3 main.py
```

### Cách 3: Chạy từ VS Code

1. Mở folder `vaccumsucksuck` trong VS Code
2. Mở file `main.py`
3. Nhấn **F5** hoặc **Ctrl+F5**

## Hướng dẫn sử dụng

### Điều khiển bằng chuột
- **Click vào ô**: Thêm/xóa bụi tại vị trí đó
- **Nút "Đặt Robot"**: Sau đó click vào ô để đặt robot
- **Nút +/-**: Thay đổi kích thước lưới (2x2 đến 10x10)

### Điều khiển bằng bàn phím
- **Phím mũi tên**: Di chuyển robot
- **Phím S**: Hút bụi tại vị trí hiện tại
- **Phím R**: Random phân bố bụi
- **Phím C**: Xóa tất cả bụi
- **Phím Space**: Chạy thuật toán tìm đường

### Các thuật toán tìm kiếm

**Uninformed Search:**
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- UCS (Uniform Cost Search)

**Informed Search:**
- Greedy Best-First Search
- A* Search

### Tính năng
- Thay đổi kích thước môi trường n×n
- Tùy chỉnh vị trí ban đầu của robot
- Random hoặc tự đặt phân bố bụi
- Hiển thị đường đi của robot
- Chạy từng bước hoặc tự động
- Điều chỉnh tốc độ animation
- So sánh kết quả các thuật toán (số nodes mở rộng, thời gian, bộ nhớ)



## Cấu trúc thư mục

```
vaccumsucksuck/
├── app/
│   └── vacuum_world_gui.py    # Giao diện đồ họa chính
├── misc/
│   ├── 1. Đặc tả bài toán...   # PEAS
│   ├── 2. Định nghĩa bài toán...
│   ├── 3. Transition Function
│   └── Search_Tree.ipynb
├── data/
├── script/
├── requirements.txt
└── README.md
```

