"""Start the local review outside the calling app's Windows process job."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, socket, subprocess, sys, time

data = Path(__file__).resolve().parent
project = data.parent / 'book-review'
server = project / 'server.py'
url = 'http://127.0.0.1:8765/'
sys.path.insert(0, str(project))
from runtime_support import inspect_runtime, python_executable

def ready():
    try:
        with socket.create_connection(('127.0.0.1', 8765), timeout=0.3):
            return True
    except OSError:
        return False

def powershell_literal(value):
    """Quote a literal without PowerShell interpolation or command expansion."""
    return "'" + str(value).replace("'", "''") + "'"

def start_independent_server():
    if os.name != 'nt':
        raise RuntimeError('This local review launcher requires Windows.')
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
    if not powershell.is_file():
        raise RuntimeError('Windows PowerShell is missing: ' + str(powershell))
    command_line = subprocess.list2cmdline([str(python_executable()), '-X', 'utf8', str(server)])
    script = "\n".join([
        "$ErrorActionPreference = 'Stop'",
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)",
        "$reviewStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }",
        "$reviewResult = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{",
        '    CommandLine = ' + powershell_literal(command_line),
        '    CurrentDirectory = ' + powershell_literal(data.parent),
        '    ProcessStartupInformation = $reviewStartup',
        '}',
        "[ordered]@{ returnValue = [int]$reviewResult.ReturnValue; pid = [int]$reviewResult.ProcessId; startedAt = (Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json -Compress",
    ])
    try:
        result = subprocess.run(
            [str(powershell), '-NoProfile', '-NonInteractive', '-Command', script],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='replace',
            timeout=20, check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('Windows process creation timed out; check whether the local review is already available at ' + url) from error
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or 'no diagnostic output'
        raise RuntimeError('Windows could not create the review server: ' + detail)
    try:
        created = json.loads(result.stdout.strip())
        return_value = int(created['returnValue'])
        pid = int(created['pid'])
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError('Windows returned an invalid process creation result: ' + result.stdout.strip()) from error
    if return_value != 0 or pid <= 0:
        raise RuntimeError(f'Windows process creation failed (ReturnValue={return_value}, PID={pid}).')
    return dict(pid=pid, url=url, startedAt=created.get('startedAt') or datetime.now(timezone.utc).isoformat(),
                mode='hidden-independent-windows-process')

def main():
    if ready():
        print('Local book review is already running: ' + url)
        return 0
    if not server.is_file():
        raise RuntimeError('Local review server is missing: ' + str(server))
    report = inspect_runtime(data.parent, bootstrap=True)
    if not report.get('reviewServerReady'):
        raise RuntimeError('Python 3.10 or later is required.')
    if not report.get('excelDependenciesReady'):
        print('Review is available; final Excel saving needs runtime setup: ' + report.get('dependencyMessage', ''), file=sys.stderr)
    if os.name != 'nt':
        print('Local book review is running in this terminal: ' + url, flush=True)
        return subprocess.call([str(python_executable()), '-X', 'utf8', str(server)], cwd=str(data.parent))
    # WMI creates the server under its service, outside the caller's process job.
    # -Command runs trusted local code without changing script execution policy.
    status = start_independent_server()
    for attempt in range(30):
        if ready():
            (data / 'local-review-server-status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
            print('Local book review started: ' + url)
            return 0
        time.sleep(0.2)
    raise RuntimeError(f"Review server was created (PID={status['pid']}) but did not become available at {url}")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print('Local review launch failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
