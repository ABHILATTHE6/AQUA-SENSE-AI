import json
import sys

from scripts.evaluate_water_stress_baseline import main


def test_evaluation_cli_writes_json_report(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "daily.jsonl"
    output_path = tmp_path / "reports" / "sensitivity.json"
    rows = []
    for day in range(1, 5):
        rows.append(
            {
                "date": f"2026-09-{day:02d}",
                "location_id": "demo_location",
                "rainfall_mm_sum": float(day),
                "soil_moisture_m3_m3_mean": 0.1 + day * 0.05,
                "et0_mm_sum": float(8 - day),
                "air_temperature_c_mean": float(35 - day),
            }
        )
    input_path.write_text(
        "".join(json.dumps(row) + "\\n" for row in rows), encoding="utf-8"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluate_water_stress_baseline.py", "--input", str(input_path), "--output", str(output_path)],
    )
    assert main() == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["dataset_window"]["row_count"] == 4
    assert report["predictive_accuracy_assessed"] is False
    assert "Predictive accuracy was not assessed" in capsys.readouterr().out
