# Báo cáo Phân tích Bài tập Thực hành: Kiểm tra Quá tải theo Người (practices3)

## Trạng thái Nghiệm thu Tổng thể
- **Không vi phạm các ràng buộc**: Không thêm tool mới, không sửa `agent.py`, không hardcode ngưỡng hoặc kết quả mẫu trong mã nguồn hay skill.
- **Dữ liệu chuẩn bị**: `workspace/data/workload.csv` đã có ở cả Stage 03 và Stage 04; file `workload-edge.csv` đã được tạo để kiểm tra edge case.
- **Stage 03**: Sử dụng Python qua công cụ Bash để tính tổng giờ theo từng người, loại trừ lỗi và loại trừ trùng lặp ID, bảo toàn file CSV gốc.
- **Stage 04**: Mở rộng script `check_csv.py` với tham số bắt buộc `--max-hours`, cập nhật `SKILL.md` và `references/report-template.md`, đồng bộ đầy đủ sang `fixtures/`.
- **Kiểm thử tự động**: Viết kiểm thử tự động mở rộng trong `tests/test_check_csv.py` với **25/25 test cases passed 100%**.
- **Đầu ra báo cáo**: Đã tạo các báo cáo mẫu `output/workload.md` (ngưỡng 8) và `output/workload-9.md` (ngưỡng 9).

---

## 1. Yêu cầu của Đề bài & Hợp đồng Kỹ thuật

1. **Stage 03**:
   - Dùng Python thông qua tool Bash để tính tổng `hours` theo `owner` trong `data/workload.csv`.
   - Không được sửa file dữ liệu gốc.
   - Giải thích rõ cơ chế xử lý dòng dữ liệu lỗi và công việc bị trùng `task_id`.
