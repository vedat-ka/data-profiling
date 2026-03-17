from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = BASE_DIR / "my_data.csv"
SVG_STYLE_PATTERN = "<style type=text/css>*{stroke-linejoin: round; stroke-linecap: butt}</style>"
SVG_STYLE_REPLACEMENT = (
	"<style type=text/css>"
	"path, line, polyline, polygon, rect, circle, ellipse {"
	"stroke-linejoin: round; stroke-linecap: butt"
	"}</style>"
)


def parse_args() -> ArgumentParser:
	parser = ArgumentParser(description="Create a ydata-profiling HTML report for a CSV file.")
	parser.add_argument(
		"csv_path",
		nargs="?",
		default=str(DEFAULT_CSV_PATH),
		help="Path to the CSV file you want to inspect.",
	)
	parser.add_argument(
		"--output",
		default=None,
		help="Optional output path for the HTML report.",
	)
	return parser


def build_output_path(csv_path: Path, output: str | None) -> Path:
	if output:
		return Path(output).expanduser().resolve()
	return csv_path.with_name(f"{csv_path.stem}_profile.html")


def print_dataframe_summary(dataframe: pd.DataFrame) -> None:
	missing_cells = int(dataframe.isna().sum().sum())
	duplicate_rows = int(dataframe.duplicated().sum())

	print("\nData overview:")
	print(f"Rows: {len(dataframe)}")
	print(f"Columns: {len(dataframe.columns)}")
	print(f"Missing cells: {missing_cells}")
	print(f"Duplicate rows: {duplicate_rows}")
	print("\nColumns:")
	for column in dataframe.columns:
		missing_values = int(dataframe[column].isna().sum())
		print(f"- {column}: dtype={dataframe[column].dtype}, missing={missing_values}")


def sanitize_embedded_svg_styles(html_path: Path) -> int:
	html = html_path.read_text(encoding="utf-8")
	replacements = html.count(SVG_STYLE_PATTERN)
	if replacements == 0:
		return 0
	html = html.replace(SVG_STYLE_PATTERN, SVG_STYLE_REPLACEMENT)
	html_path.write_text(html, encoding="utf-8")
	return replacements


def main() -> None:
	args = parse_args().parse_args()

	csv_path = Path(args.csv_path).expanduser().resolve()
	output_path = build_output_path(csv_path, args.output)

	print("Starting data profiling...")
	print(f"Input CSV: {csv_path}")
	print(f"Output report: {output_path}")
	print("Reading CSV file...")

	dataframe = pd.read_csv(csv_path)
	print("CSV loaded successfully.")
	print_dataframe_summary(dataframe)
	print("\nCreating ydata-profiling report...")

	profile = ProfileReport(
		dataframe,
		title=f"ydata-profiling: {csv_path.name}",
		explorative=True,
		progress_bar=False,
	)
	print("Writing HTML report...")
	profile.to_file(output_path)
	replacements = sanitize_embedded_svg_styles(output_path)
	if replacements:
		print(f"Patched {replacements} embedded SVG style blocks for browser compatibility.")

	print("\nProfiling finished.")
	print(f"CSV: {csv_path.name}")
	print(f"Rows: {len(dataframe)}")
	print(f"Columns: {len(dataframe.columns)}")
	print(f"Report: {output_path}")
	print("Open the HTML report and check: Overview, Variables, Missing Values, Duplicates, Samples.")


if __name__ == "__main__":
	main()