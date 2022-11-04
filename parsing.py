import datetime
import re
from typing import Optional, List, Tuple

missing_date_identifiers = ["N/A", "Unknown", "None"]

match_jobid = re.compile("^[.0-9]+$")

def as_slurm_timedelta(t: datetime.timedelta) -> str:
    hours, rem = divmod(t.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{t.days:02}-{hours:02}:{minutes:02}:{seconds:02}"

def parse_slurm_timedelta(t: str) -> Optional[datetime.timedelta]:
    if t in missing_date_identifiers:
        return None

    days_delta = datetime.timedelta()
    
    if "-" in t:
        days_delta = datetime.timedelta(days=int(t[:t.index("-")]))
        t = t[t.index("-")+1:]
    
    base_date = datetime.datetime.strptime(t, "%H:%M:%S")
    base_delta = datetime.timedelta(
        hours=base_date.hour, minutes=base_date.minute, seconds=base_date.second)

    return base_delta + days_delta

def parse_slurm_date(t: str) -> Optional[datetime.datetime]:
    if t in missing_date_identifiers:
        return None
    
    return datetime.datetime.fromisoformat(t)

def parse_count_field(field: str) -> Optional[int]:
    if field == "*":
        return None
    
    return int(field)

def parse_trackable_resource(tres: str):
    if "=" in tres:
        return (tres[:tres.index("=")], tres[tres.index("=")+1:])
    if ":" in tres:
        return (tres[:tres.index(":")], tres[tres.index(":")+1:])
    
    return (tres, None)

def parse_trackable_resources(tres: str) -> List[Tuple[str, str]]:
    if tres == "(null)" or len(tres.strip()) == 0:
        return {}

    return dict(
        parse_trackable_resource(entry)
        for entry in tres.split(",")
    )

def parse_nullable_list(l: str) -> Optional[List[str]]:
    if l == "(null)":
        return None
    
    return l.split(",")

def parse_info_line(job_line: str) -> dict:
    fields = {}
    last_field = None

    for word in job_line.split(" "):
        if "=" in word:
            eq_index = word.index("=")
            last_field = word[:eq_index]
            fields[last_field] = word[eq_index+1:]
        elif last_field is not None:
            fields[last_field] += f" {word}"

    return {k: v.strip() for k, v in fields.items()}