#!/usr/bin/env python3
import os
import shutil
import subprocess as sp
from pathlib import Path

import dearpygui.dearpygui as dpg
from requiredfile_locations import location
from utils2 import (
	subprocess_args, #これ書いとけば他から"from utils import subprocess_args"されても普通に動く
)


def message_box(msg_title: str, msg: str, msg_type: str, useGUI: bool):
	if not useGUI:
		return
	with dpg.mutex():
		with dpg.window(label=msg_title, modal=True) as msg_window:
			dpg.add_text(msg)
			dpg.add_button(label="OK", callback=lambda: dpg.configure_item(msg_window, show=False))
	dpg.split_frame()
	dpg.set_item_pos(msg_window, [dpg.get_viewport_client_width() // 2 - dpg.get_item_width(msg_window) // 2, dpg.get_viewport_client_height() // 2 - dpg.get_item_height(msg_window) // 2])
	return


def configure_progress_bar(per: float, msg: str):

	if msg: dpg.set_value('progress_msg', msg)
	dpg.set_value('progress_bar', per)
	dpg.configure_item('progress_bar', overlay='{}%'.format(int(per * 100)))

	return


def extract_archive_garbro(p: Path, e: Path, f: str = ''):
	GARBro_Path = location('GARBro')
	e.mkdir()
	if f: l = [GARBro_Path, 'x', '-if', f.lower(), '-ca', '-o', e, p]
	else: l = [GARBro_Path, 'x', '-ca', '-o', e, p]
	sp.run(l ,shell=True, **subprocess_args())#展開
	return


def openread0x84bitxor(p: Path):
	data = open(p,"rb").read()#復号化前のtxt読み込み用変数
	bin_list = []#復号したバイナリを格納する配列の作成
		
	for b in range(len(data)):#復号 0x84でbitxorしてるんだけどいまいち自分でもよく分かってない
		bin_list.append(bytes.fromhex(str((hex(int(data[b]) ^ int(0x84))[2:].zfill(2)))))
		
	decode_text = (b''.join(bin_list)).decode('cp932', errors='ignore')
	return decode_text


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


def get_dir_size(p):
	t = 0
	for e in os.scandir(p):
		if e.is_file(): t += e.stat().st_size
		elif e.is_dir(): t += get_dir_size(e.path)
	return t


def dir_allmove(input_dir, output_dir):
	#一括チェック
	for input_p in input_dir.glob('**/*'):
		output_p = Path(output_dir / input_p.relative_to(input_dir))

		#保存先ディレクトリ作成
		output_p.parent.mkdir(parents=True, exist_ok=True)

		#移動
		shutil.move(input_p, output_p)