2. **Stage 04**:
   - Mở rộng script `check_csv.py` với tham số bắt buộc `--max-hours` (số hữu hạn, không âm). Nếu thiếu hoặc sai, in lỗi ra `stderr` và trả exit code khác 0.
   - Thuật toán tính toán:
     - Giữ nguyên toàn bộ thống kê chất lượng cũ (`row_count`, `issues`,...).
     - Chuẩn hóa: strip khoảng trắng ở các cột. Giữ nguyên tính phân biệt hoa/thường của `owner` (ví dụ `Lan` khác `lan`).
     - **Quy tắc bảo lưu ID lần đầu**: Mỗi `task_id` không rỗng chỉ giữ lần xuất hiện đầu tiên trong file. Các lần xuất hiện sau đều bị loại (`duplicate_id`), kể cả khi lần đầu chứa dữ liệu lỗi và lần sau có dữ liệu hợp lệ.
     - **Điều kiện tính giờ**: Chỉ cộng dòng có đủ số cột, ID không rỗng, owner không rỗng, hours là số hữu hạn không âm (số `0` hợp lệ).
     - Gom tất cả lý do loại vào mảng `excluded_rows` theo thứ tự chuẩn hóa: `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.
     - **Quá tải**: Chỉ quá tải khi tổng giờ **lớn hơn strictly** (`>`) ngưỡng; bằng ngưỡng (`==`) không bị tính là quá tải.
   - Cập nhật `SKILL.md`: Nếu người dùng không cung cấp ngưỡng, Agent bắt buộc phải hỏi lại thay vì tự đoán hay lấy ngưỡng từ lịch sử hội thoại trước.
   - Cập nhật `references/report-template.md`: Bổ sung cấu trúc hiển thị ngưỡng, tổng giờ theo người, danh sách người quá tải, các dòng bị loại kèm lý do.
   - Đồng bộ sang thư mục `fixtures/` để bảo toàn sau khi reset workspace.

---

## 2. Chi tiết các Thay đổi đã Thực hiện

### 2.1. Chuẩn bị Dữ liệu (`data/workload.csv` và `data/workload-edge.csv`)
Tạo file `workspace/data/workload.csv` tại cả Stage 03 và Stage 04:
```csv
task_id,owner,hours
T01,Lan,4
T02,Lan,5
T03,Minh,3
T04,Minh,abc
T02,Lan,5
T05,,2
```
Tạo file `workspace/data/workload-edge.csv` tại Stage 04 để kiểm thử trường hợp đặc biệt:
```csv
task_id,owner,hours
E01,Lan,abc
E01,Lan,5
E02,Minh,0
```

### 2.2. Mở rộng Script `check_csv.py`
- **Tham số CLI**: Dùng `argparse` khai báo `--max-hours` là `required=True`. Hàm `parse_hours` kiểm tra giá trị: phải là float, không rỗng, hữu hạn (`math.isfinite`), và `>= 0`. Nếu sai, in lỗi ra `stderr` và trả `exit code 1` (hoặc `exit code 2` nếu thiếu flag).
- **Hỗ trợ UTF-8 console Windows**: Tự động reconfigure `sys.stdout` và `sys.stderr` sang UTF-8 để không bị lỗi mã hóa tiếng Việt trên Windows.
- **Bảo lưu ID ngay lần đầu**: Dùng từ điển `first_seen[task_id] = line` ngay khi duyệt đến `task_id` lần đầu tiên, trước khi xét tính hợp lệ của `hours` hay `owner`. Nếu gặp lại `task_id` ở các dòng sau, lập tức gán lý do `duplicate_id`.
- **Gom lý do & lọc dòng loại**: Mỗi dòng được thu thập toàn bộ lý do không hợp lệ vào `row_reasons`.
  - Nếu `row_reasons` rỗng: cộng vào `hours_by_owner[owner]`.
  - Nếu `row_reasons` có phần tử: sắp xếp theo thứ tự `REASON_ORDER` và đưa vào danh sách `excluded_rows`.
- **Đầu ra JSON**: Luôn chứa `max_hours`, `hours_by_owner`, `overloaded_owners` (chỉ gồm người có `total_hours > max_hours`, sắp xếp theo tên), và `excluded_rows`.

### 2.3. Cập nhật `SKILL.md`
- Hướng dẫn Agent phân tích yêu cầu: nếu người dùng yêu cầu kiểm tra quá tải mà **chưa cung cấp ngưỡng**, Agent phải dừng lại hỏi người dùng trước khi thực thi lệnh.
- Khi người dùng cung cấp ngưỡng, Agent truyền nguyên vẹn vào tham số `--max-hours` trong lệnh Bash.
- Quy định rõ ràng cấu trúc các trường mới trong JSON để Agent hiểu và diễn giải đúng kết quả.

### 2.4. Cập nhật `references/report-template.md`
- Bổ sung bảng Tổng giờ theo người (`hours_by_owner`), cột đánh giá Quá tải, mục Người quá tải, và bảng Dòng bị loại (`excluded_rows`) có đầy đủ mã lý do và diễn giải.

### 2.5. Đồng bộ vào Fixtures
Đã sao chép toàn bộ thư mục `workspace/skills/csv-quality/` sang `fixtures/skills/csv-quality/` và các file CSV sang `fixtures/data/` để đảm bảo hệ thống duy trì đầy đủ tính năng sau các lệnh reset workspace.

---

## 3. Thực thi & Giải thích Chi tiết Stage 03

### 3.1. Phân tích Dòng dữ liệu trong `data/workload.csv`
Tập dữ liệu gồm 6 dòng (không tính header):
1. Dòng 2 (`T01,Lan,4`): Hợp lệ -> **Cộng 4 giờ cho Lan**.
2. Dòng 3 (`T02,Lan,5`): Hợp lệ, `T02` xuất hiện lần đầu -> **Cộng 5 giờ cho Lan**.
3. Dòng 4 (`T03,Minh,3`): Hợp lệ -> **Cộng 3 giờ cho Minh**.
4. Dòng 5 (`T04,Minh,abc`): `hours` là `abc` không phải số -> **Loại** (`invalid_hours`).
5. Dòng 6 (`T02,Lan,5`): `T02` đã xuất hiện ở dòng 3 -> **Loại** (`duplicate_id`).
6. Dòng 7 (`T05,,2`): `owner` bị để trống -> **Loại** (`missing_owner`).

### 3.2. Kết quả tính toán
- **Lan**: 4 + 5 = **9 giờ**.
- **Minh**: **3 giờ**.
- **Tại sao Lan thành 14 giờ nếu không loại trùng?**: Nếu thuật toán không kiểm tra trùng lặp `task_id`, dòng 6 (`T02,Lan,5`) sẽ tiếp tục bị cộng vào tổng của Lan (4 + 5 + 5 = 14 giờ). Điều này sai thực tế vì công việc `T02` bị ghi nhận 2 lần.
- **Đoạn mã Python qua Bash loại trùng**:
```python
import csv, sys

seen_ids = set()
totals = {}

