"""csv-quality script: thống kê fixture, lỗi input/schema/parse exit 1, lỗi dữ liệu exit 0."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"


def run(path, max_hours="8"):
    command = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        command.extend(["--max-hours", str(max_hours)])
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert "total_hours" not in data


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n")).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"))
    assert result.returncode == 0
    assert json.loads(result.stdout)["issues"] == []


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"))
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'))
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = paths.FIXTURES_DIR / "data" / "tasks.csv"
    before = source.read_bytes()
    run(source)
    assert source.read_bytes() == before


@pytest.mark.parametrize("threshold, overloaded", [(8, [{"owner": "Lan", "total_hours": 9}]), (9, [])])
def test_workload_and_strict_threshold(threshold, overloaded):
    result = run(paths.FIXTURES_DIR / "data" / "workload.csv", threshold)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["max_hours"] == threshold
    assert data["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data["overloaded_owners"] == overloaded
    assert data["excluded_rows"] == [
        {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
        {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
        {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]},
    ]
    assert (data["row_count"], data["invalid_hours_count"], data["missing_owner_count"], data["duplicate_ids"]) == (6, 1, 1, ["T02"])


def test_first_invalid_occurrence_still_reserves_id(tmp_path):
    source = write_csv(tmp_path, "task_id,owner,hours\nE01,Lan,abc\nE01,Lan,5\nE02,Minh,0\n")
    before = source.read_bytes()
    result = run(source, 0)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Minh": 0}
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == [
        {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
        {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]},
    ]
    assert source.read_bytes() == before


@pytest.mark.parametrize("threshold", [None, "abc", "nan", "inf", "-inf", "-1", ""])
def test_missing_or_invalid_threshold_fails(tmp_path, threshold):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,1\n"), threshold)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr


def test_normalization_all_reasons_and_quality_on_excluded_rows(tmp_path):
    source = write_csv(tmp_path, "task_id,owner,hours\n X , Lan ,2\nX,,nan,extra\n,,\nY,lan,0\nZ,Zed,3\nA,Ana,4\n\n   ,   ,   \nB,Bob\nB,Bob,7\n")
    data = json.loads(run(source, 1).stdout)
    assert data["hours_by_owner"] == {"Lan": 2, "lan": 0, "Zed": 3, "Ana": 4}
    assert [o["owner"] for o in data["overloaded_owners"]] == ["Ana", "Lan", "Zed"]
    assert data["excluded_rows"] == [
        {"line": 3, "task_id": "X", "reasons": ["wrong_field_count", "duplicate_id", "missing_owner", "invalid_hours"]},
        {"line": 10, "task_id": "B", "reasons": ["wrong_field_count", "invalid_hours"]},
        {"line": 11, "task_id": "B", "reasons": ["duplicate_id"]},
    ]
    assert data["row_count"] == 7
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 2


def test_missing_id_is_null_and_retains_all_reasons(tmp_path):
    data = json.loads(run(write_csv(tmp_path, "task_id,owner,hours\n,Lan,bad,extra\n"), 0).stdout)
    assert data["excluded_rows"] == [{"line": 2, "task_id": None, "reasons": ["wrong_field_count", "missing_task_id", "invalid_hours"]}]


def test_invalid_encoding_fails(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_bytes(b"task_id,owner,hours\nT1,\xff,1\n")
    result = run(source)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "UTF-8" in result.stderr
