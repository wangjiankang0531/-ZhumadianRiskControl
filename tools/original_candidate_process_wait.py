"""Keep a single owned-process wait timeout from aborting remaining cleanup."""
import subprocess

def finish_owned_process(process, name):
    result = {}
    if process is not None and process.poll() is None:
        result['own' + name + 'Terminated'] = True
        try:
            process.terminate()
            process.wait(timeout=15)
        except (subprocess.TimeoutExpired, OSError) as error:
            result['own' + name + 'StopErrorType'] = type(error).__name__
            result['failed'] = True
    result['own' + name + 'Exited'] = process is None or process.poll() is not None
    result['own' + name + 'ExitCode'] = process.returncode if process else None
    return result


def validate_previous_database_shutdown(previous, receipt_path):
    import hashlib
    import json
    from pathlib import Path
    assert previous['ownMySQLExited'] and previous['ownMySQLExitCode'] == 0
    assert previous['ownRedisExited']
    if previous['ownRedisExitCode'] == 0:
        return
    root = Path(receipt_path).resolve().parent
    assert Path(receipt_path).name == 'recovery_after_controller_failure.json'
    assert previous.get('recoveredAfterControllerFailure') is True and previous.get('failed') is True
    assert previous.get('controllerShutdownException') == 'TimeoutExpired'
    assert previous.get('allPreviousPIDsAbsent') is True and previous.get('allThreeOwnerLocksAcquiredAndReleased') is True
    assert previous.get('ownRedisExitCode') is None and previous.get('redisExitCodeObserved') is False
    ready = json.loads((root / 'ready.json').read_bytes())
    assert ready['ownerId'] == previous['ownerId'] and ready['ownRedisPID'] == previous['ownRedisPID']
    log = (root / 'redis.private.log').read_bytes()
    assert hashlib.sha256(log).hexdigest() == previous['redisGracefulShutdownLogSHA256']
    assert b'Redis is now ready to exit, bye bye...' in log
