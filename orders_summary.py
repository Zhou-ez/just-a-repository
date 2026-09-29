#!/usr/bin/env python3
"""orders_summary.py

读取订单 CSV，按 user_id 汇总 amount，输出汇总 CSV。
仅使用 Python 标准库，单文件运行。

示例：
    python orders_summary.py orders.csv -o summary.csv
    python orders_summary.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import logging
import tempfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Sequence

LOG = logging.getLogger("orders_summary")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="读取订单 CSV，按用户汇总金额并输出汇总 CSV。",
    )
    parser.add_argument("input", nargs="?", type=Path, help="输入 CSV 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("summary.csv"),
        help="输出 CSV 文件路径，默认 summary.csv",
    )
    parser.add_argument("--user-col", default="user_id", help="用户列名，默认 user_id")
    parser.add_argument("--amount-col", default="amount", help="金额列名，默认 amount")
    parser.add_argument("--encoding", default="utf-8-sig", help="输入文件编码，默认 utf-8-sig")
    parser.add_argument("--delimiter", default=",", help="CSV 分隔符，默认逗号")
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别，默认 INFO",
    )
    parser.add_argument("--self-test", action="store_true", help="运行内置自测后退出")
    args = parser.parse_args(argv)

    if not args.self_test and args.input is None:
        parser.error("必须提供输入 CSV 文件路径，或使用 --self-test")
    return args


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def summarize_orders(
    input_path: Path,
    user_col: str,
    amount_col: str,
    encoding: str,
    delimiter: str,
) -> list[tuple[str, Decimal]]:
    if not input_path.is_file():
        raise FileNotFoundError(f"输入文件不存在或不是普通文件: {input_path}")

    totals: defaultdict[str, Decimal] = defaultdict(Decimal)

    with input_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV 文件为空或没有表头")

        missing = {user_col, amount_col} - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"缺少列: {', '.join(sorted(missing))}; 实际列: {reader.fieldnames}"
            )

        for line_no, row in enumerate(reader, start=2):
            user = (row.get(user_col) or "").strip()
            raw_amount = (row.get(amount_col) or "").strip()

            if not user:
                LOG.warning("第 %d 行用户为空，已跳过", line_no)
                continue
            if not raw_amount:
                LOG.warning("第 %d 行金额为空，已跳过", line_no)
                continue

            try:
                amount = Decimal(raw_amount)
            except InvalidOperation as exc:
                raise ValueError(
                    f"第 {line_no} 行金额无法解析: {raw_amount!r}"
                ) from exc

            totals[user] += amount

    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def write_summary(
    output_path: Path,
    rows: Iterable[tuple[str, Decimal]],
    encoding: str = "utf-8",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["user_id", "total_amount"])
        for user, total in rows:
            writer.writerow([user, format(total, "f")])


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "orders.csv"
        output_path = tmp_path / "summary.csv"

        input_path.write_text(
            "user_id,amount\n"
            "b,2.5\n"
            "a,1.25\n"
            "b,3.75\n",
            encoding="utf-8",
        )

        rows = summarize_orders(
            input_path=input_path,
            user_col="user_id",
            amount_col="amount",
            encoding="utf-8",
            delimiter=",",
        )
        assert rows == [("b", Decimal("6.25")), ("a", Decimal("1.25"))], rows

        write_summary(output_path, rows)
        text = output_path.read_text(encoding="utf-8")
        expected = "user_id,total_amount\nb,6.25\na,1.25\n"
        assert text == expected, text

    print("self-test passed")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.log_level)

    if args.self_test:
        run_self_test()
        return 0

    try:
        rows = summarize_orders(
            input_path=args.input,
            user_col=args.user_col,
            amount_col=args.amount_col,
            encoding=args.encoding,
            delimiter=args.delimiter,
        )
        write_summary(args.output, rows)
        LOG.info("已汇总 %d 个用户，结果写入 %s", len(rows), args.output)
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        LOG.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
