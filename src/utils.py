#!/usr/bin/env python3
import sys, os
import shutil
import subprocess as sp
from pathlib import Path

import dearpygui.dearpygui as dpg
from requiredfile_locations import location
from process_notons import get_titledict
from utils2 import (
	subprocess_args, #これ書いとけば他から"from utils import subprocess_args"されても普通に動く
)


def value_setting_update(values_default, value_setting):

	if value_setting:
		
		for s in value_setting.split(';'):
			try:
				k, v = s.split('=')
				if type(values_default[k]) == bool: v = strtobool(v)
				values_default[k] = type(values_default[k])(v)
				print(f'SUCCESS: Updated value of {k} to {v}')

			except: print(f'WARNING: Error in value_setting "{s}"')

	return values_default


def strtobool(val):
	# 参考: https://note.nkmk.me/python-bool-true-false-usage/#1-0-distutilsutilstrtobool
	val = val.lower()
	if val in ('y', 'yes', 't', 'true', 'on', '1'): return True
	elif val in ('n', 'no', 'f', 'false', 'off', '0'): return False
	else: raise ValueError('')


def get_meipass(p: Path):
	if hasattr(sys, '_MEIPASS'): base_dir =  Path(sys._MEIPASS)
	else: base_dir = Path('.')
	base_path = Path(base_dir / p)
	return base_path


def get_titlesettingfull(param: str):
	title_setting = 'None'
	for k,v in get_titledict().items():
		if (param == v['cli_arg']):
			title_setting = k
			break
	
	return title_setting


def message_box(msg_title: str, msg: str, msg_type: str, useGUI: bool):

	if useGUI:		
		with dpg.mutex():
			with dpg.window(label=msg_title, modal=True) as msg_window:
				dpg.add_text(msg)
				dpg.add_button(label='OK', callback=lambda: dpg.configure_item(msg_window, show=False))
		dpg.split_frame()
		dpg.set_item_pos(msg_window, [dpg.get_viewport_client_width() // 2 - dpg.get_item_width(msg_window) // 2, dpg.get_viewport_client_height() // 2 - dpg.get_item_height(msg_window) // 2])

	else:
		print(f'{msg_type}: {msg}')

	return


def configure_progress_bar(per: float, msg: str, useGUI: bool):
	if useGUI:
		if msg: dpg.set_value('progress_msg', msg)
		dpg.set_value('progress_bar', per)
		dpg.configure_item('progress_bar', overlay=f'{int(per * 100)}%')

	elif msg:
		print(f'message: {msg} [{int(per * 100)}/100]')

	return


def extract_archive_garbro(p: Path, e: Path, f: str = ''):
	GARbro_Path = location('GARbro')
	e.mkdir()
	if f: l = [GARbro_Path, 'x', '-if', f.lower(), '-ca', '-o', e, p]
	else: l = [GARbro_Path, 'x', '-ca', '-o', e, p]
	sp.run(l , **subprocess_args())#展開
	return


def openread0x84bitxor(p: Path, charset: str = 'cp932'):
	data = open(p,'rb').read()#復号化前のtxt読み込み用変数
	bin_list = []#復号したバイナリを格納する配列の作成
		
	for b in range(len(data)):#復号 0x84でbitxorしてるんだけどいまいち自分でもよく分かってない
		bin_list.append(bytes.fromhex(str((hex(int(data[b]) ^ int(0x84))[2:].zfill(2)))))
		
	decode_text = (b''.join(bin_list)).decode(charset, errors='ignore')
	return decode_text


def lower_AtoZ(s: str):

	#アルファベット小文字変換
	alphabet_upper = ''.join([chr(i) for i in range(65, 91)])#AからZ
	alphabet_lower = ''.join([chr(i) for i in range(97, 123)])#aからz
	s = s.translate(str.maketrans(alphabet_upper, alphabet_lower))#大文字→小文字変換

	return s


def format_check(filepath: Path):

	#念の為
	filepath = Path(filepath)

	#拡張子読み込み(ヘッダだけだと分けきれないことがあるので)
	filesuffix = str(filepath.suffix).lower()

	with open(filepath, 'rb') as f:
		b = f.read(12)

		if   ( b[: 4] == b'\xFF\xD8\xFF\xDB'
		) or ( b[:12] == b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01'
		) or ( b[: 4] == b'\xFF\xD8\xFF\xEE'
		) or ((b[: 4] == b'\xFF\xD8\xFF\xE1') and (b[ 6:] == b'\x45\x78\x69\x66\x00\x00')
		) or ( b[: 4] == b'\xFF\xD8\xFF\xE0'):
			ff = 'JPEG'

		elif ( b[: 2] == b'\x42\x4D'):
			ff = 'BMP'

		elif ( b[: 8] == b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
			ff = 'PNG'

		elif ((b[: 4] == b'\x52\x49\x46\x46') and (b[ 8:] == b'\x57\x41\x56\x45')):
			ff = 'WAV'

		elif ( b[: 4] == b'\x4F\x67\x67\x53'):
			if (filesuffix == '.ogv'): ff = 'OGV'#精密な判定めんどい(毎回ffprobe使う羽目になる)ので拡張子で
			else: ff = 'OGG'

		elif ( b[: 2] == b'\xFF\xFB'
		) or ( b[: 2] == b'\xFF\xF3'
		) or ( b[: 2] == b'\xFF\xF2'
		) or ( b[: 3] == b'\x49\x44\x33'):
			ff = 'MP3'
		
		elif ( b[: 8] == b'\x66\x74\x79\x70\x69\x73\x6F\x6D'
		) or ( b[: 8] == b'\x66\x74\x79\x70\x4D\x53\x4E\x56'):
			ff = 'MP4'

		elif ( b[: 4] == b'\x00\x00\x01\xBA'
		) or ( b[: 4] == b'\x00\x00\x01\xB3'):
			ff = 'MPEG'
		
		elif ((b[: 4] == b'\x52\x49\x46\x46') and (b[ 8:] == b'\x41\x56\x49\x20')):
			ff = 'AVI'

		else:
			if (filesuffix == '.mp3'): ff = 'MP3'#拡張子mp3なら多分mp3だろ(あきらめ)
			else: ff = False

	return ff


def dir_allmove(input_dir, output_dir):
	#一括チェック
	for input_p in input_dir.glob('**/*'):
		output_p = Path(output_dir / input_p.relative_to(input_dir))

		#保存先ディレクトリ作成
		output_p.parent.mkdir(parents=True, exist_ok=True)

		#移動
		shutil.move(input_p, output_p)
