#!/usr/bin/env python3
import os
import shutil
import tempfile
import subprocess as sp
import tkinter.filedialog as filedialog
import tkinter.messagebox
import webbrowser
import dearpygui.dearpygui as dpg

from pathlib import Path

from hardwarevalues_config import gethardwarevalues_full
from requiredfile_locations import exist, location
from utils import get_meipass, message_box, openread0x84bitxor, configure_progress_bar
from misc import get_programslist, exepath2icon
from process_notons import get_titledict
from conversion import convert_start


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


def ask_decode_nscriptdat(sender, app_data, charset):
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
				dpg.add_button(label='OK', user_data=(msg_ask, charset, True), callback=decode_nscriptdat)
				dpg.add_button(label='キャンセル', user_data=(msg_ask, charset, False), callback=decode_nscriptdat)
	dpg.split_frame()
	dpg.set_item_pos(msg_ask, [dpg.get_viewport_client_width() // 2 - dpg.get_item_width(msg_ask) // 2, dpg.get_viewport_client_height() // 2 - dpg.get_item_height(msg_ask) // 2])
	return


def decode_nscriptdat(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if not user_data[2]: return
	charset = user_data[1]

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

	with open(txtpath, 'w', encoding=charset, errors='ignore') as s: s.write(openread0x84bitxor(_path, charset))
	
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

def open_licensespy():
	webbrowser.open(get_meipass('licenses_py.txt'), new=1, autoraise=True)
	return


def copyrights(sender, app_data, user_data):
	message_box('copyrights', f'ONScripter Multi Converter ver.{user_data}\n(C) 2021-2025 Prince-of-sea / PC-CNT / RightHand', 'info', True)
	return


def open_input():
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()
	dpg.set_value('input_dir', _path)


def open_select(sender, app_data, user_data):
	with dpg.window(label=f'インストール済みゲーム一覧', height=360, width=628, modal=True, no_move=True) as opsel:

		#ローディング
		with dpg.group(horizontal=True, tag='loading'):
			dpg.add_text(' '*60)#ごまかしスペース ここもっと良い書き方募集中
			dpg.add_loading_indicator(style=2, radius=10)

		#一時ディレクトリ作成
		with tempfile.TemporaryDirectory() as icotemp_dir:
			icotemp_dir = Path(icotemp_dir)

			#programs_list取得
			programs_list = get_programslist(icotemp_dir, user_data)

			#ローディング削除
			dpg.delete_item('loading')

			#リスト
			for d in programs_list:

				#アイコン作成
				exepath2icon(d['exe_path'], d['icon_path'])#数が多ければ並行処理のほうが速いだろうけどめんどいのでそのまま

				#表示領域
				with dpg.group(horizontal=True, height=32):

					#アイコン表示
					width, height, channels, data = dpg.load_image(str(d['icon_path']))
					with dpg.texture_registry(): texture_id = dpg.add_static_texture(width, height, data)
					dpg.add_image(texture_id, width=32)

					#ボタン表示
					dpg.add_button(label=f'{d['name']}\t({d['exe_path'].parent}){'　'*50}', user_data=(opsel, d), width=560, callback=open_select_main)

				#ここ来るたびにとりあえず画面更新(?)
				dpg.split_frame()
	return


def open_select_main(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if not user_data[1]: return

	d = user_data[1]

	_path = str(d['exe_path'].parent).replace('\\', '/')
	dpg.set_value('input_dir', _path)

	if d['overwrite_title_setting']: dpg.set_value('title_setting', d['overwrite_title_setting'])
	else: dpg.set_value('title_setting', 'None')

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


def ask_convert_start(sender, app_data, user_data):
	configure_progress_bar(0, '変換開始...', True)

	#入力値事前取得
	values = {
		'useGUI':True,
		'hardware':user_data[0],
		'version':user_data[1],
		'charset':user_data[2],
	}

	titledict = get_titledict()

	#個別選択時
	if dpg.get_value('title_setting') in titledict.keys():
		title_info = titledict[ dpg.get_value('title_setting') ]
		configure_progress_bar(0, '個別設定変換確認...', True)
		title = title_info['title']
		requiredsoft = title_info['requiredsoft']
		version = title_info['version']
		notes = title_info['notes']
		is_43 = title_info['is_4:3']

		r_txt = '\n・'.join(['']+requiredsoft) if requiredsoft else '\n・なし'
		v_txt = '\n・'.join(['']+version)
		n_txt = '\n・'.join(['']+notes)

		h_list = []
		for hw_k, hw_v in gethardwarevalues_full().items():
			if (hw_k == 'PSP'): hw_s = '可'#PSPなら(埋め込み昆布は全部動くように作ってるはずなので)ok
			elif (not hw_v['values_ex']['aspect_4:3only']): hw_s = '可'#4:3専用機ではないならok		
			elif is_43: hw_s = '可'#作品が4:3ならok
			else: hw_s = '不可'

			h_list.append(hw_k+':'+hw_s)

		h_txt = '\n'+' / '.join(h_list)

		s = (
			'=================================================================\n'\
			f'[変換先として指定可能なハード]{h_txt}\n\n'
			'=================================================================\n'\
			f'[追加で用意するソフト]{r_txt}\n\n'\
			'=================================================================\n'\
			f'[確認済み対応タイトル]{v_txt}\n\n'\
			'=================================================================\n'\
			f'[注意事項]{n_txt}\n\n'\
			'=================================================================\n'\
			)

		with dpg.mutex():
			with dpg.window(label=f'個別設定変換確認 - {title}', modal=True, no_close=True, no_move=True) as msg_askconv:
				with dpg.child_window(height=270, width=620):
					dpg.add_text(s)
				dpg.add_text('以上を確認したうえで、変換を開始しますか？')
				with dpg.group(horizontal=True):
					dpg.add_button(label='OK', user_data=(msg_askconv, True, values), callback=askconv_callback)
					dpg.add_button(label='キャンセル', user_data=(msg_askconv, False, values), callback=askconv_callback)
		dpg.split_frame()
	# Noneなら確認を飛ばして変換開始
	else:
		return convert_start(values)
	return


def askconv_callback(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if user_data[1]:
		return convert_start(user_data[2])
	else:
		configure_progress_bar(0, '変換がキャンセルされました', True)
	return