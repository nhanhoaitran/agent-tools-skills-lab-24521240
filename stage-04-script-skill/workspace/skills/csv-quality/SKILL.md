---
name: csv-quality
description: Kiểm tra chất lượng CSV công việc (task_id, owner, hours), tính tổng giờ theo người và xác định người quá tải bằng script có sẵn. Dùng khi rà soát CSV công việc, tổng giờ hoặc người vượt ngưỡng.
---

# CSV quality

## Đầu vào và thực thi

Xác định đường dẫn CSV và ngưỡng hữu hạn không âm từ yêu cầu hiện tại. Script bắt buộc có `--max-hours`. Nếu chưa có ngưỡng, hỏi người dùng trước khi chạy hoặc kết luận quá tải. Không đặt ngưỡng mặc định, không dùng ngưỡng từ cuộc trò chuyện cũ. Truyền chính xác giá trị được cung cấp.

Dùng tool `bash`, cwd là workspace; quote các tham số:

```bash
python skills/csv-quality/scripts/check_csv.py --input '<đường dẫn CSV>' --max-hours '<ngưỡng>'
```

Không cần đọc source script để sử dụng. Script chỉ đọc CSV.

- `ok=true`, không timeout, `exit_code=0`: đọc JSON từ stdout. Lỗi chất lượng hoặc người quá tải vẫn là phân tích thành công.
- Exit khác 0: đọc stderr, báo không phân tích được; không đưa tổng giờ hay ghi báo cáo thành công. Thiếu CLI bắt buộc trả exit 2; ngưỡng không hợp lệ hoặc lỗi đầu vào trả exit 1.
- `ok=false`, timeout hoặc output bị cắt: báo lỗi hoặc kết quả không đầy đủ, không suy đoán thống kê.

## Diễn giải JSON

Giữ các trường `input`, `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`. Thống kê chất lượng xét mọi dòng dữ liệu không trống, kể cả dòng bị loại khỏi tổng.

| Trường bổ sung luôn có | Ý nghĩa |
|---|---|
| `max_hours` | Ngưỡng từ CLI. |
| `hours_by_owner` | Tên → tổng giờ; chỉ người có ít nhất một dòng được cộng, kể cả tổng 0. |
| `overloaded_owners` | Danh sách `{owner, total_hours}` có tổng **lớn hơn** ngưỡng, sắp theo tên. Bằng ngưỡng không quá tải. |
| `excluded_rows` | Danh sách `{line, task_id, reasons}`, sắp theo dòng; ID rỗng là `null`; mỗi dòng một lần với tất cả lý do. |

Trim `task_id`, `owner`, `hours`; giữ riêng tên khác hoa/thường. Mỗi ID không rỗng chỉ giữ lần xuất hiện đầu tiên trong file, kể cả lần đó lỗi. Chỉ cộng dòng đúng số trường, có ID và owner, hours hữu hạn không âm; 0 hợp lệ. Bỏ qua dòng trống. Thứ tự mã lý do: `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.

## Báo cáo

Đọc [mẫu báo cáo](references/report-template.md) bằng `read_file` tại `skills/csv-quality/references/report-template.md` khi viết báo cáo. Lấy mọi số liệu từ JSON thành công, ghi ngưỡng, tổng theo người, người quá tải, tất cả dòng bị loại và chi tiết chất lượng. Phân biệt tổng của các dòng được chấp nhận với tổng thực tế đầy đủ chưa xác minh nếu còn dòng lỗi. Không sửa CSV nguồn.

Ghi bằng `write_file` vào đường dẫn được yêu cầu, mặc định `output/workload.md`; trả đường dẫn và tóm tắt kết quả.
