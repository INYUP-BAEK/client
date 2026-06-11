import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


SUMMARY_FIELDS = [
    "target_color",
    "instruction",
    "seed",
    "num_steps",
    "first_close_step",
    "final_xy_error",
    "xy_error_at_close",
    "target_z_initial",
    "target_z_final",
    "object_lift_delta",
    "strict_lift_success",
    "stop_reason",
    "invalid_success_reason",
    "max_valid_lift_delta",
    "max_final_xy_error_for_success",
    "gate_close_by_xy",
    "close_xy_threshold",
    "assist_xy_alignment_before_close",
    "assist_xy_gain",
    "assist_xy_max_step",
    "assist_xy_deadband",
    "assist_xy_total_correction",
    "assist_xy_steps",
    "post_close_lift_controller",
    "post_close_hold_steps",
    "post_close_lift_dz",
    "post_close_lift_steps",
    "post_close_keep_xy",
    "post_close_controller_steps",
    "post_close_forced_lift_steps",
    "post_close_prevented_negative_z_steps",
    "total_xy_move",
    "post_close_lift_delta",
    "retry_sum",
]
AGGREGATE_FIELDS = [
    "color",
    "seed",
    "csv_path",
    "summary_json_path",
    "returncode",
    "error",
] + SUMMARY_FIELDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server_url", required=True)
    parser.add_argument("--xml_path", default="Raccoon_colored_cylinder.xml")
    parser.add_argument("--instruction", default=None)
    parser.add_argument("--instruction_template", default=None)
    parser.add_argument("--colors", nargs="+", default=["red", "blue", "green", "yellow"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--max_steps", type=int, default=200)
    parser.add_argument("--max_delta_xyz", type=float, default=0.12)
    parser.add_argument("--output_dir", default="batch_eval_outputs")
    parser.add_argument("--use_action_smoothing", action="store_true")
    parser.add_argument("--smooth_alpha", type=float, default=0.6)
    parser.add_argument("--max_action_abs", type=float, default=None)
    parser.add_argument("--stop_on_lift_success", action="store_true")
    parser.add_argument("--lift_success_threshold", type=float, default=0.010)
    parser.add_argument("--min_steps_after_close", type=int, default=10)
    parser.add_argument("--max_valid_lift_delta", type=float, default=0.08)
    parser.add_argument("--max_final_xy_error_for_success", type=float, default=0.05)
    parser.add_argument("--gate_close_by_xy", action="store_true")
    parser.add_argument("--close_xy_threshold", type=float, default=0.015)
    parser.add_argument("--preclose_min_z_when_xy_bad", type=float, nargs="?", const=0.045, default=None)
    parser.add_argument("--latch_gripper_after_close", action="store_true")
    parser.add_argument("--post_close_clamp_negative_z", action="store_true")
    parser.add_argument("--post_close_lift_controller", action="store_true")
    parser.add_argument("--post_close_hold_steps", type=int, default=3)
    parser.add_argument("--post_close_lift_dz", type=float, default=0.0025)
    parser.add_argument("--post_close_lift_steps", type=int, default=12)
    parser.add_argument("--post_close_keep_xy", action="store_true")
    parser.add_argument("--assist_xy_alignment_before_close", action="store_true")
    parser.add_argument("--assist_xy_gain", type=float, default=0.5)
    parser.add_argument("--assist_xy_max_step", type=float, default=0.004)
    parser.add_argument("--assist_xy_deadband", type=float, default=0.002)
    parser.add_argument("--no_save_images", action="store_true")
    return parser.parse_args()


def tail_message(text: str, max_lines: int = 12) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def load_summary(summary_path: Path) -> Dict[str, Any]:
    if not summary_path.exists():
        return {}
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def build_command(
    args: argparse.Namespace,
    client_path: Path,
    color: str,
    seed: int,
    episode_id: int,
    csv_path: Path,
    summary_path: Path,
) -> List[str]:
    cmd = [
        sys.executable,
        str(client_path),
        "--server_url",
        args.server_url,
        "--xml_path",
        args.xml_path,
        "--target_color",
        color,
        "--seed",
        str(seed),
        "--episode_id",
        str(episode_id),
        "--max_steps",
        str(args.max_steps),
        "--max_delta_xyz",
        str(args.max_delta_xyz),
        "--output_dir",
        str(args.output_dir),
        "--log_csv",
        str(csv_path),
        "--summary_json",
        str(summary_path),
        "--lift_success_threshold",
        str(args.lift_success_threshold),
        "--min_steps_after_close",
        str(args.min_steps_after_close),
        "--max_valid_lift_delta",
        str(args.max_valid_lift_delta),
        "--max_final_xy_error_for_success",
        str(args.max_final_xy_error_for_success),
        "--close_xy_threshold",
        str(args.close_xy_threshold),
        "--assist_xy_gain",
        str(args.assist_xy_gain),
        "--assist_xy_max_step",
        str(args.assist_xy_max_step),
        "--assist_xy_deadband",
        str(args.assist_xy_deadband),
        "--post_close_hold_steps",
        str(args.post_close_hold_steps),
        "--post_close_lift_dz",
        str(args.post_close_lift_dz),
        "--post_close_lift_steps",
        str(args.post_close_lift_steps),
    ]

    if args.instruction is not None:
        cmd.extend(["--instruction", args.instruction])
    if args.instruction_template is not None:
        cmd.extend(["--instruction_template", args.instruction_template])
    if args.use_action_smoothing:
        cmd.append("--use_action_smoothing")
    cmd.extend(["--smooth_alpha", str(args.smooth_alpha)])
    if args.max_action_abs is not None:
        cmd.extend(["--max_action_abs", str(args.max_action_abs)])
    if args.stop_on_lift_success:
        cmd.append("--stop_on_lift_success")
    if args.gate_close_by_xy:
        cmd.append("--gate_close_by_xy")
    if args.preclose_min_z_when_xy_bad is not None:
        cmd.extend(["--preclose_min_z_when_xy_bad", str(args.preclose_min_z_when_xy_bad)])
    if args.latch_gripper_after_close:
        cmd.append("--latch_gripper_after_close")
    if args.post_close_clamp_negative_z:
        cmd.append("--post_close_clamp_negative_z")
    if args.post_close_lift_controller:
        cmd.append("--post_close_lift_controller")
    if args.post_close_keep_xy:
        cmd.append("--post_close_keep_xy")
    if args.assist_xy_alignment_before_close:
        cmd.append("--assist_xy_alignment_before_close")
    if args.no_save_images:
        cmd.append("--no_save_images")
    return cmd


def write_summary_csv(output_dir: Path, rows: List[Dict[str, Any]]) -> None:
    summary_csv = output_dir / "summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AGGREGATE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in AGGREGATE_FIELDS})
    print(f"[BATCH] wrote {summary_csv}")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client_path = Path(__file__).with_name("openvla_multicolor_client.py")

    rows: List[Dict[str, Any]] = []
    episode_id = 1
    for color in args.colors:
        for seed in args.seeds:
            csv_path = output_dir / f"{color}_seed{seed}.csv"
            summary_path = output_dir / f"{color}_seed{seed}.summary.json"
            cmd = build_command(args, client_path, color, seed, episode_id, csv_path, summary_path)

            print(f"[BATCH] running color={color} seed={seed}")
            result = subprocess.run(cmd, text=True, capture_output=True)

            summary = load_summary(summary_path)
            error: Optional[str] = None
            if result.returncode != 0:
                error = tail_message(result.stderr) or tail_message(result.stdout) or f"returncode={result.returncode}"
                print(f"[BATCH] failed color={color} seed={seed}: {error}")
            elif not summary:
                error = "summary JSON was not written"
                print(f"[BATCH] missing summary color={color} seed={seed}")
            else:
                print(f"[BATCH] done color={color} seed={seed}")

            row: Dict[str, Any] = {
                "color": color,
                "seed": seed,
                "csv_path": str(csv_path),
                "summary_json_path": str(summary_path),
                "returncode": result.returncode,
                "error": error or "",
            }
            row.update(summary)
            rows.append(row)
            episode_id += 1

    write_summary_csv(output_dir, rows)


if __name__ == "__main__":
    main()
