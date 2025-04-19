#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp
import tempfile
import shutil
import i18n

from requiredfile_locations import location_env
from utils import subprocess_args


def convert_music(f_dict: dict):
    extractedpath = Path(f_dict['extractedpath'])
    convertedpath = Path(f_dict['convertedpath'])

    # ffmpegのパス取得
    ffmpeg_Path = location_env('ffmpeg')

    with tempfile.TemporaryDirectory() as mustemp_dir:
        mustemp_dir = Path(mustemp_dir)
        mustemppath = Path(mustemp_dir / f'_.{f_dict['format']}'.lower())

        match f_dict['format']:
            case 'OGG':
                cmd = [ffmpeg_Path, '-y',
                       '-i', extractedpath,
                       '-vn',
                       '-ab', f'{f_dict['kbps']}k',
                       '-ar', f_dict['hz'],
                       '-ac', f_dict['ch'],
                       '-threads', '1',
                       mustemppath,
                       ]

            case 'MP3':
                cmd = [ffmpeg_Path, '-y',
                       '-i', extractedpath,
                       '-vn',
                       '-ab', f'{f_dict['kbps']}k',
                       '-ar', f_dict['hz'],
                       '-ac', f_dict['ch'],
                       '-cutoff', f_dict['cutoff'],
                       '-threads', '1',
                       mustemppath,
                       ]

            case 'WAV':
                cmd = [ffmpeg_Path, '-y',
                       '-i', extractedpath,
                       '-vn',
                       '-ar', f_dict['hz'],
                       '-ac', f_dict['ch'],
                       '-acodec', f_dict['acodec'],
                       '-threads', '1',
                       mustemppath,
                       ]

            case _: raise ValueError(i18n.t('ui.Audio_format_not_selected'))

        sp.run(cmd, **subprocess_args())
        shutil.move(mustemppath, convertedpath)

    # 元nbz用コビー
    if (f_dict['nbz']) and (str(convertedpath.suffix).lower() != '.nbz'):
        shutil.copy(convertedpath, convertedpath.with_suffix('.nbz'))

    return
