"""Plot benchmark summaries using cnsplots for the report."""

import argparse


def main() -> None:
    """Parse command-line inputs for the planned workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="results/summary", help="Input summaries")
    parser.add_argument("--output-dir", default="results/figures", help="Output figures")
    parser.parse_args()
    raise NotImplementedError("Plot benchmark summaries using cnsplots for the report.")


if __name__ == "__main__":
    main()
