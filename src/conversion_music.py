#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp
import tempfile, shutil

from requiredfile_locations import location_env
from utils import subprocess_args


def convert_music(f_dict: dict):
	extractedpath = f_dict['extractedpath']
	convertedpath = f_dict['convertedpath']

	#ffmpegのパス取得
	ffmpeg_Path = location_env('ffmpeg')

	with tempfile.TemporaryDirectory() as mustemp_dir:
		mustemp_dir = Path(mustemp_dir)
	
		match f_dict['format']:
			case 'OGG':
				mustemppath = (mustemp_dir / 'x.ogg')
				sp.run([ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ab', str(f_dict['kbps']) + 'k',
					'-ar', str(f_dict['hz']),
					'-ac', str(f_dict['ch']), 
					mustemppath,
				], shell=True, **subprocess_args())

			case 'MP3':
				mustemppath = (mustemp_dir / 'x.mp3')
				sp.run([ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ab', str(f_dict['kbps']) + 'k',
					'-ar', str(f_dict['hz']),
					'-ac', str(f_dict['ch']), 
					'-cutoff', str(f_dict['cutoff']),
					mustemppath,
				], shell=True, **subprocess_args())	

			case 'WAV':
				mustemppath = (mustemp_dir / 'x.wav')
				sp.run([ffmpeg_Path, '-y',
					'-i', extractedpath,
					'-vn',
					'-ar', str(f_dict['hz']),
					'-ac', str(f_dict['ch']), 
					'-acodec', f_dict['acodec'],
					mustemppath,
				], shell=True, **subprocess_args())	

			case _: raise ValueError('音声の変換フォーマットが選択されていません')
		
		shutil.move(mustemppath, convertedpath)

	#元nbz用コビー
	if (f_dict['nbz']) and (convertedpath.suffix != '.nbz'): shutil.copy(convertedpath, convertedpath.with_suffix('.nbz'))

	return