with open('data/workload.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) # bỏ qua header
    for row in reader:
        if not row or not any(row): continue
        tid, owner, hours = [c.strip() for c in row]
        # Xử lý trùng lặp và lỗi
        if tid in seen_ids:
            continue # Loại dòng trùng ID
        seen_ids.add(tid) # Giữ chỗ ID ngay lần xuất hiện đầu tiên
        
        try:
            val = float(hours)
            if val < 0 or not owner: continue
            totals[owner] = totals.get(owner, 0.0) + val
        except ValueError:
            continue

print(totals) # Kết quả: {'Lan': 9.0, 'Minh': 3.0}
```

---

## 4. Kết quả Chạy Script Trực tiếp (Stage 04)

### Trường hợp 1: Ngưỡng 8 (`--max-hours 8`)
- **Lệnh**: `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8`
- **Exit code**: `0`
- **Kết quả JSON**:
  - `hours_by_owner`: `{"Lan": 9.0, "Minh": 3.0}`
  - `overloaded_owners`: `[{"owner": "Lan", "total_hours": 9.0}]` (chỉ Lan quá tải vì 9.0 > 8.0)
  - `excluded_rows`:
    - Line 5 (`T04`): `["invalid_hours"]`
    - Line 6 (`T02`): `["duplicate_id"]`
    - Line 7 (`T05`): `["missing_owner"]`

### Trường hợp 2: Ngưỡng 9 (`--max-hours 9`)
- **Lệnh**: `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 9`
- **Exit code**: `0`
- **Kết quả JSON**:
  - `hours_by_owner`: `{"Lan": 9.0, "Minh": 3.0}`
  - `overloaded_owners`: `[]` (Không ai quá tải vì 9.0 không lớn hơn 9.0; bằng ngưỡng không phải quá tải)
  - `excluded_rows`: Giữ nguyên như trên.

### Trường hợp 3: Trường hợp đặc biệt (Edge Case: `workload-edge.csv`, ngưỡng 0)
- **Dữ liệu**:
  ```csv
  task_id,owner,hours
  E01,Lan,abc
  E01,Lan,5
  E02,Minh,0
  ```
- **Lệnh**: `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload-edge.csv --max-hours 0`
- **Exit code**: `0`
- **Kết quả JSON**:
  - `hours_by_owner`: `{"Minh": 0.0}`
  - `overloaded_owners`: `[]` (Minh có 0h, bằng ngưỡng 0h nên không quá tải)
  - `excluded_rows`:
    - Line 2 (`E01`): `["invalid_hours"]` (lần đầu xuất hiện của `E01` bị lỗi hours)
    - Line 3 (`E01`): `["duplicate_id"]` (lần 2 của `E01` bị loại do trùng ID, dù có hours=5 hợp lệ thì cũng không được cộng vào cho Lan)

### Trường hợp 4: Thiếu tham số `--max-hours` hoặc giá trị sai
- **Lệnh**: `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv`
- **Exit code**: `2` (theo chuẩn argparse khi thiếu cờ bắt buộc)
- **Stderr**: `ERROR: the following arguments are required: --max-hours`

### Trường hợp 5: File không tồn tại
- **Lệnh**: `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input data/khong-ton-tai.csv --max-hours 8`
- **Exit code**: `1`
- **Stderr**: `ERROR: Không đọc được file data/khong-ton-tai.csv: No such file or directory`

---

## 5. Kết quả Kiểm thử Tự động (`pytest`)

File kiểm thử [tests/test_check_csv.py] bao phủ toàn diện 25 ca kiểm thử:
1. `test_fixture_statistics`: Kiểm tra tính toàn vẹn của fixture ban đầu `tasks.csv`.
2. `test_non_finite_negative_or_empty_hours_rejected`: Từ chối NaN, inf, số âm, chuỗi rỗng.
3. `test_clean_data_exit_0_without_issues`: Dữ liệu sạch trả exit 0 và không có issues.
4. `test_missing_file_exit_1`: File không tồn tại trả exit 1.
5. `test_missing_column_exit_1`: Thiếu cột bắt buộc trả exit 1.
6. `test_parse_error_exit_1`: Lỗi parse CSV trả exit 1.
7. `test_script_does_not_modify_input`: Đảm bảo script tuyệt đối không sửa đổi file nguồn.
8. `test_workload_and_strict_threshold`: Kiểm thử ngưỡng 8 (Lan quá tải) và ngưỡng 9 (không ai quá tải).
9. `test_first_invalid_occurrence_still_reserves_id`: Kiểm thử ca đặc biệt (ID đầu lỗi vẫn giữ chỗ, lần 2 bị loại trùng, không cộng giờ).
10. `test_missing_or_invalid_threshold_fails`: Kiểm tra từ chối khi thiếu ngưỡng hoặc ngưỡng âm, NaN, chuỗi.
11. `test_normalization_all_reasons_and_quality_on_excluded_rows`: Kiểm tra trim khoảng trắng, phân biệt hoa thường (`Lan` vs `lan`), gom tất cả mã lý do trên 1 dòng.
12. `test_missing_id_is_null_and_retains_all_reasons`: task_id rỗng chuyển thành `null` trong JSON và giữ đầy đủ các lỗi khác.
13. `test_invalid_encoding_fails`: File không đúng chuẩn UTF-8 báo lỗi rõ ràng.

**Kết quả chạy**:
```bash
uv run pytest tests/test_check_csv.py
============================= 25 passed in 2.23s ==============================
```

---

## 6. Trả lời Câu hỏi Cuối bài

### Câu hỏi 1: Phần nào do script tính, phần nào do model diễn giải?
- **Phần do Script tính toán (Deterministic Logic)**:
  - Đọc, parse và validate cú pháp CSV;
  - Nhận diện các lỗi chất lượng dữ liệu (thiếu cột, sai số trường, task_id trùng, thiếu owner, hours không hợp lệ);
  - Thực thi quy tắc nghiệp vụ cốt lõi: bảo lưu ID ở lần gặp đầu tiên, loại trừ các dòng lỗi, cộng dồn tổng giờ của từng người theo các dòng hợp lệ;
  - So sánh toán học giữa tổng giờ và ngưỡng `--max-hours` để kết luận danh sách `overloaded_owners`.
  - Toàn bộ kết quả này là số liệu chính xác 100%, có thể kiểm chứng độc lập bằng code.
- **Phần do Model diễn giải (Agentic & Reasoning Role)**:
  - Hiểu ý định của người dùng từ ngôn ngữ tự nhiên (xác định người dùng muốn kiểm tra file nào, ngưỡng bao nhiêu);
  - Chọn đúng công cụ/skill (`csv-quality`) để sử dụng;
  - Phát hiện thông tin còn thiếu (nếu người dùng chưa cung cấp ngưỡng) để chủ động đặt câu hỏi làm rõ thay vì chạy bừa;
  - Soạn thảo và thực thi câu lệnh Bash tương ứng với tham số chính xác;
  - Đọc kết quả JSON trả về từ stdout và đọc template từ reference;
  - Diễn đạt kết quả thành báo cáo Markdown hoàn chỉnh, giải thích nguyên nhân tại sao một dòng bị loại và đưa ra khuyến nghị thực tế cho người dùng mà không làm biến dạng dữ liệu.

### Câu hỏi 2: Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?
1. **Agent gọi sai lệnh CLI**: Script mới bắt buộc phải có cờ `--max-hours <ngưỡng>`. Nếu không cập nhật `SKILL.md`, Agent sẽ tiếp tục chạy lệnh cũ `python check_csv.py --input ...` mà không có `--max-hours`, dẫn đến script bị dừng với exit code khác 0 (`ERROR: the following arguments are required: --max-hours`).
2. **Agent tự bịa hoặc tái sử dụng ngưỡng cũ**: Nếu người dùng không đưa ngưỡng, Agent không biết quy tắc phải hỏi lại người dùng, có thể tự lấy ngưỡng mặc định (ví dụ số 8) từ trí nhớ quá khứ hoặc tự đoán mò, dẫn đến vi phạm quy định nghiệp vụ.
3. **Hiểu sai định nghĩa quá tải**: Agent có thể tự suy luận quá tải là `>=` thay vì `>` dẫn đến khi tổng giờ bằng ngưỡng (ví dụ 9 giờ với ngưỡng 9) Agent kết luận nhầm là bị quá tải.
4. **Báo cáo thiếu toàn bộ thông tin mới**: Reference template cũ chỉ có bảng lỗi chất lượng; nếu không cập nhật template, báo cáo tạo ra sẽ hoàn toàn thiếu:
   - Bảng tổng giờ được chấp nhận theo từng người;
   - Đánh giá ai là người bị quá tải;
   - Bảng danh sách các dòng bị loại khỏi tổng giờ và lý do tương ứng.
5. **Nhầm lẫn giữa lỗi dữ liệu và lỗi thực thi**: Agent có thể không biết cách xử lý khi script trả về các mã lỗi khác nhau hoặc diễn giải sai các mã lý do trong `excluded_rows`.
