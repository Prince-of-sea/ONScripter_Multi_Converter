from pathlib import Path
import subprocess as sp
import sys, os


#同一階層のパスを変数へ代入
__same_hierarchy = Path(sys.argv[0]).parent

#ファイルパス辞書
requiredfile_locations_dict = {
	#必須
	'GARbro_GUI' : Path(__same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.GUI.exe'),
	'GARBro' : Path(__same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.Console.exe'),
	'smjpeg_encode' : Path(__same_hierarchy / 'tools' / 'smjpeg_encode.exe'),
	'nsaed' : Path(__same_hierarchy / 'tools' / 'nsaed.exe'),

	#'PATH'でもおｋ
	'ffmpeg' : Path(__same_hierarchy / 'tools' / 'ffmpeg.exe'),
	'ffprobe' : Path(__same_hierarchy / 'tools' / 'ffprobe.exe'),
}


################################################################################
def subprocess_args_for_locations(include_stdout=True):
	#subprocessがexe化時正常に動かないときの対策
	# 'utils'から取ってこようとすると相互importになって(?)エラー吐くので仕方なく置いてる
	# なんかいい方法見つけ次第修正予定

	if hasattr(sp, 'STARTUPINFO'):
		si = sp.STARTUPINFO()
		si.dwFlags |= sp.STARTF_USESHOWWINDOW
		env = os.environ
	else:
		si = None
		env = None

	if include_stdout: ret = {'stdout': sp.PIPE}
	else: ret = {}

	ret.update({'stdin': sp.PIPE, 'stderr': sp.PIPE, 'startupinfo': si, 'env': env})
	return ret
################################################################################


def location(key: str) -> Path:
	return requiredfile_locations_dict[key]


def location_env(key: str) -> Path:
	if (requiredfile_locations_dict[key]).exists(): return requiredfile_locations_dict[key]
	else: return key


def location_list(key_list: list) -> list:
	result_list = []
	for k in key_list:
		result_list.append(requiredfile_locations_dict[k])
	return result_list


def exist(key: str) -> bool:
	return bool(requiredfile_locations_dict.get(key).exists())


def exist_env(key: str) -> bool:
	if (requiredfile_locations_dict[key]).exists(): return True
	else:
		try: sp.run(key, **subprocess_args_for_locations(True))
		except: return False
		else: return True


def exist_all(key_list: list) -> bool:
	result_list = []
	for k in key_list:
		result_list.append(bool(requiredfile_locations_dict.get(k).exists()))
	return not (False in result_list)#一個でもFalseがあったらFalse


def exist_list(key_list: list) -> list:
	result_list = []
	for k in key_list:
		result_list.append(bool(requiredfile_locations_dict.get(k).exists()))
	return result_list

#将来的には旧verにあった"何が足りないか"を指定する機能もほしいなって