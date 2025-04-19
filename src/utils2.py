#!/usr/bin/env python3
import subprocess as sp
import os


# requiredfile_locationsの相互importエラー対策でこれだけ隔離

def subprocess_args(include_stdout=True):
    # subprocessがexe化時正常に動かないときの対策

    if hasattr(sp, 'STARTUPINFO'):
        si = sp.STARTUPINFO()
        si.dwFlags |= sp.STARTF_USESHOWWINDOW
        env = os.environ
    else:
        si = None
        env = None

    if include_stdout:
        ret = {'stdout': sp.PIPE}
    else:
        ret = {}

    ret.update({'stdin': sp.PIPE, 'stderr': sp.PIPE,
               'startupinfo': si, 'env': env})
    return ret
