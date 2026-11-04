import csv
import io


MAX_RECORDS = 10_000


def parse_csv_content(content: bytes) -> list[dict]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must use UTF-8 encoding.") from exc

    reader = csv.reader(io.StringIO(text, newline=""))

    try:
        headers = next(reader)
    except StopIteration:
        raise ValueError("CSV file is empty.")

    headers = [header.strip() for header in headers]

    if not headers or any(not header for header in headers):
        raise ValueError("CSV contains an empty column name.")

    if len(headers) != len(set(headers)):
        raise ValueError("CSV contains duplicate column names.")

    records = []

    for row_number, row in enumerate(reader, start=2):
        if not row:
            continue

        if len(row) != len(headers):
            raise ValueError(
                f"Row {row_number} has {len(row)} values; "
                f"expected {len(headers)}."
            )

        records.append(dict(zip(headers, row)))

        if len(records) > MAX_RECORDS:
            raise ValueError(
                f"CSV exceeds the maximum of {MAX_RECORDS} records."
            )

    if not records:
        raise ValueError("CSV contains headers but no data records.")

    return records