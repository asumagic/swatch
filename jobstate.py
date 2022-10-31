import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import datetime
import pathlib
import os

from parsing import *


@dataclass
class JobState:
    job_id: int

    array_job_id: Optional[int]
    array_task_id: Optional[str]
    array_task_throttle: Optional[int]

    job_name: str

    user_name: str
    user_id: int

    group_name: str
    group_id: int

    mcs_label: str

    priority: int

    nice: int

    account: str

    qos: str # TODO: enum

    job_state: str # TODO: enum
    job_state_reasons: List[str] # TODO: enum?

    dependency: str # TODO: ?

    requeue: bool
    restart_count: int

    was_run_using_sbatch: bool

    requested_node_reboot: bool

    exit_code: int
    exit_signal: int

    run_time: datetime.timedelta
    min_time_limit: datetime.timedelta
    max_time_limit: datetime.timedelta

    submit_time: datetime.datetime
    eligible_time: datetime.datetime
    accrue_time: datetime.datetime
    start_time: datetime.datetime
    end_time: datetime.datetime
    deadline: Optional[datetime.datetime]
    suspend_time: Optional[datetime.datetime]

    secs_pre_suspend: Optional[int]

    last_sched_eval: datetime.datetime

    partition: str

    requested_nodes: List[str]
    excluded_nodes: List[str]
    nodes: List[str]

    num_nodes: int
    num_tasks: int

    num_cpus: int
    cpus_per_task: int

    requested_baseboards: Optional[int]
    requested_sockets_pre_baseboard: Optional[int]
    requested_cores_per_socket: Optional[int]
    requested_threads_per_core: Optional[int]

    trackable_resources: List[Tuple[str, str]]
    trackable_resources_per_node: List[Tuple[str, str]]

    sockets_per_node: Optional[int]

    tasks_per_node: Optional[int]
    tasks_per_baseboard: Optional[int]
    tasks_per_socket: Optional[int]
    tasks_per_core: Optional[int]

    system_reserved_cores: Optional[int]

    min_cpus_per_node: Optional[int]
    min_ram_per_node: Optional[str] # TODO: as bytes
    min_tmp_disk_per_node: str

    stdout_path: Optional[pathlib.Path]
    stderr_path: Optional[pathlib.Path]

    features: Optional[str]
    delay_boot: datetime.timedelta

    over_subscribe: bool

    require_contiguous_nodes: bool

    command: str

    workdir: pathlib.Path

    power: str

    mail_user: str
    mail_type: str # TODO: enum (list of enum?)?

    def __init__(self, job_state_dict: Dict[str, str]):
        j = job_state_dict

        self.job_id = int(j["JobId"])

        self.array_job_id = None
        self.array_task_id = None
        self.array_task_throttle = None

        self.job_name = j["JobName"]

        user_field = j["UserId"]
        self.user_name = user_field[:user_field.index("(")]
        self.user_id = int(user_field[user_field.index("(")+1:user_field.index(")")])

        group_field = j["GroupId"]
        self.group_name = group_field[:group_field.index("(")]
        self.group_id = int(group_field[group_field.index("(")+1:group_field.index(")")])

        self.mcs_label = j["MCS_label"]

        self.priority = int(j["Priority"])

        self.nice = int(j["Nice"])

        self.account = j["Account"]

        self.qos = j["QOS"]

        self.job_state = j["JobState"]
        self.job_state_reasons = j["Reason"].split(",")

        self.dependency = j["Dependency"]

        self.requeue = int(j["Requeue"]) != 0
        self.restart_count = int(j["Restarts"])

        self.was_run_using_sbatch = int(j["BatchFlag"]) != 0

        self.requested_node_reboot = int(j["Reboot"]) != 0

        code_str, signal_str = j["ExitCode"].split(":")
        self.exit_code = int(code_str)
        self.exit_signal = int(signal_str)

        self.run_time = parse_slurm_timedelta(j["RunTime"])
        self.min_time_limit = parse_slurm_timedelta(j["TimeMin"])
        self.max_time_limit = parse_slurm_timedelta(j["TimeLimit"])

        self.submit_time = parse_slurm_date(j["SubmitTime"])
        self.eligible_time = parse_slurm_date(j["EligibleTime"])
        self.accrue_time = parse_slurm_date(j["AccrueTime"])
        self.start_time = parse_slurm_date(j["StartTime"])
        self.end_time = parse_slurm_date(j["EndTime"])
        self.deadline = parse_slurm_date(j["Deadline"])
        self.suspend_time = parse_slurm_date(j["SuspendTime"])

        self.secs_pre_suspend = int(j["SecsPreSuspend"])

        self.last_sched_eval = parse_slurm_date(j["LastSchedEval"])

        self.partition = j["Partition"]

        self.requested_nodes = parse_nullable_list(j["ReqNodeList"])
        self.excluded_nodes = parse_nullable_list(j["ExcNodeList"])
        self.nodes = parse_nullable_list(j["NodeList"])

        # TODO: BatchHost

        self.num_nodes = 0 # int(j["NumNodes"]) # TODO: can be 1-1 etc
        self.num_tasks = int(j["NumTasks"])

        self.num_cpus = int(j["NumCPUs"])
        self.cpus_per_task = int(j["CPUs/Task"])

        req_b, req_s, req_c, req_t = j["ReqB:S:C:T"].split(":")
        self.requested_baseboards = parse_count_field(req_b)
        self.requested_sockets_pre_baseboard = parse_count_field(req_s)
        self.requested_cores_per_socket = parse_count_field(req_c)
        self.requested_threads_per_core = parse_count_field(req_t)

        self.trackable_resources = parse_trackable_resources(j["TRES"])

        if "TresPerNode" in j:
            self.trackable_resources_per_node = parse_trackable_resources(j["TresPerNode"])
        else:
            self.trackable_resources_per_node = []

        self.sockets_per_node = parse_count_field(j["Socks/Node"])

        task_n, task_b, task_s, task_c = j["NtasksPerN:B:S:C"].split(":")
        self.tasks_per_node = parse_count_field(task_n)
        self.tasks_per_baseboard = parse_count_field(task_b)
        self.tasks_per_socket = parse_count_field(task_s)
        self.tasks_per_core = parse_count_field(task_c)

        self.system_reserved_cores = parse_count_field(j["CoreSpec"])

        self.min_cpus_per_node = j["MinCPUsNode"]
        self.min_ram_per_node = j.get("MinMemoryNode", None) # TODO: as bytes
        self.min_tmp_disk_per_node = int(j["MinTmpDiskNode"])

        self.stdout_path = j.get("StdOut", None)
        self.stderr_path = j.get("StdErr", None)

        self.features = j["Features"]
        self.delay_boot = parse_slurm_timedelta(j["DelayBoot"])

        self.over_subscribe = j["OverSubscribe"] == "OK"

        self.require_contiguous_nodes = int(j["Contiguous"]) != 0

        self.command = j["Command"]

        self.workdir = pathlib.Path(j["WorkDir"])

        self.power = j["Power"]

        self.mail_user = j["MailUser"]
        self.mail_type = j["MailType"]
    
    def get_node_count(self):
        return int(self.trackable_resources["node"])
    
    def get_cpus(self):
        return int(self.trackable_resources["cpu"])
    
    def get_ram(self) -> str:
        return self.trackable_resources["mem"]

    def get_gpus(self, compact: bool = False) -> str:
        def compact_filter(text: str):
            if ":" in text:
                return text[text.rindex(":")+1:]

            return text

        if not compact:
            compact_filter = lambda x: x

        if "gpu" in self.trackable_resources_per_node:
            return compact_filter(self.trackable_resources_per_node["gpu"])

        if "gres/gpu" in self.trackable_resources:
            return compact_filter(self.trackable_resources["gres/gpu"])
        
        return "-"

    def is_mine(self) -> bool:
        return self.user_name == os.getlogin()

def parse_job_list(job_list: List[str]) -> dict:
    jobs = {}

    for job_line in job_list:
        fields = parse_info_line(job_line)
        jobs[fields["JobId"]] = JobState(fields)
    
    return jobs

async def query_jobs() -> Dict[str, JobState]:
    proc = await asyncio.create_subprocess_exec(
        "scontrol", "show", "jobs", "--oneliner", "--quiet",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)
    
    stdout, stderr = await proc.communicate()
    output = stdout.decode("utf-8").splitlines()
    return parse_job_list(output)

async def query_job(job_id: str) -> JobState:
    if not match_jobid.match(job_id):
        raise ValueError("Invalid slurm JobID received")
    
    proc = await asyncio.create_subprocess_exec(
        "scontrol", "show", "job", job_id, "--oneliner", "--quiet",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)
    
    stdout, stderr = await proc.communicate()

    output = stdout.decode("utf-8")

    return JobState(parse_info_line(output))