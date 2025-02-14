#!/usr/bin/env python3
import shutil, stat, os


def convert_other(f_dict: dict):
	extractedpath = f_dict['extractedpath']
	convertedpath = f_dict['convertedpath']

	#まぁconvertとか言いつつ移動してるだけなんですけど
	os.chmod(path=extractedpath, mode=stat.S_IWRITE)#念の為読み取り専用を外す
	shutil.move(extractedpath, convertedpath)

	#元nbz用コビー
	if (f_dict['nbz']) and (convertedpath.suffix != '.nbz'): shutil.copy(convertedpath, convertedpath.with_suffix('.nbz'))
	return