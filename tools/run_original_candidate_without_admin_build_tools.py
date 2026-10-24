"""Process-local Python audit of a fixed candidate controller's prepared admin path.

This is integration evidence, not an OS sandbox or an audit of child JVM reads.
Original admin tar reads and Node/Babel use by this Python chain are rejected.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import runpy
import sys


def normalized(value):
    if isinstance(value, bytes): value = os.fsdecode(value)
    if isinstance(value, os.PathLike): value = os.fspath(value)
    return value.replace('\\', '/').lower() if isinstance(value, str) else ''


def forbidden_file(value):
    value = normalized(value)
    if value.rsplit('/', 1)[-1] == 'dist_new.tar.gz': return 'original-admin-archive'
    if value.rsplit('/', 1)[-1] in {'node', 'node.exe'}: return 'node-executable'
    if '/node_modules/@babel/parser/' in value: return 'babel-parser'
    if value.rsplit('/', 1)[-1] == 'adapt_original_admin_static.mjs': return 'admin-build-recipe'
    return None


def forbidden_command(executable, arguments):
    values = [executable] + (list(arguments) if isinstance(arguments, (list, tuple)) else [arguments])
    for value in values:
        reason = forbidden_file(value)
        if reason: return reason
        text = normalized(value)
        if re.search(r'(?:^|[/\s\"\x27])node(?:\.exe)?(?:$|[\s\"\x27])', text): return 'node-command'
        if '/node_modules/@babel/parser/' in text: return 'babel-parser-command'
    return None


class AdminBuildAudit:
    def __init__(self, report, ready_file, controller_sha):
        self.report = Path(report).absolute(); self.pending = self.report.with_suffix('.pending')
        self.ready_file = normalized(Path(ready_file).absolute())
        self.own_reports = {normalized(self.report), normalized(self.pending)}
        self.state = {'schema': 'xnby.original-admin.python-audit.v1', 'installed': False,
            'controllerSHA256': controller_sha, 'startedAt': datetime.datetime.now().astimezone().isoformat(),
            'openEvents': 0, 'subprocessEvents': 0, 'subprocessExecutableCounts': {}, 'blockedAttempts': [],
            'readyFileOpenObserved': False, 'controllerReturned': False, 'controllerExceptionClass': None,
            'scope': 'this Python controller chain only; not child JVM or operating-system isolation'}

    def snapshot(self, phase):
        self.state.update(phase=phase, observedAt=datetime.datetime.now().astimezone().isoformat())
        self.pending.write_text(json.dumps(self.state, indent=2) + '\n', encoding='utf-8')
        os.replace(self.pending, self.report)

    def reject(self, event, reason):
        self.state['blockedAttempts'].append({'event': event, 'reason': reason})
        self.snapshot('dependency-rejected')
        raise PermissionError('PREPARED_ADMIN_BUILD_DEPENDENCY_REJECTED_' + reason)

    def __call__(self, event, args):
        if event == 'open':
            name = normalized(args[0])
            if name in self.own_reports: return
            self.state['openEvents'] += 1
            reason = forbidden_file(args[0])
            if reason: self.reject(event, reason)
            if name == self.ready_file:
                self.state['readyFileOpenObserved'] = True
                self.snapshot('candidate-ready-file-open-observed')
        elif event == 'subprocess.Popen':
            self.state['subprocessEvents'] += 1
            reason = forbidden_command(args[0], args[1])
            if reason: self.reject(event, reason)
            name = normalized(args[0]).rsplit('/', 1)[-1]
            counts = self.state['subprocessExecutableCounts']; counts[name] = counts.get(name, 0) + 1
            self.snapshot('allowed-child-start-observed')

    def install(self):
        sys.addaudithook(self)
        self.state['installed'] = True
        self.snapshot('installed-before-controller')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path, required=True)
    parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--audit-output', type=Path, required=True)
    args, controller_args = parser.parse_known_args()
    if not controller_args or controller_args.pop(0) != '--': raise ValueError('EXPLICIT_CONTROLLER_ARGUMENT_SEPARATOR_REQUIRED')
    controller = args.controller.resolve(strict=True)
    if controller.name != 'serve_original_integrated_candidate.py' or controller.parent.name != 'tools':
        raise ValueError('EXPLICIT_KNOWN_CANDIDATE_CONTROLLER_REQUIRED')
    if not re.fullmatch('[0-9a-f]{64}', args.controller_sha256) or hashlib.sha256(controller.read_bytes()).hexdigest() != args.controller_sha256:
        raise ValueError('EXPLICIT_CANDIDATE_CONTROLLER_PIN_REQUIRED')
    def option(name):
        if controller_args.count(name) != 1: raise ValueError('EXACT_CONTROLLER_OPTION_REQUIRED_' + name)
        return controller_args[controller_args.index(name) + 1]
    workspace = Path(option('--workspace')).resolve(strict=True); name = option('--name')
    if not re.fullmatch(r'own-j[1-9][0-9]{0,3}', name): raise ValueError('EXPLICIT_UNIQUE_CANDIDATE_NAME_REQUIRED')
    option('--admin-frontend-runtime')
    if not re.fullmatch('[0-9a-f]{64}', option('--admin-frontend-runtime-sha256')):
        raise ValueError('EXPLICIT_PREPARED_ADMIN_SELECTION_REQUIRED')
    report = args.audit_output.absolute()
    if report.exists() or not report.parent.is_dir() or report.parent.resolve() != report.parent or not report.is_relative_to(workspace):
        raise ValueError('FRESH_OWN_AUDIT_REPORT_IN_WORKSPACE_REQUIRED')
    if report.is_relative_to(workspace / name): raise ValueError('AUDIT_REPORT_MUST_NOT_PRECREATE_CONTROLLER_RUNTIME')
    sys.path.insert(0, str(controller.parent)); sys.argv = [str(controller), *controller_args]
    audit = AdminBuildAudit(report, workspace / name / 'ready.json', args.controller_sha256); audit.install()
    try:
        runpy.run_path(str(controller), run_name='__main__')
        audit.state['controllerReturned'] = True
    except BaseException as error:
        audit.state['controllerExceptionClass'] = type(error).__name__
        raise
    finally:
        audit.snapshot('controller-terminal-observed')


if __name__ == '__main__': main()
