#!/usr/bin/env python3
"""Kiểm tra chất lượng CSV công việc (task_id, owner, hours) và in JSON ra stdout.

Cách chạy (cwd là workspace):
    python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours <ngưỡng>

Exit 0: phân tích thành công, kể cả khi dữ liệu có lỗi chất lượng.
Exit 1: file không tồn tại/không đọc được, thiếu cột bắt buộc, lỗi parse CSV,
        giá trị --max-hours không hợp lệ; thông báo ra stderr.
Exit 2: thiếu tham số CLI bắt buộc; thông báo ra stderr.
Script chỉ đọc, không sửa CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys

REQUIRED_COLUMNS = ("task_id", "owner", "hours")

# Thứ tự chuẩn của mã lý do loại dòng, dùng để sắp xếp ổn định.
REASON_ORDER = {
    "wrong_field_count": 0,
    "missing_task_id": 1,
    "duplicate_id": 2,
    "missing_owner": 3,
    "invalid_hours": 4,
}


class InputError(Exception):
    pass


def parse_hours(raw: str | None) -> float | None:
    """Số giờ hợp lệ: số hữu hạn, không âm. Trả None nếu không hợp lệ."""
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value


def analyze(path: str, max_hours: float) -> dict:
    try:
        handle = open(path, encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise InputError(f"Không đọc được file {path}: {exc.strerror or exc}") from exc
    with handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise InputError(f"File {path} rỗng, không có header.")
            columns = [c.strip() for c in header]
            missing = [c for c in REQUIRED_COLUMNS if c not in columns]
            if missing:
                raise InputError(f"Thiếu cột bắt buộc: {', '.join(missing)}. Header hiện có: {', '.join(columns)}")
            index = {name: columns.index(name) for name in REQUIRED_COLUMNS}

            row_count = 0
            missing_owner = 0
            invalid_hours = 0
            first_seen: dict[str, int] = {}
            duplicate_ids: list[str] = []
            issues: list[dict] = []

            # --- Phần mở rộng: tổng giờ và dòng bị loại ---
            hours_by_owner: dict[str, float] = {}
            excluded_rows: list[dict] = []

            for row in reader:
                line = reader.line_num
                if not any(cell.strip() for cell in row):
                    continue  # bỏ qua dòng trống

                row_count += 1

                def cell(name: str) -> str:
                    position = index[name]
                    return row[position].strip() if position < len(row) else ""

                task_id, owner, hours_raw = cell("task_id"), cell("owner"), cell("hours")
                hours_value = parse_hours(hours_raw)

                # Thu thập tất cả lý do loại dòng này
                row_reasons: list[str] = []

                # --- Kiểm tra chất lượng (giữ nguyên logic cũ) ---
                if len(row) != len(columns):
                    issues.append({"line": line, "column": None, "type": "wrong_field_count", "task_id": task_id or None,
                                   "message": f"Có {len(row)} trường, header có {len(columns)} cột."})
                    row_reasons.append("wrong_field_count")

                if not task_id:
                    issues.append({"line": line, "column": "task_id", "type": "missing_task_id", "task_id": None,
                                   "message": "task_id trống."})
                    row_reasons.append("missing_task_id")
                elif task_id in first_seen:
                    if task_id not in duplicate_ids:
                        duplicate_ids.append(task_id)
                    issues.append({"line": line, "column": "task_id", "type": "duplicate_id", "task_id": task_id,
                                   "message": f"task_id {task_id} đã xuất hiện ở line {first_seen[task_id]}."})
                    row_reasons.append("duplicate_id")
                else:
                    first_seen[task_id] = line

                if not owner:
                    missing_owner += 1
                    issues.append({"line": line, "column": "owner", "type": "missing_owner", "task_id": task_id or None,
                                   "message": "owner trống."})
                    row_reasons.append("missing_owner")

                if hours_value is None:
                    invalid_hours += 1
                    issues.append({"line": line, "column": "hours", "type": "invalid_hours", "task_id": task_id or None,
                                   "value": hours_raw, "message": f"hours '{hours_raw}' không phải số hữu hạn không âm."})
                    row_reasons.append("invalid_hours")

                # --- Quyết định cộng vào tổng giờ hay loại ---
                # Chỉ cộng khi: đúng số trường, ID không rỗng, không trùng, owner không rỗng, hours hợp lệ.
                if row_reasons:
                    # Sắp xếp reasons theo thứ tự chuẩn
                    row_reasons.sort(key=lambda r: REASON_ORDER.get(r, 99))
                    excluded_rows.append({
                        "line": line,
                        "task_id": task_id if task_id else None,
                        "reasons": row_reasons,
                    })
                else:
                    # Dòng hợp lệ hoàn toàn → cộng vào tổng giờ
                    hours_by_owner[owner] = hours_by_owner.get(owner, 0.0) + hours_value

        except csv.Error as exc:
            raise InputError(f"Lỗi parse CSV ở line {reader.line_num}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise InputError(f"File {path} không phải UTF-8: {exc}") from exc

    result = {
        "input": path,
        "row_count": row_count,
        "missing_owner_count": missing_owner,
        "invalid_hours_count": invalid_hours,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "issues": sorted(issues, key=lambda item: item["line"]),
    }

    result["max_hours"] = max_hours
    result["hours_by_owner"] = hours_by_owner
    result["overloaded_owners"] = [
        {"owner": name, "total_hours": total}
        for name, total in sorted(hours_by_owner.items())
        if total > max_hours
    ]
    result["excluded_rows"] = sorted(excluded_rows, key=lambda r: r["line"])

    return result


def main(argv: list[str] | None = None) -> int:
    # Đảm bảo stdout/stderr dùng UTF-8 trên Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng CSV công việc (task_id, owner, hours).")
    parser.add_argument("--input", required=True, help="Đường dẫn CSV, ví dụ data/tasks.csv")
    parser.add_argument("--max-hours", required=True,
                        help="Ngưỡng giờ tối đa mỗi người (số hữu hạn không âm).")
    args = parser.parse_args(argv)

    max_hours = parse_hours(args.max_hours)
    if max_hours is None:
        print(f"ERROR: --max-hours phải là số hữu hạn không âm, nhận được '{args.max_hours}'.", file=sys.stderr)
        return 1

    try:
        result = analyze(args.input, max_hours=max_hours)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
