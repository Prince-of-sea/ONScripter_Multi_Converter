#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp
import tempfile, shutil

from requiredfile_locations import location_env
from utils import subprocess_args


def convert_music(f_dict: dict):
	extractedpath = Path(f_dict['extractedpath'])
	convertedpath = Path(f_dict['convertedpath'])

	#ffmpegのパス取得
	ffmpeg_Path = location_env('ffmpeg')

	with tempfile.TemporaryDirectory() as mustemp_dir:
		mustemp_dir = Path(mustemp_dir)
		mustemppath = Path(mustemp_dir / 'x.{}'.format(f_dict['format']).lower())
	
		match f_dict['format']:
			case 'OGG':
				cmd = [ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ab', '{}k'.format(f_dict['kbps']),
					'-ar', f_dict['hz'],
					'-ac', f_dict['ch'], 
					mustemppath,
				]

			case 'MP3':
				cmd = [ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ab', '{}k'.format(f_dict['kbps']),
					'-ar', f_dict['hz'],
					'-ac', f_dict['ch'], 
					'-cutoff', f_dict['cutoff'],
					mustemppath,
				]

			case 'WAV':
				cmd = [ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ar', f_dict['hz'],
					'-ac', f_dict['ch'], 
					'-acodec', f_dict['acodec'],
					mustemppath,
				]

			case _: raise ValueError('音声の変換フォーマットが選択されていません')
		
		sp.run(cmd, **subprocess_args())
		shutil.move(mustemppath, convertedpath)

	#元nbz用コビー
	if (f_dict['nbz']) and (str(convertedpath.suffix).lower() != '.nbz'): shutil.copy(convertedpath, convertedpath.with_suffix('.nbz'))

	return