"""Run the configured methods on the benchmark manifest."""

import argparse


def main() -> None:
    """Parse command-line inputs for the planned workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/benchmark.json", help="Experiment configuration")
    parser.parse_args()
    raise NotImplementedError("Run the configured methods on the benchmark manifest.")


if __name__ == "__main__":
    main()
