import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from parsing import *

fail_states = ("DOWN", "NODE_FAIL", "DRAIN")


def get_and_transform(d, key, transform, default):
    try:
        v = d[key]
    except KeyError:
        return default

    return transform(v)


def parse_nullable_float(v: str):
    if v.lower() == "n/a":
        return None

    return float(v)

@dataclass
class NodeState:
    name: str
    arch: Optional[str]

    cores_per_socket: int
    
    cpu_alloc: int
    cpu_total: int

    cpu_load: float

    available_features: List[str]
    active_features: List[str]

    gres: List[str]

    address: str
    hostname: str
    version: str

    kernel_version: str

    memory_total_mbytes: float
    memory_alloc_mbytes: float
    memory_free_mbytes: float

    sockets: int
    boards: int

    state: str # TODO: enum
    state_reason: Optional[str]

    threads_per_core: int

    tmp_disk: int
    weight: float

    # owner
    # MCS_label

    partitions: List[str]

    boot_time: str # TODO: date
    slurm_start_time: str # TODO: date

    tres_total: List[str]
    tres_alloc: List[str]
    cap_watts: str # TODO
    current_watts: str # TODO
    average_watts: str # TODO
    ext_sensors_joules: str # TODO
    ext_sensors_watts: str # TODO
    ext_sensors_temp: str # TODO

    def __init__(self, node_state_dict: Dict[str, str]):
        n = node_state_dict

        self.name = n["NodeName"]
        self.arch = n.get("Arch", None)
        self.cores_per_socket = get_and_transform(n, "CoresPerSocket", transform=int, default=None)

        self.cpu_alloc = int(n["CPUAlloc"])
        self.cpu_total = int(n["CPUTot"])

        self.cpu_load = get_and_transform(n, "CPULoad", transform=parse_nullable_float, default=None)

        self.available_features = get_and_transform(n, "AvailableFeatures", transform=parse_nullable_list, default=[])
        self.active_features = get_and_transform(n, "ActiveFeatures", transform=parse_nullable_list, default=[])

        self.gres = parse_trackable_resources(n["Gres"])

        self.address = n.get("NodeAddr", None)
        self.hostname = n.get("NodeHostName", None)
        self.version = n.get("Version", None)

        self.kernel_version = n.get("OS", None)

        self.memory_total_mbytes = get_and_transform(n, "RealMemory", transform=parse_nullable_float, default=None)
        self.memory_alloc_mbytes = get_and_transform(n, "AllocMem", transform=parse_nullable_float, default=0)
        self.memory_free_mbytes = get_and_transform(n, "FreeMem", transform=parse_nullable_float, default=0)

        self.sockets = get_and_transform(n, "Sockets", transform=int, default=None)
        self.boards = get_and_transform(n, "Boards", transform=int, default=None)

        self.state = n["State"]
        self.state_reason = n.get("Reason", None)
        self.up = not any(fail_state in self.state for fail_state in fail_states)

        self.threads_per_core = int(n.get("ThreadsPerCore", 1))

        self.tmp_disk = 0
        self.weight = 0

        self.partitions = get_and_transform(n, "Partitions", transform=parse_nullable_list, default=[])

        self.boot_time = None
        self.slurm_start_time = None

        self.tres_total = parse_trackable_resources(n["CfgTRES"])
        self.tres_alloc = parse_trackable_resources(n["AllocTRES"])
        self.cap_watts = None
        self.current_watts = None
        self.average_watts = None
        self.ext_sensors_joules = None
        self.ext_sensors_watts = None
        self.ext_sensors_temp = None


def parse_node_list(node_list: List[str]) -> dict:
    jobs = {}

    for job_line in node_list:
        fields = parse_info_line(job_line)
        jobs[fields["NodeName"]] = NodeState(fields)

    return jobs


async def query_nodes() -> Dict[str, NodeState]:
    proc = await asyncio.create_subprocess_exec(
        "scontrol", "show", "nodes", "--oneliner", "--quiet",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    output = stdout.decode("utf-8").splitlines()
    return parse_node_list(output)
