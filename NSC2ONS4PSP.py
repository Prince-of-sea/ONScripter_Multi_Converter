#!/usr/bin/env python3
# windows only
import base64
import concurrent.futures
import json
import math
import os
import re
import shutil
import stat
import subprocess as sp
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path

import mozjpeg_lossless_optimization as mozj
import numpy as np
import zopfli as zf
from PIL import Image

from GUI import gui_main, gui_msg

####################################################################################################

# -memo-
# jsonでの作品個別処理何も実装してねぇ... - v1.3.0で実装予定だった - 現在未実装orz

# -最新の更新履歴(v1.4.8)-
# 🚚 toolsディレクトリを整理
# ♻️ GUIの部分だけ別ファイルに
# 
# 機能的には変更なし
# PC-CNT氏に手伝ってもらいました

# これを読んだあなた。
# どうかこんな可読性の欠片もないクソコードを書かないでください。
# それだけが私の望みです。

######################################## subprocessがexe化時正常に動かんときの対策 ########################################
# 以下のサイトのものを使わせてもらってます
# https://qiita.com/nonzu/pxs/b4cb0529a4fc65f45463
def subprocess_args(include_stdout=True):
	if hasattr(sp, 'STARTUPINFO'):
		si = sp.STARTUPINFO()
		si.dwFlags |= sp.STARTF_USESHOWWINDOW
		env = os.environ
	else:
		si = None
		env = None

	if include_stdout: ret = {'stdout': sp.PIPE}
	else: ret = {}

	ret.update({'stdin': sp.PIPE,
				'stderr': sp.PIPE,
				'startupinfo': si,
				'env': env })
	return ret



def get_cur_dictlist():
		#-----カーソル画像(容量削減のためpng変換済)をbase64にしたものを入れた辞書作成-----
	cur_dictlist = [
		{#ONSforPSP向けカーソル(大)
			'cursor0' :r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPAgMAAAANEK40AAAACVBMVEX+Af4BAQH+/v4EXGBQAAAAQ0lEQVR4AWMQYEACqkAMF9AKQBJQWQoVAHO4AqACIA7DUqgAmMMVABUAcRiWAAUcVBiWoMkg9KCZhrAHxQXobkNxNQDgyRHjcXthuQAAAABJRU5ErkJggg==',
			'cursor1' :r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPAgMAAAANEK40AAAADFBMVEX+Af7+/v4BAQEAAACZSqvyAAAAW0lEQVR4AWJAAaGhDgg6AdChHNsACMUwEDXrMA0FKX8Dygj0WYcsRMUoCDinuSfFWoCrvFeDausAlNlUgCqPUYD+79OgfgOqvIZBtb+PQT0DVBFhUM3dBhUH6AdM5TrA8UycDgAAAABJRU5ErkJggg==',
			'doffcur' :r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAOUlEQVR4Aa3KsRUAEADEULe6vSEdAJCX8hsvb/eSdK55h8KuNC/pg+YJfdY8oc+aW/pPc05/6y7lCCihdDnxHWpgAAAAAElFTkSuQmCC',
			'doncur'  :r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAANklEQVR4AazKsQEAEAAAIP1/M+wAaC4kaRMutq2apLttXV+2RX3cZvV9a+rXrak/dxlEKSYCAGqKArAfIzK1AAAAAElFTkSuQmCC',
			'uoffcur' :r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAPUlEQVR4Aa3KhQ1CAQBDQW717g18d5eXxpr7/PyWS4Ll/1inC6/qTMNLOmvhsc52eKBzFG7pnAvXdTnnKgDBvFyBNGOuowAAAABJRU5ErkJggg==',
			'uoncur'  :r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAPklEQVR4Aa3KhQGAMADAMPL/zbj7tDBP0+me/xie9+V6C1X1LVTSr6FY/4QC3YfCocdi9XhYdPcb0vX4i2sANT3rNNe5to0AAAAASUVORK5CYII=',
		},
		{#ONSforPSP向けカーソル(小)
			'cursor0':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAU0lEQVR4AcXU0QkAIQzAULP/zuEmkEAPLPj/UtQeERBfniOqQNqDvlC17VlfzCphz/tCxbCnfaGG/a/vqt5sMfvE7Nufde9eF97wyn9d2E0Le/gDfvymHqJYAJkAAAAASUVORK5CYII=',
			'cursor1':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAcElEQVR4AcWQAQbAQBADd///51NKIGKEo40oyk2ymbPne/+YGrV3jrLU3Q1vepYbmJb6amaI2PcDpt260pE8o++HTF+YL+v7MTMtrC+z+D8z08ISs7gfM28X5n68cNbNwiClqnsQsaAfM5Xau+2HfgDZDaj6N8Tv0wAAAABJRU5ErkJggg==',
			'doffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAM0lEQVR4AaXKwRUAEACAUK1ub+gMQK/jD5kcdwE3ztdIcOl8gZ6cD9GH8x79Oe/Rn+uRV3DDFOu8xuq5AAAAAElFTkSuQmCC',
			'doncur' :r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAL0lEQVR4AaXKsREAEAAEMNl/5z89AKlTIlu4ejYpcvus0tszTc9Pn36fLv2+PkUqsdF9i/bqJEIAAAAASUVORK5CYII=',
			'uoffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAANUlEQVR4AZXKuQ0AMADCwHh19s5fusOiQjcWS0sC6Gyc0M+0dEKmvTMy7ZyRaefiHNC4O5w7fgoBJ7Twmi8AAAAASUVORK5CYII=',
			'uoncur' :r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAANklEQVR4AaXKhQ3AQAADsXr/mctMz1ZE0XWD4bUZXmdtd0Jz94KG7hfqujAUdmMKli7p6AxSJjVLaeiYxu8vAAAAAElFTkSuQmCC',
		},
		{#NScripter付属 公式カーソル
			'cursor0':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAIAAADWASznAAAAl0lEQVR4AWL4x/iPEQyAjOGEQB4DA6j3hp/HqOO9wRP/gHbsEAcAEIZi6P1vjcdUPLXkJ+hB+wnAPjDHgwrhCLaip8cVwFGA+eIkf3cUYFKX8ndHAQZ4nj85CjDA8/zJUYABnudvjgKs5otZPX9xFGAxfrZeTQpyRwM7tRV3eFw47ndBX3hS7RF84duyj+bd1sCaOYF0dDzSFWKiYdvwAQAAAABJRU5ErkJggg==',
			'cursor1':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAIAAADWASznAAAAuUlEQVR4Ae2SAQbFQBQD/7v/nddHETCsEatqI2gVb5Lmt2Z90jfYu3yD7WqO24Il2Mxs3GijsBUYBOswlTqyYPDHhrWiIgrbg4kpRkUUtAfjKeaV6y+ikD2Ym2Ju9FDAFgymiM4BDlbqyIMl2Gav+QrB2h15sOEpsoim25EGc1OMOVinIw2GU4y4cqCpduTB+lP0KH6Kd4rwfHyKGqw/xXpHDHanKHRmikIJ9niUiigUe4QSrGnfUdF/OeND+SWrDuIAAAAASUVORK5CYII=',
			'doffcur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAATUlEQVR4Aa3MORWAAADFML51fHMqyNK+zjnu3ck/dCK3LYVkWfmEFoJlpYZgUekhWFR6SJaVHqIFpYdoQekhWlB6iBaUHqIFpYcwle8XVsfRQJCtfnsAAAAASUVORK5CYII=',
			'doncur' :r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAASElEQVR4Ab3MwQ0AMAjDQLz/zlFHiCgQy+8roZVLaB6wCzFVhNYhRsoRxKdyCtFWAhANJQbRUGIQXslDeCUP4ZU8hFfyEF4RehVZUP4nhUDMAAAAAElFTkSuQmCC',
			'uoffcur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAATUlEQVR4Ab3MuQ3AMBDAsNzq3jv/AmwEC6p5XHMlG1p/M7MVgmKrh6jQ6iEosHoICqweggKrh6DA6iEotHpIiq0csmKrhpazlULv49ADQ7envrPgz34AAAAASUVORK5CYII=',
			'uoncur' :r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAASElEQVR4Ac3MtRHAQADAsGj/mcNNGB99rtV0uii/gOZQCbQKxaFDKAhdhBLQfcgLvQm5oPchA/QxpIT+hTRQSIgNhYe4kE5wA44DJ3zWlVpmAAAAAElFTkSuQmCC',
		},
	]#すとーむ氏に怒られたら消します(爆)
	return cur_dictlist



