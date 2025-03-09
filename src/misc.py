#!/usr/bin/env python3
import os
import re
import shutil
import sys
import i18n
import pythoncom
import win32ui, win32gui
import win32com.client

from pathlib import Path

from process_notons import get_titledict


def get_programslist(icotemp_dir: Path, charset: str):
	titledict = get_titledict()
	programs_list = []

	for env in ['ALLUSERSPROFILE', 'APPDATA']:

		#環境変数からスタートメニューへのパスを取得
		programs_dir = Path(Path(os.environ[env]) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs')

		#スタートメニューリンク一覧取得
		for i, lnk_path in enumerate(programs_dir.glob('**/*.lnk')):
			icon_path = Path(icotemp_dir / f'{i}.bmp')

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
				programs_list.append( {'name': program_name, 'exe_path': target_path, 'icon_path': icon_path, 'overwrite_title_setting': False} )
			
			#個別変換 - 日本語のみ対応
			# [追記]この仕様「.lnkの親フォルダ名(ない場合.lnk本体の名前)」と「リンク先の.exe名」でチェック掛けてるので両方一致すると別プログラムでも元作品と誤認します
			# 今のところは意図的に合わせないと被らないような名前だけだが、将来的にはもっと厳格な仕様に変えたほうが良いかも
			elif (charset == 'cp932'):

				#個別変換一致確認
				for k,v in titledict.items():

					#名前一致&ファイルが存在する場合
					if (v.get('program_name') == program_name) and (v.get('exe_name') == target_path.stem) and (target_path.is_file()):

						#存在する場合はprograms_listに追加
						programs_list.append( {'name': v['title'], 'exe_path': target_path, 'icon_path': icon_path, 'overwrite_title_setting': k} )

	return programs_list


def exepath2icon(exe_path: Path, icon_path: Path):
	#参考: https://stackoverflow.com/questions/19760913/how-to-extract-32x32-icon-bitmap-data-from-exe-and-convert-it-into-a-pil-image-o

	large, small = win32gui.ExtractIconEx(str(exe_path),0)

	hdc = win32ui.CreateDCFromHandle( win32gui.GetDC(0) )
	hbmp = win32ui.CreateBitmap()
	hbmp.CreateCompatibleBitmap( hdc, 32, 32 )
	hdc = hdc.CreateCompatibleDC()

	hdc.SelectObject( hbmp )

	try: hdc.DrawIcon( (0,0), large[0] )#アイコンがない場合ここでエラー
	except: pass

	win32gui.DestroyIcon(large[0])
	win32gui.DestroyIcon(small[0])

	hbmp.SaveBitmapFile( hdc, str(icon_path))
	
	return


def in_out_dir_check(values: dict):
	input_dir = values['input_dir']
	output_dir = values['output_dir']
	
	#エラーメッセージ作成
	errmsg = ''
	
	if not input_dir: errmsg = i18n.t('ui.Input_directory_not_specified')
	elif Path(input_dir).is_dir() == False: errmsg = i18n.t('ui.Input_directory_not_found')

	elif not output_dir: errmsg = i18n.t('ui.Output_directory_not_specified')
	elif Path(output_dir).is_dir() == False: errmsg = i18n.t('ui.Output_directory_not_found')

	elif os.path.normpath(input_dir).lower() in os.path.normpath(output_dir).lower(): errmsg = i18n.t('ui.Input_output_conflict')

	if errmsg: raise Exception(errmsg)
	
	return


def create_configfile(values: dict, values_ex:dict, compressed_dir: Path):
	output_resolution = values_ex['output_resolution']    
	etc_iniramfont_chk = values['etc_iniramfont_chk']
	etc_inicursor_chk = values['etc_inicursor_chk']
	etc_iniscreen = values['etc_iniscreen']
	select_resolution = values_ex['select_resolution']
	configfile = values_ex['configfile']
	charset = values['charset']

	match configfile:
		case 'ons.ini':#実質PSP専用?

			#cp932の場合
			if charset == 'cp932':
				#surface/aspect
				if (etc_iniscreen == i18n.t('var.full_size')) or (not output_resolution in select_resolution):#フルor解像度無視変換
					surface = 'SOFTWARE'
					aspect = 'OFF'

				elif (etc_iniscreen == i18n.t('var.maintain_ratio')):#アス比維持
					surface = 'SOFTWARE'
					aspect = 'ON'
				
				elif (etc_iniscreen == i18n.t('var.no_expansion')):#拡大しない
					surface = 'HARDWARE'
					aspect = 'OFF'

				else: raise i18n.t('ui.ons_ini_not_found_expansion_settings')

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
			#gbkの場合
			elif charset == 'gbk':#Based on 20080121-zh04
				screensize = 'full' if (etc_iniscreen == i18n.t('var.full_size')) else 'normal'
				cfg = f'''resolution={output_resolution[0]}
screensize={screensize}
cpuclock=333
busclock=166
'''
		
		case 'sittings.txt':#現時点ではvita専用 おそらくyuri系列大体この仕様
			cfg = r'--window --fontcache --textbox'
			if charset == 'cp932': cfg += r' --enc:sjis'
			
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
	charset = values['charset']

	#0.txt書き出し
	ztxtscript += (f'\nend\n\n;\tConverted by "ONScripter Multi Converter ver.{version}"\n;\thttps://github.com/Prince-of-sea/ONScripter_Multi_Converter\n')
	with open(Path(compressed_dir / '0.txt'), 'w', encoding=charset, errors='ignore') as s: s.write(ztxtscript)

	#ついでにエラーログがあれば書き出し
	if allerrlog:
		with open(Path(compressed_dir / 'errorlog.tsv'), 'w', encoding='utf-8', errors='ignore') as s: s.write(allerrlog)

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
