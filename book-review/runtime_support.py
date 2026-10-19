"""Locate installed Codex runtimes without downloading or copying dependencies."""
from pathlib import Path
import os
import shutil
import subprocess
import sys


def _command(value):
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    found = shutil.which(value)
    return Path(found).resolve() if found else None


def runtime_root():
    return Path.home() / '.cache' / 'codex-runtimes' / 'codex-primary-runtime' / 'dependencies'


def python_executable():
    explicit = os.environ.get('CODEX_PYTHON')
    if explicit:
        result = _command(explicit)
        if not result:
            raise RuntimeError('CODEX_PYTHON does not identify an installed Python executable.')
        return result
    return Path(sys.executable).resolve()


def node_executable():
    explicit = os.environ.get('CODEX_NODE')
    if explicit:
        result = _command(explicit)
        if not result:
            raise RuntimeError('CODEX_NODE does not identify an installed Node.js executable.')
        return result
    for name in ('node.exe', 'node'):
        bundled = runtime_root() / 'node' / 'bin' / name
        if bundled.is_file():
            return bundled.resolve()
    found = _command('node')
    if found:
        return found
    raise RuntimeError('Node.js is unavailable. Set CODEX_NODE to an installed executable.')


def _has_artifact_tool(directory):
    return (directory / '@oai' / 'artifact-tool' / 'package.json').is_file()


def node_modules_directory(root):
    """Find an existing install; CODEX_NODE_MODULES names the node_modules folder."""
    explicit = os.environ.get('CODEX_NODE_MODULES')
    if explicit:
        directory = Path(explicit).expanduser().resolve()
        if not _has_artifact_tool(directory):
            raise RuntimeError('CODEX_NODE_MODULES must contain @oai/artifact-tool/package.json.')
        return directory
    candidates = [Path(root) / 'review-data' / 'node_modules',
                  runtime_root() / 'node' / 'node_modules']
    try:
        node = node_executable()
        candidates += [node.parent / 'node_modules', node.parent.parent / 'node_modules']
    except RuntimeError:
        pass
    for directory in candidates:
        if _has_artifact_tool(directory):
            return directory.resolve()
    raise RuntimeError('Installed @oai/artifact-tool is unavailable. Open this folder in Codex '
                       'and set CODEX_NODE_MODULES to its installed node_modules directory.')


def link_node_modules(root, source):
    """Create one local directory link, never replace an existing file or directory."""
    target = Path(root).resolve() / 'review-data' / 'node_modules'
    source = Path(source).resolve()
    if _has_artifact_tool(target):
        if target.resolve() != source:
            raise RuntimeError('A different node_modules installation already exists; keep it '
                               'or explicitly select it with CODEX_NODE_MODULES.')
        return target
    if os.path.lexists(target):
        raise RuntimeError('review-data/node_modules exists but lacks @oai/artifact-tool. '
                           'No existing dependency directory was changed.')
    target.parent.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        result = subprocess.run([os.environ.get('ComSpec', 'cmd.exe'), '/d', '/c',
                                 'mklink', '/J', str(target), str(source)],
                                capture_output=True, text=True,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise RuntimeError('Could not link installed dependencies: ' + result.stderr.strip())
    else:
        target.symlink_to(source, target_is_directory=True)
    if not _has_artifact_tool(target):
        raise RuntimeError('Dependency link verification failed.')
    return target


def writer_environment(root):
    """Return child process settings, linking already installed dependencies if needed."""
    node = node_executable()
    python = python_executable()
    modules = node_modules_directory(root)
    link_node_modules(root, modules)
    environment = os.environ.copy()
    environment.update(CODEX_NODE=str(node), CODEX_PYTHON=str(python),
                       CODEX_NODE_MODULES=str(modules))
    return node, environment


def inspect_runtime(root, bootstrap=False):
    report = {'projectRoot': str(Path(root).resolve()), 'python': str(python_executable()),
              'reviewServerReady': sys.version_info >= (3, 10),
              'networkUsed': False, 'packagesDownloaded': False}
    try:
        node = node_executable()
        modules = node_modules_directory(root)
        report.update(node=str(node), nodeModules=str(modules), excelDependenciesReady=True)
        if bootstrap:
            report['dependencyLink'] = str(link_node_modules(root, modules))
        else:
            report['dependencyLinkPresent'] = _has_artifact_tool(Path(root) / 'review-data' / 'node_modules')
    except (OSError, RuntimeError) as error:
        report.update(excelDependenciesReady=False, dependencyMessage=str(error))
    report['ready'] = report['reviewServerReady'] and report['excelDependenciesReady']
    return report
