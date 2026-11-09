"""Checkpoint helpers used by long-running validation jobs."""
import re
import subprocess


def remaining_steps(target, checkpoint):
    """GROMACS -nsteps applies after the checkpoint's initial step."""
    if target < 0 or checkpoint < 0:
        raise ValueError('Step counts must be nonnegative')
    return max(0, target - checkpoint)


def checkpoint_step(command, env):
    """Read only the checkpoint header, avoiding a huge coordinate dump."""
    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True,
                               encoding='utf-8', errors='replace')
    try:
        for line in process.stdout:
            match = re.match(r'^step\s*=\s*(\d+)\s*$', line)
            if match:
                return int(match.group(1))
        raise RuntimeError('Could not read checkpoint step')
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
