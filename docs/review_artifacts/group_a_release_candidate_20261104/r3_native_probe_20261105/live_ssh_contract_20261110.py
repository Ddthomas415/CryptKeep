"""Local argv/configuration contract only; importing never starts SSH."""
SSH = '/usr/bin/ssh'
TARGET = 'cryptkeep@100.86.128.9'
OPTIONS = (
    '-F', '/dev/null', '-T',
    '-o', 'BatchMode=yes', '-o', 'ConnectionAttempts=1',
    '-o', 'ConnectTimeout=210', '-o', 'ServerAliveInterval=0',
    '-o', 'ServerAliveCountMax=3', '-o', 'StrictHostKeyChecking=yes',
    '-o', 'UpdateHostKeys=no', '-o', 'ForwardAgent=no',
    '-o', 'ClearAllForwardings=yes', '-o', 'PermitLocalCommand=no',
    '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
    '-o', 'LogLevel=VERBOSE',
)

def configuration_argv():
    return [SSH, '-G', *OPTIONS, TARGET]

def validate_effective(fields):
    interval = int(fields['serveraliveinterval'])
    count = int(fields['serveralivecountmax'])
    if interval > 0 and interval * count < 210:
        raise ValueError('packet_timeout_shorter_than_approval_window')
    required = {'hostname': '100.86.128.9', 'user': 'cryptkeep',
                'connecttimeout': '210', 'serveraliveinterval': '0',
                'connectionattempts': '1', 'stricthostkeychecking': 'true',
                'updatehostkeys': 'false', 'forwardagent': 'no',
                'batchmode': 'yes', 'controlmaster': 'false', 'loglevel': 'VERBOSE'}
    if any(fields.get(key) != value for key, value in required.items()):
        raise ValueError('live_ssh_contract_mismatch')

def live_argv():
    return ['/usr/bin/perl', '-e', 'alarm 300; exec @ARGV or die "exec failed: $!";',
            '--', SSH, *OPTIONS, TARGET, 'python3 -I -S -B -']
