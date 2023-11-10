import argparse
import glob
import logging
import os.path
import pathlib
import re

from helper_functions import parse_pou_file

argparser = argparse.ArgumentParser(
    description="Utility function for creating reports from all files matching a given pattern")
argparser.add_argument("--base-path", required=True, help="The root path to look for file in")
argparser.add_argument("--file-match-glob", required=False, default="**/*.pou")
argparser.add_argument("--output-report-path", required=True)
argparser.add_argument("--dry-run", required=False, action="store_true")
argparser.add_argument("--ignore-files", required=False, default=[], nargs="+", metavar="IgnoreMe",
                       help="File name patterns to ignore")

log = logging.Logger("batch_logger")
log.setLevel(logging.INFO)


def parse_or_except(file_to_parse):
    try:
        program = parse_pou_file(file_to_parse)
        report = program.report_as_text()
        return report

    except Exception as e:
        log.error(f"Failure during parse process of {file_to_parse}. {e}")
        return None


def main():
    args = argparser.parse_args()
    files_to_process = glob.glob(args.base_path + "/" + args.file_match_glob, recursive=True)
    for ignore_pattern in args.ignore_files:
        files_to_process = [f for f in files_to_process if re.match(ignore_pattern, os.path.basename(f)) == None]
    if args.dry_run:
        print("The following files would be analysed:")
        print("\n".join(files_to_process))
    else:
        results = [parse_or_except(f) for f in files_to_process]
        results_filtered = [r for r in results if r is not None]

        pathlib.Path(args.output_report_path).write_text("\n\n\n".join(results_filtered), encoding="utf8")


if __name__ == "__main__":
    main()
