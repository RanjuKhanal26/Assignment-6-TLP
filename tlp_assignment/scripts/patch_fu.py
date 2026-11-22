import argparse
import re
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument("--source", required=True)
parser.add_argument("--op-lat", type=int)
parser.add_argument("--issue-lat", type=int)
parser.add_argument("--restore", action="store_true")

args = parser.parse_args()

source = Path(args.source).resolve()
backup = source.with_suffix(source.suffix + ".tlp_original")

if not source.exists():
    raise SystemExit("MinorCPU.py was not found.")

if args.restore:
    if not backup.exists():
        raise SystemExit("Original backup was not found.")

    shutil.copy2(backup, source)
    print("Original MinorCPU.py restored.")
    raise SystemExit(0)

if args.op_lat is None or args.issue_lat is None:
    raise SystemExit("Provide both latency values.")

if args.op_lat < 1 or args.issue_lat < 1:
    raise SystemExit("Latency values must be positive.")

if args.op_lat + args.issue_lat != 7:
    raise SystemExit("opLat + issueLat must equal 7.")

# Save the original source only once.
if not backup.exists():
    shutil.copy2(source, backup)

text = backup.read_text()

# Locate the FloatSimd functional unit class.
pattern = (
    r"(class\s+MinorDefaultFloatSimdFU\s*\([^)]*\)\s*:\s*)"
    r"(.*?)(?=\nclass\s|\Z)"
)

match = re.search(pattern, text, flags=re.S)

if not match:
    raise SystemExit(
        "MinorDefaultFloatSimdFU was not found. "
        "Inspect MinorCPU.py and check the class name."
    )

block = match.group(2)

def update_parameter(block, name, value):

    pattern = re.compile(
        r"(^[ \t]*" + name +
        r"\s*=\s*Param\.Cycles\()\s*\d+(\s*,)",
        flags=re.M
    )

    updated, count = pattern.subn(
        r"\g<1>" + str(value) + r"\g<2>",
        block,
        count=1
    )

    if count != 1:
        raise SystemExit("Could not update " + name)

    return updated

block = update_parameter(block, "opLat", args.op_lat)
block = update_parameter(block, "issueLat", args.issue_lat)

updated_text = (
    text[:match.start(2)]
    + block
    + text[match.end(2):]
)

source.write_text(updated_text)

print("FloatSimdFU updated successfully.")
print("opLat   =", args.op_lat)
print("issueLat=", args.issue_lat)
print("Total   =", args.op_lat + args.issue_lat)
print("Backup  =", backup)
