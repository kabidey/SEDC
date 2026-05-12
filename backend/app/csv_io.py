import csv
import io
from typing import List, Dict, Any, Optional
from fastapi.responses import StreamingResponse


def rows_to_csv(rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> StreamingResponse:
    if not rows:
        rows = []
    if not fieldnames:
        keys = set()
        for r in rows:
            keys.update(r.keys())
        fieldnames = sorted(keys)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for r in rows:
        writer.writerow({k: (v if not isinstance(v, (list, dict)) else str(v)) for k, v in r.items()})
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=export.csv'})


def csv_to_rows(content: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content))
    return [dict(r) for r in reader]
