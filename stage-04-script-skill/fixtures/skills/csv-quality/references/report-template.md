# Báo cáo chất lượng và tải công việc: `{input}`

Công cụ: `skills/csv-quality/scripts/check_csv.py`. Exit code: {exit_code}.
Ngưỡng: **{max_hours} giờ**. Quá tải khi tổng giờ **> ngưỡng**, bằng ngưỡng không quá tải.

## Tổng quan chất lượng

| Chỉ số | Giá trị |
|---|---|
| Dòng dữ liệu không trống (không tính header) | {row_count} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| ID bị lặp, đếm ID phân biệt | {duplicate_id_count}: {duplicate_ids} |

## Tổng giờ theo người

| Người | Tổng giờ được chấp nhận | Quá tải? |
|---|---|---|
| {owner} | {total_hours} | {Có/Không, theo overloaded_owners} |

Chỉ liệt kê owner trong hours_by_owner, kể cả tổng bằng 0.

## Người quá tải

{Danh sách từ overloaded_owners hoặc “Không ai quá tải.”}

## Dòng bị loại khỏi tổng giờ

| Dòng | task_id | Tất cả mã lý do | Giải thích |
|---|---|---|---|
| {line} | {task_id hoặc null} | {reasons} | {Diễn giải mã lý do} |

Header là dòng 1. Mỗi dòng bị loại ghi một lần theo thứ tự dòng. Lý do theo thứ tự wrong_field_count, missing_task_id, duplicate_id, missing_owner, invalid_hours. Nếu rỗng ghi “Không có dòng bị loại.”

## Chi tiết lỗi chất lượng

| Dòng | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message từ issues} |

## Đánh giá và khuyến nghị

- Tổng giờ chỉ tính dòng hợp lệ được chấp nhận; không khẳng định tổng thực tế đầy đủ khi còn dòng lỗi.
- ID được trim, chỉ giữ lần đầu kể cả lần đầu lỗi; không lấy lần hợp lệ đầu tiên. Owner khác hoa/thường giữ riêng. Giờ 0 hợp lệ.
- Đề xuất sửa dữ liệu thiếu/sai, kiểm tra bản ghi trùng; không sửa CSV nguồn.
- Nếu script thất bại: báo lỗi thực thi từ stderr, không dùng mẫu để tạo báo cáo thành công.
