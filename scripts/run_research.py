"""Run one configured research workflow."""

import argparse

from a_share_quant.runner import run_research


def main() -> None:
    parser = argparse.ArgumentParser(description="运行可重复的 A 股因子研究")
    parser.add_argument("config", help="JSON 配置文件路径")
    args = parser.parse_args()
    artifacts = run_research(args.config)
    print("研究结果已保存：", artifacts.output_dir)
    print("累计收益：", artifacts.metrics["cumulative_return"])
    print("最大回撤：", artifacts.metrics["max_drawdown"])


if __name__ == "__main__":
    main()