def start_check(same_hierarchy):
	
	#起動時必要なファイルリスト
	start_file_list = [
		Path(same_hierarchy / 'tools' / 'nsaed.exe'),
		Path(same_hierarchy / 'tools' / 'smjpeg_encode.exe'),
		Path(same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.Console.exe')
	]

	#ffmpeg/probe/pngquantは別で存在チェック
	try: sp.run('ffmpeg', **subprocess_args(True))
	except: ffmpeg_exist = False
	else: ffmpeg_exist = True

	try: sp.run('ffprobe', **subprocess_args(True))
	except: ffprobe_exist = False
	else: ffprobe_exist = True

	try: sp.run('pngquant', **subprocess_args(True))
	except: pngquant_exist = False
	else: pngquant_exist = True

	#エラーメッセージ作成
	errmsg = ''

	if not ffmpeg_exist: errmsg += 'ffmpeg.exeが見つかりません\n'
	if not ffprobe_exist: errmsg += 'ffprobe.exeが見つかりません\n'
	if not pngquant_exist: errmsg += 'pngquant.exeが見つかりません\n'
		
	for f in start_file_list:
		if not f.exists(): errmsg += ( str(f.relative_to(same_hierarchy)) + 'が用意されていません\n')
	
	if (os.name != 'nt'): errmsg += 'Windows以外で起動しています'
	return errmsg



def scenario_check(path_input_dir):

	path_00txt = Path(path_input_dir / '00.txt')
	path_0txt  = Path(path_input_dir / '0.txt')
	path_nsdat = Path(path_input_dir / 'nscript.dat')

	if path_00txt.exists() or path_0txt.exists():
		text = ''
		if path_00txt.exists():
			for i in range(0, 100):
				range_path = Path(path_input_dir / (str(i).zfill(2) + '.txt'))
		
				if range_path.exists():				
					text += open(range_path, 'r', errors='ignore').read()
					text += '\n\n;##\n;{} end\n;##\n\n'.format(str(range_path.name))	
		
		else:
			for i in range(0, 10):
				range_path = Path(path_input_dir / (str(i) + '.txt'))

				if range_path.exists():				
					text += open(range_path, 'r', errors='ignore').read()
					text += '\n\n;##\n;{} end\n;##\n\n'.format(str(range_path.name))

	elif path_nsdat.exists():
		data = open(path_nsdat,"rb").read()#復号化前のtxt読み込み用変数
		bin_list = []#復号したバイナリを格納する配列の作成
		
		for b in range(len(data)):#復号 0x84でbitxorしてるんだけどいまいち自分でもよく分かってない
			bin_list.append(bytes.fromhex(str((hex(int(data[b]) ^ int(0x84))[2:].zfill(2)))))
		
		text = (b''.join(bin_list)).decode('cp932', errors='ignore')

	else:
		text = ''

	return text



def in_out_dir_check(input_dir, output_dir):
	
	#エラーメッセージ作成
	errmsg = ''
	
	#output_dirと表記を合わせるためあえてtemp_dir未使用
	if not input_dir: errmsg = '入力先が指定されていません'
	elif Path(input_dir).exists() == False: errmsg = '入力先が存在しません'

	elif not output_dir: errmsg = '出力先が指定されていません'
	elif Path(output_dir).exists() == False: errmsg = '出力先が存在しません'

	elif input_dir in output_dir: errmsg = '入出力先が競合しています'
	
	return errmsg



def zero_txt_check(text):
	errmsg = ''

	##### 解像度抽出(&置換) #####
	newnsc_mode = (r'(\r|\n|\t|\s)*?;\$V[0-9]{1,}G([0-9]{1,})S([0-9]{1,}),([0-9]{1,})L[0-9]{1,}')#ONS解像度新表記
	newnsc_search = re.search(newnsc_mode, text)
	oldnsc_mode = (r';mode([0-9]{3})')#ONS解像度旧表記
	oldnsc_search = re.search(oldnsc_mode, text)

	noreschk = bool(r'<ONS_RESOLUTION_CHECK_DISABLED>' in text)#解像度無視変換

	if newnsc_search:#ONS解像度新表記時
		newnsc_width = int(newnsc_search.group(3))
		newnsc_height = int(newnsc_search.group(4))

		#解像度&比率判定 - PSPでは新表記読めないのでついでに置換処理
		if (newnsc_width in [800, 640, 400, 320] and newnsc_width == newnsc_height/3*4) or (noreschk):
			if (newnsc_width == 640) or (noreschk): text = re.sub(newnsc_mode, r';value\2', text, 1)#640x480 or 解像度無視変換時
			else: text = re.sub(newnsc_mode, r';mode\3,value\2', text, 1)#通常時
			game_mode = newnsc_width#作品解像度を代入

		else:
			game_mode = 0
			errmsg = '解像度の関係上このソフトは変換できません'

	elif oldnsc_search:#ONS解像度旧表記時
		game_mode = int(oldnsc_search.group(1))#作品解像度を代入

	else:#ONS解像度無表記時
		game_mode = 640#作品解像度を代入

	#*defineがない時
	if not re.search(r'\*define', text):
		errmsg = '0.txtの復号化に失敗しました'

	return noreschk, game_mode, errmsg, text



def zero_txt_conv(text, per, values, default_transmode):

	#-PSPで使用できない命令を無効化する- (ここ将来的に変数定義上書きとかで消したいよね)
	text = re.sub(r'savescreenshot2?[\t\s]+"(.+?)"[\t\s]*([:|\n])', r'wait 0\2', text)#savescreenshot抹消(PSPだとクソ重いしほぼ確実に取得サイズずれるし...)
	text = re.sub(r'([\n|\t| |:])avi[\t\s]+"(.+?)",([0|1]|%[0-9]+)', r'\1mpegplay "\2",\3', text)#aviをmpegplayで再生(後に拡張子偽装)
	text = re.sub(r'([\n|\t| |:])okcancelbox[\t\s]+%(.+?),', r'\1mov %\2,1 ;', text)#okcancelboxをmovで強制ok
	text = re.sub(r'([\n|\t| |:])yesnobox[\t\s]+%(.+?),', r'\1mov %\2,1 ;', text)#yesnoboxをmovで強制yes
	text = re.sub(r'\n[\t\s]*ns[2|3][\t\s]*\n', r'\nnsa\n', text)#ns2/ns3命令は全部nsaへ

	#nbz
	text = text.replace('.NBZ', '.wav')#大文字
	text = text.replace('.nbz', '.wav')#小文字

	if values['sw_txtsize']:#setwindow文字拡大処理

		#-txt内のsetwindow命令を格納-
		#[0]命令文前部分/[2]横文字数/[3]縦文字数/[4]横文字サイズ/[5]縦文字サイズ/[6]横文字間隔/[7]縦文字間隔/[8]命令文後部分
		setwindow_re_tup = re.findall(r'(setwindow3? ([0-9]{1,},){2})([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),(([0-9]{1,},){3}(.+?)(,[0-9]{1,}){2,4})', text)

		for v in set(setwindow_re_tup):
			txtmin = math.ceil(10 / per)
			nummin = min(int(v[4]), int(v[5]))
			if txtmin > nummin:#表示時10pxを下回りそうな場合 - ちなみに10pxはMSゴシックで漢字が潰れない最低サイズ

				#文字の縦横サイズが違う可能性を考え別に処理 - もちろん縦横比維持
				v4rp = str( int( txtmin * ( int(v[4]) / nummin ) ) )#横文字サイズ(拡大)
				v5rp = str( int( txtmin * ( int(v[5]) / nummin ) ) )#縦文字サイズ(拡大)
				v6rp = str( int( int(v[6]) * ( nummin / int(v4rp) ) ) )#横文字間隔(縮小)
				v7rp = str( int( int(v[7]) * ( nummin / int(v5rp) ) ) )#縦文字間隔(縮小)

				#横に表示できる最大文字数を(文字を大きくした分)減らす - 見切れるのを防ぐため縦はそのまま
				#v2rp = str( int( int(v[2]) * ( int(v[4]) + int(v[6]) ) / ( int(v4rp) + int(v6rp) ) ) )

				sw = (v[0] + v[2] +','+ v[3] +','+ v[4] +','+ v[5] +','+ v[6] +','+ v[7] +','+ v[8])
				sw_re = (v[0] + v[2] +','+ v[3] +','+ v4rp +','+ v5rp +','+ v6rp +','+ v7rp +','+ v[8])
				
				text = text.replace(sw, sw_re)

	#-txt内の画像の相対パスを格納-

	#画像表示命令抽出
	#[0]が命令文/[3]が(パスの入っている)変数名/[5]が透過形式/[6]が分割数/[8]が相対パス - [3]か[8]はどちらかのみ代入される
	immode_dict_tup  = re.findall(r'(ld)[\t\s]+([lcr])[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")[\t\s]*,[\t\s]*[0-9]+', text)#ld
	immode_dict_tup += re.findall(r'((abs)?setcursor)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', text)#setcursor系
	immode_dict_tup += re.findall(r'(lsp(h)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', text)#lsp系
	immode_dict_tup += re.findall(r'(lsph?2(add|sub)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")(([\t\s]*,[\t\s]*((-?[0-9]{1,3})|(%.+?))){1,6})?', text)#lsp2系

	#変数に画像表示命令用の文字列突っ込んである場合があるのでそれ抽出
	#[0]が命令文/[1]が変数名/[3]が透過形式/[4]が分割数/[6]が相対パス
	immode_var_tup = re.findall(r'(stralias|mov)[\t\s]*(\$?[A-Za-z0-9_]+?)[\t\s]*,[\t\s]*"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)"', text)#パスの入ったmov及びstralias
	
	#画像状態保存用辞書作成
	immode_dict = {
		#カーソル類は最初から書いとく
		Path(r'cursor0.bmp'):{'cursor': True, 'trans': 'l', 'part': 3},
		Path(r'cursor1.bmp'):{'cursor': True, 'trans': 'l', 'part': 3},
		Path(r'doncur.bmp'):{'cursor': True, 'trans': 'l', 'part': 1},
		Path(r'doffcur.bmp'):{'cursor': True, 'trans': 'l', 'part': 1},
		Path(r'uoncur.bmp'):{'cursor': True, 'trans': 'l', 'part': 1},
		Path(r'uoffcur.bmp'):{'cursor': True, 'trans': 'l', 'part': 1},	
	}

	for l in immode_dict_tup:
		p = ''

		if ( bool(l[8]) and (not r'$' in l[8]) ):
			p = l[8]

		elif ( bool(l[3]) and (not r'$' in l[3]) ):
			p = l[3]

		if p:
			#カーソルかどうか
			cursor = bool(r'setcursor' in l[0])

			#透過モード
			trans = l[5] if bool(l[5]) else default_transmode

			#表示時画像分割数
			part = int(l[6]) if bool(l[6]) else 1

			immode_dict[Path(p)] = {
				'cursor': cursor,
				'trans': trans,
				'part': part,	
			}

	for l in immode_var_tup:
		p = ''
		if ( bool(l[6]) and (not r'$' in l[6]) ):
			p = l[6]

		if p:
			#透過モード
			trans = l[3] if bool(l[3]) else default_transmode

			#表示時画像分割数
			part = int(l[4]) if bool(l[4]) else 1

			immode_dict[Path(p)] = {
				'cursor': False,
				'trans': trans,
				'part': part,	
			}
	
	#音楽抽出
	msc_list = []#txt内の音源の相対パスを格納するための配列
	for a in re.findall(r'(bgm|mp3loop)[\t\s]+"(.+?)"', text):#txt内の音源の相対パスを格納
		msc_list.append(Path(a[1]))
	
	#動画変換処理を行う - 現時点で動画はヘッダで判別できないので仕方なく命令文抽出で判断
	vid_list = []#txt内の動画の相対パスを格納するための配列
	for a in re.findall(r'mpegplay[\t\s]+"(.+?)",([0|1]|%[0-9]+)', text):#txt内の動画の相対パスを格納
		vid_list.append(Path(a[0]))

	#重複除去
	msc_list = set(msc_list)
	vid_list = set(vid_list)

	return text, immode_dict, vid_list, msc_list



def arc_extract(GARbro_path, p, e):
	e.mkdir()
	sp.run([GARbro_path, 'x', '-ca', '-o', e, p] ,shell=True, **subprocess_args(True))#展開
	return



def func_video_conv(f, values, noreschk, res, same_hierarchy, temp_dir, ex_dir):
	smjpeg_path = Path(same_hierarchy / 'tools' / 'smjpeg_encode.exe')
	
	vid_res = (str(res) + r':' + str(int(res/4*3))) if (not noreschk) else r'480:272'#引数用動画解像度代入
	vid_tmp = (temp_dir / 'no_comp' / Path(str(f.relative_to(ex_dir))+'.mpg'))
	vid_result = (temp_dir / 'no_comp' / f.relative_to(ex_dir))

	#保存先作成
	vid_result.parent.mkdir(parents=True,  exist_ok=True)

	if not f.exists():#パスのファイルが実際に存在するかチェック
		return#なければ終了
	
	with tempfile.TemporaryDirectory() as vidtmpdir:#一時ディレクトリ作成
		vidtmpdir = Path(vidtmpdir)

		vid_info_txt = sp.check_output([#動画情報を代入
			'ffprobe', '-hide_banner',
			'-v', 'error', '-print_format',
			'json', '-show_streams',
			'-i', f,
		],text=True, shell=True, **subprocess_args(False))#check_output時はFalse 忘れずに
		vid_info = json.loads(vid_info_txt)

		#fpsの上2桁を抽出(fpsが小数点の際たまに暴走して299700fpsとかになるので)& "/1" 削除
		vid_frame = (vid_info['streams'][0]['r_frame_rate'].replace('/1', ''))[:2]

		#(横幅/2の切り上げ)*2でfpsを偶数へ
		vid_frame = math.ceil(int(vid_frame)/2)*2#だって奇数fpsの動画なんてまず無いし...
		vid_codec = (vid_info['streams'][0]['codec_name'])#コーデック取得

		#-展開前にPSPの再生可能形式(MPEG-1か2)へ-
		if vid_codec == 'mpeg2video' or vid_codec == 'mpeg1video':#判定
			shutil.copy(f,vid_tmp)#そのまま再生できそうならコピー
			os.chmod(path=vid_tmp, mode=stat.S_IWRITE)#念の為読み取り専用を外す
		else:
			sp.run(['ffmpeg', '-y',#そのまま再生できなそうならエンコード
				'-i', f,
				'-vcodec', 'mpeg2video',
				'-qscale', '0',
				str(vid_tmp),
			], shell=True, **subprocess_args(True))

		#-連番画像展開-
		sp.run(['ffmpeg', '-y',
			'-i', str(vid_tmp),
			'-s', str(vid_res),
			'-r', str(vid_frame),
			'-qscale', str(int(51-int(values['jpg_quality_2'])/2)),#JPEG品質指定を動画変換時にも適応
			str(vidtmpdir) + '/%08d.jpg',#8桁連番
		], shell=True, **subprocess_args(True))

		#-音源抽出+16bitPCMへ変換-
		try:
			sp.run(['ffmpeg', '-y',
				'-i', (vid_tmp),
				'-f', 's16le',#よく考えるとなんで16bitPCMなんだろう
				'-vn',
				'-ar', '44100',
				'-ac', '2',
				str(vidtmpdir) + '/audiodump.pcm',
			], shell=True, **subprocess_args(True))
		except:
			pass#エラー時飛ばす(無音源動画対策)

		vid_tmp.unlink(missing_ok=True)#変換前動画が変換後動画と競合しないようここで削除

		#-抽出ファイルをsmjpeg_encode.exeで結合-
		sp.run([str(smjpeg_path),
		 '--video-fps', str(vid_frame),#小数点使用不可
		 '--audio-rate', '44100',
		 '--audio-bits', '16',
		 '--audio-channels', '2',
		], shell=True, cwd=vidtmpdir, **subprocess_args(True))

		shutil.move((vidtmpdir / r'output.mjpg'), vid_result)#完成品を移動
	
	return



def func_image_conv(f, fc, values, def_trans, immode_dict, noreschk, per, temp_dir, ex_dir, nsa_save_image):
	img_result = (temp_dir / nsa_save_image / f.relative_to(ex_dir))

	#保存先作成
	img_result.parent.mkdir(parents=True,  exist_ok=True)

	try: img = Image.open(f)#画像を開く
	except: return#失敗したら終了

	#画像ではない場合(=画像のフォーマットが存在しない場合)終了 - 拡張子偽装対策
	if img.format == False: return

	#αチャンネル付き&非RGBAな画像をRGBAへ変換
	if ('transparency' in img.info): img = img.convert('RGBA')
	
	#その他RGBじゃない画像をRGB形式に(但しRGBAはそのまま)
	elif (not img.mode == 'RGB') and (not img.mode == 'RGBA'): img = img.convert('RGB')	

	result_width = round(img.width*per)#変換後サイズを指定 - 横
	result_height = round(img.height*per)#変換後サイズを指定 - 縦

	#縦/横幅指定が0以下の時1に - 流石に1切ると変換できないので
	if result_width < 1: result_width = 1
	if result_height < 1: result_height = 1

	#解像度無視変換時、縦270pxは強制的に272px判定
	if (noreschk and result_height == 270): result_height = 272
	
	a_px = (0, 0, 0)#背景画素用仮変数
	img_mask = False#マスク用仮変数

	#---設定生成---
	if f.relative_to(ex_dir) in immode_dict.keys(): img_d = immode_dict[f.relative_to(ex_dir)]#すでに辞書にある場合 - 取ってくるだけ

	else:
		#ない場合
		img_d = {
			'cursor': False,
			'trans': def_trans,
			'part': int(values['img_multi'])
		}

	#それっぽい名前の場合カーソル扱い - たまに「カーソルをsetcursorで呼ばない」作品とかあるのでそれ対策
	for n in ['cursor', 'offcur', 'oncur']:
		if n in str(f.stem): img_d['cursor'] = True
	
	#---カーソル専用処理---
	if img_d['cursor']:
		#---画素比較のためnumpyへ変換---
		np_img = np.array(img.convert('RGB'))

		#---for文で標準画像とそれぞれ比較---
		cur_dictlist = get_cur_dictlist()
		for k, v in cur_dictlist[2].items():

			img_default = Image.open(BytesIO(base64.b64decode(v)))
			np_img_default = np.array(img_default.convert('RGB'))
				
			#カーソルが公式の画像と同一の時
			if np.array_equal(np_img, np_img_default): img_d['default_cursor'] = k
	
	#---(leftup/rightupのみ)背景色を抽出しそこからマスク画像を作成---
	if (img_d['cursor']) and (img_d['trans'] in ['l', 'r']) and (not img_d.get('default_cursor')) and (not img.mode == 'RGBA'):
		#これキレイだけどガチで重いんで基本カーソル専用!!!!
		#透過背景を灰色っぽくすることで縮小時に画像周りの色を目立たなくする

		img = img.convert('RGB')#編集のためまず強制RGB化
		img_datas = img.getdata()#画像データを取得

		if img_d['trans'] == 'l': a_px = img.getpixel((0, 0))#左上の1pxを背景色に指定
		elif img_d['trans'] == 'r': a_px = img.getpixel((img.width-1, 0))#右上の1pxを背景色に指定

		img_mask = Image.new('L', img.size, 0)

		#-ピクセル代入用配列作成-
		px_list = []
		mask_px_list = []
		for px in img_datas:
			if px == a_px:#背景色と一致したら
				px_list.append((128, 128, 128))#灰色に
				mask_px_list.append((0))#マスクは白
			else:#それ以外は
				px_list.append(px)#そのまま
				mask_px_list.append((255))#マスクは黒
					
			img.putdata(px_list)#完了
			img_mask.putdata(mask_px_list)
	
	#アルファブレンド画像の場合は画像分割数2倍
	if (img_d['trans'] == 'a'): img_d['part'] *= 2

	#-----処理分岐-----
	if img_d.get('default_cursor'):#デフォルトの画像そのままのカーソル
		#-読み込んだものと同じカーソルの縮小版を辞書から持ってくる&デコード&代入-
		#  縮小率50%を境にアイコンサイズ(大/小)を決定
		#  bool(T/F)の結果をint(1/0)として使っている
		img_resize = Image.open(BytesIO(base64.b64decode(cur_dictlist[(per < 0.5)][img_d['default_cursor']])))

	elif (img_d['part'] > 1):#縮小時分割が必要な画像(カーソル含む)
		#---分割する横幅を指定---
		crop_width = int(img.width/img_d['part'])
		crop_result_width = math.ceil(result_width/img_d['part'])

		#---切り出し→縮小→再結合---
		img_resize = Image.new(img.mode, (crop_result_width*img_d['part'], result_height), a_px)#結合用画像
		for i in range(img_d['part']):#枚数分繰り返す
			img_crop = img.crop((crop_width*i, 0, crop_width*(i+1), img.height))#画像切り出し

			if img_mask:#(専用縮小処理が必要な)カーソルの時
				img_crop = img_crop.resize((crop_result_width-1, result_height-1), Image.Resampling.LANCZOS)

				#画像本体をLANCZOS、透過部分をNEARESTで処理することによってカーソルをキレイに縮小
				img_bg = Image.new(img.mode, (crop_result_width-1, result_height-1), a_px)#ベタ塗りの背景画像を作成
				img_mask_crop = img_mask.crop((crop_width*i, 0, crop_width*(i+1), img.height))#画像切り出し
				img_mask_crop = img_mask_crop.resize((crop_result_width-1, result_height-1), Image.Resampling.NEAREST)#マスク画像はNEARESTで縮小
				img_crop = Image.composite(img_crop, img_bg, img_mask_crop)#上記2枚を利用しimg_cropへマスク

			elif (fc == 'BMP') and (img_d['trans'] in ['l', 'r']):#背景がボケると困る画像(NEAREST)
				img_crop = img_crop.resize((crop_result_width, result_height), Image.Resampling.NEAREST)

			else:#それ以外の画像(LANCZOS)
				img_crop = img_crop.resize((crop_result_width, result_height), Image.Resampling.LANCZOS)

			img_resize.paste(img_crop, (crop_result_width*i, bool(img_mask)))#結合用画像へ貼り付け - 専用カーソルは上1px空ける

	else:
		img_resize = img.resize((result_width, result_height), Image.Resampling.LANCZOS)
	
	#-----画像保存-----
	if img_d['cursor']:#カーソル

		#PNG可逆
		img_io = BytesIO()
		img_resize.save(img_io, format="PNG")
		img_io.seek(0)
		with open(img_result, "wb") as img_resize_comp:
			img_resize_comp.write(zf.ZopfliPNG().optimize(img_io.read()))

	elif (fc == 'PNG'):#元々PNG

		if values['PNGcolor_comp']:
			with tempfile.TemporaryDirectory() as imgtmpdir:#一時ディレクトリ作成
				imgtmpdir = Path(imgtmpdir)
				img_result_tmp = Path(imgtmpdir / img_result.name)

				#PNG減色→可逆
				img_resize.save(img_result_tmp, format="PNG")
				sp.run(['pngquant', '--floyd=1', '--speed=1', '--quality=0-100', '--force', '--ext', '.png', str(values['PNGcolor_comp_num']), str(img_result_tmp)], shell=True, **subprocess_args(True))
				
				#入力元が拡張子偽装だと出力結果が".jpg.png"みたいになるのでそっち指定
				img_result_tmp2 = Path(img_result_tmp.parent / Path(str(img_result_tmp.name) + '.png'))
				if img_result_tmp2.exists(): img_result_tmp = img_result_tmp2

				with open(img_result_tmp, "rb") as im:
					im_bin = im.read()
				with open(img_result, "wb") as im:
					im.write(zf.ZopfliPNG().optimize(im_bin))

		else:
			#PNG可逆
			img_io = BytesIO()
			img_resize.save(img_io, format="PNG")
			img_io.seek(0)
			with open(img_result, "wb") as img_resize_comp:
				img_resize_comp.write(zf.ZopfliPNG().optimize(img_io.read()))

	elif (fc == 'BMP') and ( (img_d['trans'] in ['l', 'r']) or (not values['jpg_mode']) ):#bmpかつLRで呼出またはJPGmode OFF
		img_resize.save(img_result)

	else:#それ以外 - JPGmode ON時のbmp 拡張子偽装
		#JPG可逆
		img_io = BytesIO()
		img_resize.save(img_io, format="JPEG", quality=int(values['jpg_quality_1']))
		img_io.seek(0)
		with open(img_result, "wb") as img_resize_comp:
			img_resize_comp.write(mozj.optimize(img_io.read()))

	return



def func_music_conv(f, values, temp_dir, ex_dir, msc_list, nsa_save_music, nsa_save_voice):

	#---ディレクトリ名に"bgm"もしくは"cd"とあるか&bgm命令抽出で判定---
	if ( 'bgm' in str(f.relative_to(ex_dir)) ) or ( 'cd' in str(f.relative_to(ex_dir)) ) or ( (f.relative_to(ex_dir))  in msc_list ):
		msc_result = (temp_dir / nsa_save_music / f.relative_to(ex_dir))
		result_kbps = str(values['BGM_kbps']) + 'k'
		result_Hz = str(values['BGM_Hz'])

	else:
		msc_result = (temp_dir / nsa_save_voice / f.relative_to(ex_dir))
		result_kbps = str(values['SE_kbps']) + 'k'
		result_Hz = str(values['SE_Hz'])
	
	msc_result.parent.mkdir(parents=True,  exist_ok=True)#保存先作成
	
	#---ogg変換用処理---
	if values['ogg_mode']:
		with tempfile.TemporaryDirectory() as msctmpdir:#一時ディレクトリ作成
			msctmpdir = Path(msctmpdir)
			msc_temp_ogg = Path(msctmpdir / 'a.ogg')

			sp.run(['ffmpeg', '-y',
				'-i', str(f),
				'-ab', result_kbps,
				'-ar', result_Hz,
				'-ac', '2', str(msc_temp_ogg),
			], shell=True, **subprocess_args(True))	
			
			#一時ディレクトリ作成→そちらにogg保存→元の場所に移行 にすることによって、
			#並列処理時の競合を防ぐ
			msc_temp_ogg.rename(msc_result)

	else:
		os.chmod(path=f, mode=stat.S_IWRITE)#念の為読み取り専用を外す
		shutil.move(f,msc_result)#移動するだけ

	return



def func_data_move(f, temp_dir, nsa_save, ex_dir):
	d = (temp_dir / nsa_save['other'] / f.relative_to(ex_dir)).parent
	d.mkdir(parents=True,  exist_ok=True)
	os.chmod(path=f, mode=stat.S_IWRITE)#念の為読み取り専用を外す
	shutil.move(f, d)
	return



def func_arc_nsa(temp_dir, a, same_hierarchy):
	with tempfile.TemporaryDirectory() as nsatmpdir:#一時ディレクトリ作成
		nsatmpdir = Path(nsatmpdir)

		nsaed_path = Path(same_hierarchy / 'tools' / 'nsaed.exe')
		nsaed_path_copy = Path(nsatmpdir / 'nsaed.exe')

		arc_dir = Path( temp_dir / a )
		arc_dir2= Path( nsatmpdir / a )
		arc_result = Path( temp_dir / 'no_comp' / str(a + '.nsa') ) 

		if not arc_dir.exists(): return#なければ終了

		#nsaed.exeは"自分と同階層にarc.nsaを作成する"仕様なので、
		#exe自体をnsatmpdirにコピーしてから使う
		shutil.copy(nsaed_path, nsaed_path_copy)

		#一時ディレクトリへ移動
		shutil.move(arc_dir, nsatmpdir)

		#保存先作成 - 早い話'no_comp'のこと
		arc_result.parent.mkdir(parents=True,  exist_ok=True)

		try: sp.call([nsaed_path_copy, arc_dir2], shell=True, **subprocess_args(True))
		except: pass#異常終了時 何もしない - 本当は再実行とかするべきなんだろうけど
		else: Path(nsatmpdir / 'arc.nsa').rename(arc_result)#正常終了時 - nsa移動

	return



def func_ons_ini(noreschk, values, resolution):
	reswstr = str(resolution)
	reshstr = str(int(resolution/4*3)) if (not noreschk) else str(272)

	#-メモリにフォントを読み込んでおくか-
	if values['ram_font']: ini_fm = 'ON'
	else: ini_fm = 'OFF'

	#-解像度拡大-
	if values['size_full'] or noreschk:#フルor解像度無視変換
		ini_sur = 'SOFTWARE'
		ini_asp = 'OFF'

	elif values['size_aspect']:#アス比維持
		ini_sur = 'SOFTWARE'
		ini_asp = 'ON'

	elif values['size_normal']:#拡大しない
		ini_sur = 'HARDWARE'
		ini_asp = 'OFF'

	#-サンプリングレート(Hz)-
	if values['ogg_mode']:
		ini_rate = str(max(values['BGM_Hz'], values['SE_Hz']))#ogg設定値
	else:
		ini_rate = '44100'#強制44100

	#-ons.ini作成-
	ons_ini= [
		'SURFACE=' + ini_sur + '\n',
		'WIDTH=' + reswstr + '\n',
		'HEIGHT=' + reshstr + '\n',
		'ASPECT=' + ini_asp + '\n',
		'SCREENBPP=32\n',
		'CPUCLOCK=333\n',
		'FONTMEMORY=' + ini_fm + '\n',
		'ANALOGKEY=ON1\n',
		'CURSORSPEED=10\n',
		'SAMPLINGRATE=' + ini_rate +'\n',
		'CHANNELS=2\n',
		'TRIANGLE=27\n', 'CIRCLE=13\n', 'CROSS=32\n', 'SQUARE=305\n', 'LTRIGGER=111\n', 'RTRIGGER=115\n', 'DOWN=274\n', 'LEFT=273\n', 'UP=273\n', 'RIGHT=274\n', 'SELECT=48\n', 'START=97\n', 'ALUP=276\n', 'ALDOWN=275\n',	
	]
	return ons_ini



def format_check(file):
	with open(file, 'rb') as f:
		b = f.read(8)

		if re.match(b'^\xff\xd8', b):
			ff = 'JPEG'

		elif re.match(b'^\x42\x4d', b):
			ff = 'BMP'

		elif re.match(b'^\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', b):
			ff = 'PNG'

		elif re.match(b'^\x52\x49\x46\x46', b):
			ff = 'WAV'#これ単なるRIFFだからAVIとかも引っかかるんだが...

		elif re.match(b'^\x4f\x67\x67\x53', b):
			ff = 'OGG'

		elif re.match(b'^\xff\xf3', b) or re.match(b'^\xff\xfa', b) or re.match(b'^\xff\xfb', b) or re.match(b'^\x49\x44\x33', b) or re.match(b'^\xff\x00\x00', b):
			ff = 'MP3'#ヘッダーについて詳細不明、情報求む

		else:
			ff = False

	return ff



def main():
	window_title = 'ONScripter Multi Converter for PSP ver.1.4.8'

	same_hierarchy = Path(sys.argv[0]).parent#同一階層のパスを変数へ代入

	#起動用ファイルチェック～なかったら終了
	sc = start_check(same_hierarchy)
	if sc:
		gui_msg(sc, '!')
		return
	
	#Newデバッグモード(笑)設定
	debug_dir = Path(same_hierarchy / 'debug')
	debug_mode = debug_dir.is_dir()
	if debug_mode: window_title += ' - !DEBUG MODE!'
	
	#↓実は使ってないこいつら
	default_input = ''
	default_output = ''

	window = gui_main(window_title, default_input, default_output)

	##### Event Loop #####
	with tempfile.TemporaryDirectory() as temp_dir:#一時ディレクトリ作成
		temp_dir = Path(temp_dir)
		ex_arc_dir = Path(temp_dir / 'extract_arc')
		ex_dir = Path(temp_dir / 'extract')

		disabled_list = ['progressbar']
		
		while True:
			event, values = window.read()

			### 終了時 ###
			if event is None or event == 'Exit': break

			### 入力ディレクトリ指定時 ###
			elif event == 'input_dir':
				window['convert'].update(disabled=True)#とりあえず'convert'操作無効化
				window.refresh()
				window['progressbar'].UpdateBar(10000)#処理中ですアピール的な

				text = scenario_check(Path(values['input_dir']))
				window['progressbar'].UpdateBar(0)#もどす

				if text:#txtの内容がある＝input_dirが問題ない場合のみ
					window['convert'].update(disabled=False)#'convert'操作有効化
					window.refresh()
				
				else: gui_msg('シナリオファイルが見つかりません', '!')#問題あるならエラー

			### PNG減色チェック ###
			elif event == 'PNGcolor_comp':#チェックしたときのみ色数指定有効化
				if values['PNGcolor_comp']:
					window['PNGcolor_comp_num'].update(disabled=False)
					disabled_list.remove('PNGcolor_comp_num')
				
				else:
					window['PNGcolor_comp_num'].update(disabled=True)
					disabled_list.append('PNGcolor_comp_num')
			
			### oggチェック ###
			elif event == 'ogg_mode':
				if values['ogg_mode']:
					window['BGM_kbps'].update(disabled=False)
					window['BGM_Hz'].update(disabled=False)
					window['SE_kbps'].update(disabled=False)
					window['SE_Hz'].update(disabled=False)
					disabled_list.remove('BGM_kbps')
					disabled_list.remove('BGM_Hz')
					disabled_list.remove('SE_kbps')
					disabled_list.remove('SE_Hz')
				
				else:
					window['BGM_kbps'].update(disabled=True)
					window['BGM_Hz'].update(disabled=True)
					window['SE_kbps'].update(disabled=True)
					window['SE_Hz'].update(disabled=True)
					disabled_list.append('BGM_kbps')
					disabled_list.append('BGM_Hz')
					disabled_list.append('SE_kbps')
					disabled_list.append('SE_Hz')
								
			### convert押されたとき ###
			elif event == 'convert':
				window['convert'].update(disabled=True)#'convert'操作無効化
				for d in values.keys():#その他もまとめて
					if not d in disabled_list: window[str(d)].update(disabled=True)
				window.refresh()

				#デバッグモードだと時間測るので
				if debug_mode: start_time = time.time()

				#入出力ディレクトリ競合チェック
				dc = in_out_dir_check(values['input_dir'], values['output_dir'])
				if dc: gui_msg(dc, '!')#エラー時メッセージ

				else:#正常動作時
					noreschk, game_mode, zc, text = zero_txt_check(text)#0.txt内容チェック
					if zc: gui_msg(zc, '!')#エラー時メッセージ
					
					else:
						#ここから変換開始
						window['progressbar'].UpdateBar(100)#進捗 100/10000

						#解像度無視変換時横480
						if noreschk: res = 480

						#ラジオボタンから代入
						elif values['res_640']: res = 640
						elif values['res_384']: res = 384
						elif values['res_360']: res = 360
						elif values['res_320']: res = 320
						
						#画像縮小率=指定解像度/作品解像度
						per = res / game_mode

						#画像が初期設定でどのような透過指定で扱われるかを代入
						try: def_trans = (re.findall(r'\n[\t| ]*transmode[\t| ]+([leftup|rightup|copy|alpha])', text))[0]
						except: def_trans = 'l'#見つからないなら初期値leftup

						#0.txtを編集&画像と動画の表示命令を抽出
						text, immode_dict, vid_list, msc_list = zero_txt_conv(text, per, values, def_trans)
						window['progressbar'].UpdateBar(200)#進捗 200/10000
						
						#その他ファイルをコピー
						shutil.copytree(Path(values['input_dir']), ex_dir, ignore=shutil.ignore_patterns('*.sar', '*.nsa', '*.ns2', '*.exe', '*.dll', '*.txt', '*.ini', '*.ttf', 'gloval.sav', 'envdata', 'nscript.dat'))

						#存在するarcをここで全てリスト化(もちろん上書き順は考慮)
						temp_arc = []
						temp_arc += sorted(list(Path(values['input_dir']).glob('*.ns2')))
						temp_arc += reversed(list(Path(values['input_dir']).glob('*.nsa')))
						temp_arc += reversed(list(Path(values['input_dir']).glob('*.sar')))

						#↑のリスト順にarcを処理
						GARbro_path = Path(same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.Console.exe')
						ex_arc_dir.mkdir()

						#一度全て並列展開
						with concurrent.futures.ThreadPoolExecutor() as executor:
							futures = []
							for p in temp_arc:
								e = Path(ex_arc_dir / p.name)
								futures.append(executor.submit(arc_extract, GARbro_path, p, e))#nsaやsarを展開
							
							lentmparc = len(temp_arc)
							for i,ft in enumerate(concurrent.futures.as_completed(futures)):
								window['progressbar'].UpdateBar(200 + int(float(i / lentmparc) * 300))#進捗 ~500/10000
						
						#展開したやつをnsa読み取り優先順に上書き移動
						for p in temp_arc:
							e = Path(ex_arc_dir / p.name)
							for f in e.glob('**/*'):
								if f.is_file():
									f_ex = (ex_dir / f.relative_to(e))
									f_ex.parent.mkdir(parents=True, exist_ok=True)
									shutil.move(f, f_ex)
							
						#保存先辞書作成 - ここ将来的にもっと分割したいなぁ
						if values['nsa_mode']: nsa_save = {'image':'arc', 'music':'arc1', 'voice':'arc2', 'other':'arc'}
						else: nsa_save = {'image':'no_comp', 'music':'no_comp', 'voice':'no_comp', 'other':'no_comp'}

						#展開したファイルを並列変換
						with concurrent.futures.ThreadPoolExecutor() as executor:
							futures = []
							for f in ex_dir.glob('**/*'):
								if f.is_file():
									fc = format_check(f)

									#動画
									if (f.relative_to(ex_dir) in vid_list) or ((f.suffix).lower() in ['.avi', '.mpg', '.mpeg']):
										futures.append(executor.submit(func_video_conv, f, values, noreschk, res, same_hierarchy, temp_dir, ex_dir))
							
									#画像
									elif fc in ['PNG', 'BMP', 'JPEG']:
										futures.append(executor.submit(func_image_conv, f, fc, values, def_trans, immode_dict, noreschk, per, temp_dir, ex_dir, nsa_save['image']))

									#音源
									elif fc in ['WAV', 'OGG', 'MP3']:
										futures.append(executor.submit(func_music_conv, f, values, temp_dir, ex_dir, msc_list, nsa_save['music'], nsa_save['voice'] ))

									#その他
									else:
										futures.append(executor.submit(func_data_move, f, temp_dir, nsa_save, ex_dir))

							lenex = len(list(ex_dir.glob('**/*')))						
							for i,ft in enumerate(concurrent.futures.as_completed(futures)):
								window['progressbar'].UpdateBar(500 + int(float(i / lenex) * 9000))#進捗 ~9500/10000

						#nsa並列作成
						arcname = ['arc', 'arc1', 'arc2']
						with concurrent.futures.ThreadPoolExecutor() as executor:
							futures = []
							for a in arcname:
								futures.append(executor.submit(func_arc_nsa, temp_dir, a, same_hierarchy))

							lenarcname = len(arcname)#一応他と書式合わせる感じで
							for i,ft in enumerate(concurrent.futures.as_completed(futures)):
								window['progressbar'].UpdateBar(9500 + (float(i / lenarcname) * 300))#進捗 ~9800/10000

						#ons.ini作成
						with open(Path( temp_dir / 'no_comp' / 'ons.ini' ), 'w') as n: n.writelines( func_ons_ini(noreschk, values, res) )
						
						#savedataフォルダ作成(無いとエラー出す作品向け)
						if Path(Path(values['input_dir']) / 'savedata').exists(): Path(temp_dir / 'no_comp' / 'savedata').mkdir()
						
						#最後に0.txt作成(今更感)
						with open(Path(temp_dir / 'no_comp' / '0.txt'), 'w') as s:
							text += ('\n\n;\tConverted by "' + window_title + '"\n;\thttps://github.com/Prince-of-sea/ONScripter_Multi_Converter\n')
							s.write(text)#もう少し早めでもいい気がする
							window['progressbar'].UpdateBar(9900)#進捗 9900/10000

						#arc2があってarc1がない場合
						arc1_path = Path(temp_dir / 'no_comp' / 'arc1.nsa')
						arc2_path = Path(temp_dir / 'no_comp' / 'arc2.nsa')
						if (arc2_path.exists()) and (not arc1_path.exists()): arc2_path.rename(arc1_path)#2を1に
						
						#debugフォルダ内のファイル全部ぶっこむ
						if debug_mode:
							for f in debug_dir.glob('**/*'):
								if f.is_file():
									f.parent.mkdir(parents=True, exist_ok=True)
									shutil.copy(f, Path(temp_dir / 'no_comp'))

						#result移動前の準備
						result_dir = Path( Path(values['output_dir']) / Path('PSP_' + str(Path(values['input_dir']).stem)))
						if result_dir.exists():
							os.chmod(path=result_dir, mode=stat.S_IWRITE)#読み取り専用を外す
							shutil.rmtree(result_dir)#すでにディレクトリが存在する場合は削除
						
						Path(temp_dir / 'no_comp').rename(result_dir)#完成品を移動
						window['progressbar'].UpdateBar(10000)#進捗 10000/10000

						if debug_mode:
							with open(Path(result_dir / 'debug.txt'), mode='w') as f:
								s = '##################################################\n'+str(window_title)+'\n##################################################\n変換ファイル総数:\t\t'+str(lenex)+'\n処理時間:\t\t'+str(time.time()-start_time)+'s\n\n##################################################\n変数:\n\n'
								for d in values.keys(): s += (str(d) + ':\t\t' + str(values[d]) + '\n')
								f.write(s)

						gui_msg('処理が終了しました', '!')#メッセージ
						break


				window['convert'].update(disabled=False)#'convert'操作有効化
				for d in values.keys():#その他もまとめて
					if not d in disabled_list: window[str(d)].update(disabled=False)

				window.refresh()



main()