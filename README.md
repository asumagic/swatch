# swatch

A lightweight web tool to monitor Slurm jobs and nodes with no admin privileges
required by parsing `scontrol` output.

## Features

- [Node list view](http://localhost:51024/): View advanced node status and
resource allocation information (as parsed from `scontrol show nodes`).
View various information on pending or active jobs per-partition and per-node.
- [Job view](http://localhost:51024/jobs): View the state of jobs on the
cluster, including per-job resource consumption, state reasons, etc. (as parsed
from `scontrol show jobs`).
Running, pending and recently failed or completed tasks will be displayed.
Your tasks are always shown at the top of the list.
- Tooltips with explanations and details on hover.

There is no automatic refresh feature at the moment.
Refresh the page when you want up-to-date information.  

`scontrol` command executions are cached for a few seconds, so changes
may not be immediately reflected in the UI.

## Setup

```bash
cd
git clone # ...
cd swatch
conda env create -f environment.yml # creates a 'swatch' conda env
```

Now, let's create a `password.txt` file that is **not world-readable**:

```bash
touch password.txt
chmod 600 password.txt
nano password.txt
```

`password.txt` should contain a single line with a **long** password of your choice
(just save it in your browser).

## Updating

You may want to regularly check for updates to gain access to new features,
bugfixes, and security patches:

```bash
cd ~/swatch
git pull
conda env update -f environment.yml -n swatch --prune
```

## Usage

For security reasons, this tool will only listen to `localhost` connections.
As you will be running `swatch` on your slurm login node, you will need to use
SSH port forwarding to access the server locally.

To run the server, execute this cursed one-liner **from your machine** (which
you can of course alias in your shell):

```bash
ssh -L localhost:51024:localhost:51432 -t myuser@myslurmloginnode 'exec conda run --no-capture-output --cwd ~/swatch -n swatch ~/swatch/swatch.py --port 51432 2>&1 | tee -a ~/swatch/log.txt'
```

To avoid port conflicts with other users, replace both mentions to port `51432`
with any unused port on the server you are running this on.  
`51024` will still be the port being forwarded to on your local machine.

Open [`http://localhost:51024`](http://localhost:51024) in your browser.

- Username: `swatch`
- Password: Whatever you set in `password.txt`.

Using the provided command, access logs are saved both to the standard output
and to `~/swatch/logs.txt`.
