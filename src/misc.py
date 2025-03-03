#!/usr/bin/env python3
import os
import re
import shutil
import subprocess as sp
import sys
import pythoncom
import tkinter.filedialog as filedialog
import tkinter.messagebox
import win32com.client
import webbrowser
from pathlib import Path
import dearpygui.dearpygui as dpg

from requiredfile_locations import exist, location
from utils import message_box, openread0x84bitxor
from process_notons import get_titledict

def get_programslist():
	titledict = get_titledict()
	programs_list = []

	for env in ['ALLUSERSPROFILE', 'APPDATA']:

		#環境変数からスタートメニューへのパスを取得
		programs_dir = Path(Path(os.environ[env]) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs')

		#スタートメニューリンク一覧取得
		for lnk_path in programs_dir.glob('**/*.lnk'):

			#アンインストール系(と思われるもの)は飛ばす
			if any(s in lnk_path.stem.lower() for s in ['削除', 'アンインストール', 'ｱﾝｲﾝｽﾄｰﾙ', 'uninstall']): continue

			#ショートカットのターゲットを取得
			pythoncom.CoInitialize()
			target_path = Path(win32com.client.Dispatch("WScript.Shell").CreateShortcut(str(lnk_path)).TargetPath)
			pythoncom.CoUninitialize()

			#拡張子が.exeでない場合は飛ばす
			if (not target_path.suffix.lower() == '.exe'): continue

			#ショートカットの親ディレクトリ名を取得
			lnk_parentname = lnk_path.parent.name

			#親ディレクトリ名がProgramsでない場合はそのまま、Programsの場合はショートカット名にする
			program_name = lnk_parentname if (lnk_parentname != 'Programs') else lnk_path.stem

			#ショートカットのターゲットにnscripterのシナリオファイルが存在するか確認
			if any(s for s in ['nscript.dat', '0.txt', '00.txt'] if Path(target_path.parent / s).is_file()):

				#存在する場合はprograms_listに追加
				programs_list.append( {'name': program_name, 'exe_path': target_path, 'overwrite_title_setting': False} )
			
			#存在しない場合はタイトル名を取得し、titledictからtitleを取得
			else:

				#個別変換一致確認
				for k,v in titledict.items():

					#名前一致&ファイルが存在する場合
					if (v.get('program_name') == program_name) and (v.get('exe_name') == target_path.stem) and (target_path.is_file()):

						#存在する場合はprograms_listに追加
						programs_list.append( {'name': v['title'], 'exe_path': target_path, 'overwrite_title_setting': k} )

	return programs_list


def get_uiiconpath():
	if hasattr(sys, '_MEIPASS'): base_dir =  Path(sys._MEIPASS)
	else: base_dir = Path('.')
	uiicon = Path(base_dir / '__icon.ico')
	return str(uiicon)
	

def ask_create_disabledvideofile():
	with dpg.mutex():
		with dpg.window(label='連番動画無効化ファイル作成', modal=True) as msg_ask:
			dpg.add_text('一部作品では、連番画像に変換した動画が再生されずに\n' +\
						'操作不能になって先に進めなくなることがあります\n\n' +\
						'本機能で作成した無効化ファイルを置くことで\n' +\
						'再生をスキップし、不具合を回避することが出来ます\n' +\
						'(ver.2.3.1以降で変換した作品でのみ有効です)\n\n' +\
						'無効化ファイルを作成しますか？')
			with dpg.group(horizontal=True):
				dpg.add_button(label='OK', user_data=(msg_ask, True), callback=create_disabledvideofile)
				dpg.add_button(label='キャンセル', user_data=(msg_ask, False), callback=create_disabledvideofile)
	dpg.split_frame()
	dpg.set_item_pos(msg_ask, [dpg.get_viewport_client_width() // 2 - dpg.get_item_width(msg_ask) // 2, dpg.get_viewport_client_height() // 2 - dpg.get_item_height(msg_ask) // 2])
	return


def create_disabledvideofile(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if not user_data[1]:
		return
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()

	if not _path: return

	_path = Path(_path)
	with open(Path(_path / '_DISABLED_VIDEO'), 'wb') as s: s.write(b'\xff')
	
	message_box('完了', '無効化ファイルを作成しました', 'info', True)
	return


def ask_decode_nscriptdat():
	with dpg.mutex():
		with dpg.window(label='nscript.dat復号化', modal=True) as msg_ask:
			dpg.add_text('そのままでは読めない形式になっているnscript.datを復号化します\n' +\
						'普通はゲームを選択し[Convert]ボタンを押せば自動で復号化されるため、\n' +\
						'本機能は使う必要がありません\n' +\
						'また、普通のConvertで復号化が失敗するnscript.datは、\n' +\
						'本機能でも復号化に失敗します\n\n' +\
						'Convert前に0.txtを手動で編集する必要がある時など、\n' +\
						'特殊な作業を行う場合にのみ使ってください\n\n' +\
						'復号化するnscript.datを選択しますか？')
			with dpg.group(horizontal=True):
				dpg.add_button(label='OK', user_data=(msg_ask, True), callback=decode_nscriptdat)
				dpg.add_button(label='キャンセル', user_data=(msg_ask, False), callback=decode_nscriptdat)
	dpg.split_frame()
	dpg.set_item_pos(msg_ask, [dpg.get_viewport_client_width() // 2 - dpg.get_item_width(msg_ask) // 2, dpg.get_viewport_client_height() // 2 - dpg.get_item_height(msg_ask) // 2])
	return


def decode_nscriptdat(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if not user_data[1]:
		return
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askopenfilename(filetypes=[('NScripter script','nscript.dat;*.scp')])#どうせ同じなので旧Scripterもできるようにしておく
	root.destroy()

	if not _path: return

	_path = Path(_path)

	if (str(_path.name).lower() == 'nscript.dat'):

		txtpath = _path.parent / '0.txt'
		bakpath = _path.parent / '0.txt.bak'

	else:#旧Scripter
		txtpath = _path.parent / f'{_path.stem}.txt'
		bakpath = _path.parent / f'{_path.stem}.txt.bak'
		
	if txtpath.exists():
		if bakpath.exists():
			if bakpath.is_file(): bakpath.unlink()
			else: shutil.rmtree(bakpath)

		txtpath.rename(bakpath)

	with open(txtpath, 'w', encoding='cp932', errors='ignore') as s: s.write(openread0x84bitxor(_path))
	
	message_box('完了', '復号化しました', 'info', True)
	return


def open_garbro():
	if exist('GARbro_GUI'): sp.Popen([location('GARbro_GUI')])
	else: message_box('警告', 'GARbro_GUIが見つかりません', 'warning', True)
	return


def open_repositorieslink():
	url = 'https://github.com/Prince-of-sea/ONScripter_Multi_Converter'
	webbrowser.open(url, new=1, autoraise=True)
	return


def copyrights():
	message_box('copyrights', f'ONScripter Multi Converter ver.{dpg.get_value('version')}\n(C) 2021-2025 Prince-of-sea / PC-CNT / RightHand', 'info', True)
	return


def open_input():
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()
	dpg.set_value('input_dir', _path)


def open_select():
	programs_list = get_programslist()

	with dpg.window(label=f'インストール済みゲーム一覧', height=360, width=628, modal=True, no_move=True) as opsel:
		for d in programs_list:
			with dpg.group(horizontal=True, height=32, width=600):
				dpg.add_button(label=f'{d['name']}\t({d['exe_path'].parent}){'　'*50}', user_data=(opsel, d), callback=open_select_main)
		
		dpg.split_frame()
	return


def open_select_main(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if not user_data[1]: return

	d = user_data[1]

	_path = str(d['exe_path'].parent).replace('\\', '/')
	dpg.set_value('input_dir', _path)

	if d['overwrite_title_setting']: dpg.set_value('title_setting', d['overwrite_title_setting'])
	else: dpg.set_value('title_setting', '未指定')

	return


def open_output():
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()
	dpg.set_value('output_dir', _path)


def desktop_output():
	_path = str(Path(os.environ['USERPROFILE']) / 'Desktop').replace('\\', '/')
	dpg.set_value('output_dir', _path)
	return


def close_dpg():
	dpg.stop_dearpygui()


def in_out_dir_check(values: dict):
	input_dir = values['input_dir']
	output_dir = values['output_dir']
	
	#エラーメッセージ作成
	errmsg = ''
	
	if not input_dir: errmsg = '入力先が指定されていません'
	elif Path(input_dir).is_dir() == False: errmsg = '入力先が存在しません'

	elif not output_dir: errmsg = '出力先が指定されていません'
	elif Path(output_dir).is_dir() == False: errmsg = '出力先が存在しません'

	elif input_dir in output_dir: errmsg = '入出力先が競合しています'

	if errmsg: raise Exception(errmsg)
	
	return


def create_configfile(values: dict, values_ex:dict, compressed_dir: Path):
	output_resolution = values_ex['output_resolution']	
	etc_iniramfont_chk = values['etc_iniramfont_chk']
	etc_inicursor_chk = values['etc_inicursor_chk']
	etc_iniscreen = values['etc_iniscreen']
	select_resolution = values_ex['select_resolution']
	configfile = values_ex['configfile']

	match configfile:
		case 'ons.ini':#実質PSP専用?

			#surface/aspect
			if (etc_iniscreen == '拡大(フルサイズ)') or (not output_resolution in select_resolution):#フルor解像度無視変換
				surface = 'SOFTWARE'
				aspect = 'OFF'

			elif (etc_iniscreen == '拡大(比率維持)'):#アス比維持
				surface = 'SOFTWARE'
				aspect = 'ON'
			
			elif (etc_iniscreen == '拡大しない'):#拡大しない
				surface = 'HARDWARE'
				aspect = 'OFF'

			else: raise ValueError('ons.iniの拡大設定が見つかりません')

			#fontmemory
			fontmemory = 'ON' if etc_iniramfont_chk else 'OFF'

			#analogkey
			analogkey = 'ON2' if etc_inicursor_chk else 'ON1'

			cfg = f'''SURFACE={surface}
WIDTH={output_resolution[0]}
HEIGHT={output_resolution[1]}
ASPECT={aspect}
SCREENBPP=32
CPUCLOCK=333
FONTMEMORY={fontmemory}
ANALOGKEY={analogkey}
CURSORSPEED=10
SAMPLINGRATE=44100
CHANNELS=2
TRIANGLE=27
CIRCLE=13
CROSS=32
SQUARE=305
LTRIGGER=111
RTRIGGER=115
DOWN=274
LEFT=273
UP=273
RIGHT=274
SELECT=48
START=97
ALUP=276
ALDOWN=275
'''
		
		case 'sittings.txt':#現時点ではvita専用 おそらくyuri系列大体この仕様
			cfg = r'--window --fontcache --textbox --enc:sjis'
			
		case _: return

	with open(Path(compressed_dir / configfile), 'w', encoding='utf-8') as s: s.write(cfg)

	return


def remove_0txtcommentout(values_ex):
	ztxtscript = values_ex['0txtscript']
	ztxtscript_new = ''

	#最初のコメントアウトは解像度表記(のはず)なので飛ばすようフラグ立て
	first_commentout_flag = True

	for line in ztxtscript.splitlines():
		#行がある場合のみ(=空行は飛ばす)
		if line:

			#コメントアウトの有無確認
			line_match1 = re.match(r'\s*(.*?)\s*;(?!.*")', line)#コメント付き命令行から命令だけ出すやつ
			line_match2 = re.match(r'\s*;', line)#コメントしか無い行検出

			if (line_match1):

				#初回はフラグ折って普通に書く(これで解像度表記だけは普通に通るはず)
				if first_commentout_flag:
					first_commentout_flag = False
					ztxtscript_new += (line + '\n')
				
				#二度目以降はコメント全消し
				else:
					if line_match1[1]: ztxtscript_new += (line_match1[1] + '\n')

			elif (not line_match2):
				ztxtscript_new += (line + '\n')

	return ztxtscript_new


def create_0txt(values: dict, values_ex: dict, compressed_dir: Path):
	ztxtscript = values_ex['0txtscript']
	allerrlog = values_ex['allerrlog']
	version = values['version']

	#0.txt書き出し
	ztxtscript += (f'\nend\n\n;\tConverted by "ONScripter Multi Converter ver.{version}"\n;\thttps://github.com/Prince-of-sea/ONScripter_Multi_Converter\n')
	with open(Path(compressed_dir / '0.txt'), 'w', encoding='cp932', errors='ignore') as s: s.write(ztxtscript)

	#ついでにエラーログがあれば書き出し
	if allerrlog:
		with open(Path(compressed_dir / 'errorlog.tsv'), 'w', encoding='cp932', errors='ignore') as s: s.write(allerrlog)

	return


def create_savedatadir(values_ex: dict, compressed_dir: dict):
	savedir_path = values_ex['savedir_path']

	if savedir_path:
		Path(compressed_dir / savedir_path).mkdir()

	return


def debug_copy(values: dict, compressed_dir: Path):
	d = Path( Path(sys.argv[0]).parent / 'debug' / values['hardware'] )

	if d.is_dir():
		for p in d.glob('*'): shutil.copy(p, compressed_dir)

	return


def result_move(result_dir: Path, compressed_dir: Path):
	
	#すでにあるなら削除
	if result_dir.exists(): shutil.rmtree(result_dir)

	#移動
	shutil.move(compressed_dir, result_dir)
	
	return
