"""Run the order and CP pilot using the benchmark deadline and size guards."""

if __package__:
    from .benchmark import REPO_ROOT, _load_config, run_benchmark
else:
    from benchmark import REPO_ROOT, _load_config, run_benchmark


def main():
    config = REPO_ROOT / "configs" / "order_cp_pilot.json"
    return run_benchmark(_load_config(config), config)


if __name__ == "__main__":
    raise SystemExit(main())
