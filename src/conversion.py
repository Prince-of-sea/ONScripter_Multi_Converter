#!/usr/bin/env python3
import concurrent.futures
import math
import os
import shutil
import tempfile
import time
import i18n
from pathlib import Path

import dearpygui.dearpygui as dpg

from conversion_etc import create_cnvsetdict, tryconvert
from conversion_video import convert_video_renban2, getvidrenbanres
from hardwarevalues_config import gethardwarevalues
from misc import (
	create_0txt,
	create_configfile,
	create_savedatadir,
	debug_copy,
	in_out_dir_check,
	remove_0txtcommentout,
	result_move,
	get_iconexepath,
	create_iconpng,
)
from nsa_operations import compressed_nsa, extract_nsa
from ons_script import onsscript_check, onsscript_decode
from process_notons import get_titledict, pre_convert
from requiredfile_locations import exist_all, exist_env
from utils import configure_progress_bar, message_box


def convert_files(values: dict, values_ex: dict, cnvset_dict: dict, extracted_dir: Path, converted_dir: Path, useGUI: bool):
	num_workers = values_ex['num_workers']

	#連番かな
	isrenban = bool(values['vid_movfmt_radio'] == i18n.t('var.numbered_images'))

	#先にパスの代入&ディレクトリ作成
	for f_path_re, f_dict in cnvset_dict.items():
		#元nbzにフラグ付け
		f_dict['nbz'] = bool(f_path_re.with_suffix('.nbz') in values_ex['nbzlist'])

		#パスの代入
		f_dict['extractedpath'] = extracted_dir / f_path_re
		f_dict['convertedpath'] = converted_dir / f_dict['comp'] / 'arc_' / f_path_re

		#ディレクトリ作成
		f_dict['convertedpath'].parent.mkdir(parents=True, exist_ok=True)
	
	#並列ファイル変換時プログレスバー最大数設定
	cnvbarnum = 0.90 if (not isrenban) else 0.30

	#並列ファイル変換
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for f_path_re, f_dict in cnvset_dict.items():
			futures.append(executor.submit(tryconvert, values, values_ex, f_dict, f_path_re, converted_dir))
		
		for i,ft in enumerate(concurrent.futures.as_completed(futures)):
			configure_progress_bar(0.05 + (float(i / len(list(cnvset_dict))) * cnvbarnum), '', useGUI)#進捗 0.05→0.95(連番時0.35)

	#連番動画利用時はその画像を並列圧縮
	if isrenban:
		f_dict_video_list = []
		
		for f_dict in cnvset_dict.values():
			if (f_dict['fileformat'] == 'video'): f_dict_video_list.append(f_dict)

		for cnt, f_dict in enumerate(f_dict_video_list):
				#convert_video内で実装するとThreadPoolExecutorが競合しそうなのでこっちで処理
				startbarnum = (0.35 + ((0.60 / len(f_dict_video_list)) * cnt))
				addbarnum = (0.60 / len(f_dict_video_list))
				convert_video_renban2(values, values_ex, f_dict, startbarnum, addbarnum, useGUI)

	#2GBorファイル数20k超えチェック
	for arc_dir_num in range(10):

		#arc_dirの設定
		arc_dir = Path(converted_dir / f'arc{arc_dir_num}' / 'arc_' )

		#arc_dirが存在しないやつは無視する
		if not arc_dir.exists(): continue

		#ex_dir_nameの設定
		ex_dir_name = f'no_comp'#初期値("圧縮しない"選択時orすでにarc9まで作ってる場合このまま)
		if (values['etc_over_2gb_nsa'] == i18n.t('var.create_new_nsa_after_arc3')):
			if (arc_dir_num < 3):
				ex_dir_name = f'arc3'
			elif (arc_dir_num < 9):
				ex_dir_name = f'arc{arc_dir_num+1}'

		#合計サイズ/ファイル数を計算するための変数初期化
		dir_size = 0
		dir_cnt = 0
		dir_flag = False

		#arc_dirの中身を全件取得してサイズチェックする
		for p in arc_dir.glob('**/*'):
			if p.is_file():#ファイルのみを取得
				if (not dir_flag):#フラグが立っていなかったら
					if (dir_size <= 2097152000):#2000MB(≒2GB)以下なら
						dir_size += p.stat().st_size#累積サイズに加える
					
					if (dir_cnt <= 20000):#ファイル数が20000以下なら
						dir_cnt += 1#ファイル数を加える

					if (dir_size > 2097152000) or (dir_cnt > 20000):#容量が2000MBより大きいまたは20000ファイルより多いなら
						dir_flag = True#フラグを立てる

				if (dir_flag):#フラグが立っていたら - 乗った瞬間からこっちの処理走らせるためelse未使用
					p_moved = Path(converted_dir / ex_dir_name / 'arc_' / p.relative_to(arc_dir))#移動先パス
					p_moved.parent.mkdir(parents=True, exist_ok=True)#移動先ディレクトリ作成
					shutil.move(p, p_moved)#ファイルを移動する

	#arcダミー処理
	dummy_dir_flag = False
	for dummy_dir_num in range(2, -1, -1):#arc2からarcまで(3以降は順番に生成されるはずのため歯抜けは起きないはず)
		dummy_dir_name = f'arc{dummy_dir_num}' if (dummy_dir_num > 0) else 'arc'

		#dummy_dirの設定
		dummy_dir = Path(converted_dir / dummy_dir_name / 'arc_' )

		#まずarcの最大値が出たらフラグを立てる
		if (not dummy_dir_flag) and (p.is_file()):
			dummy_dir_flag = True
		
		#フラグが立っているのにarcが存在しないなら
		elif (dummy_dir_flag) and (not p.is_file()):
			dummy_dir.mkdir(parents=True)#とりあえずarc作って
			with open(Path(dummy_dir / '.dummy'), 'wb') as s: s.write(b'\xff')#ダミー突っ込んどく(ここ意味があるのか不明、未検証)
	
	#エラーログ収集
	allerrlog = ''
	for errlogpath in converted_dir.glob('ERROR*'):
		with open(errlogpath, 'r', encoding='utf-8') as er: allerrlog += er.read()
	
	values_ex['allerrlog'] = allerrlog
	return values_ex


def convert_start(values):
	start_time = time.perf_counter()
	useGUI = values['useGUI']
	
	#GUI時
	if (useGUI):
		
		#一旦全要素入力不可に
		for i in dpg.get_aliases():
			try: dpg.disable_item(i)
			except: pass

			#ついでに辞書に入力値取得
			values[i] = dpg.get_value(i)
		
	configure_progress_bar(0, i18n.t('ui.Progress_start_conversion'), useGUI)

	#ここから処理
	try:
		required_soft_list = ['GARbro', 'smjpeg_encode', 'nsaed']

		#タイトル個別処理辞書取得
		titledict = get_titledict()

		#個別選択時
		if values['title_setting'] in titledict.keys():
			title_info = titledict[values['title_setting']]

			#必要ソフトを配列に代入
			required_soft_list += title_info['requiredsoft']

		#必要ソフトチェック
		if not exist_env('ffmpeg'): raise FileNotFoundError(i18n.t('ui.ffmpeg_not_found'))
		if not exist_env('ffprobe'): raise FileNotFoundError(i18n.t('ui.ffprobe_not_found'))
		if not exist_all(required_soft_list): raise FileNotFoundError(i18n.t('ui.required_software_not_found'))

		#入出力ディレクトリチェック
		in_out_dir_check(values)

		#Path型に変換
		values['input_dir'] = Path(values['input_dir'])
		values['output_dir'] = Path(values['output_dir'])

		#一時ディレクトリ作成    
		with tempfile.TemporaryDirectory() as temp_dir:
			temp_dir = Path(temp_dir)

			#展開済データ置き場(nsa展開物)
			extracted_dir = Path(temp_dir / 'extracted')

			#変換済データ置き場(この時点でnsa再圧縮用に分けとく)
			converted_dir = Path(temp_dir / 'converted')

			#圧縮済データ置き場(nsaに再圧縮、0.txtもここ)
			compressed_dir = Path(temp_dir / 'compressed')

			#最終的な出力はこれ
			result_dir = Path(values['output_dir'] / Path(f'result_{values['hardware']}_{values['input_dir'].name}'))

			#データ置き場作成
			extracted_dir.mkdir()
			converted_dir.mkdir()
			compressed_dir.mkdir()

			#元valuesから計算処理かけて作った結果いれるところ+0.txt(&他)からすくい上げるもの
			configure_progress_bar(0.005, i18n.t('ui.Progress_get_hardware_settings'), useGUI)
			values_ex = gethardwarevalues(values['hardware'], 'values_ex')

			#並列処理用スレッド設定
			values_ex['num_workers'] = math.ceil(os.cpu_count() / 4) if (values.get('lower_cpu_usage')) else (os.cpu_count() + 4)#low時スレッド数/4繰り上げ、通常時スレッド数+4(初期値)

			#個別選択時
			if values['title_setting'] in titledict.keys():

				#個別タイトルが非4:3&変換先ハードが4:3限定(PSP除く)の場合
				if (not title_info['is_4:3']) and (values_ex['aspect_4:3only']) and (values['hardware'] != 'PSP'):

					#非対応解像度エラー
					raise Exception(i18n.t('ui.Unsupported_resolution'))

				#事前変換用ディレクトリパス
				pre_converted_dir = Path(temp_dir / 'pre_converted')

				#事前変換用ディレクトリ作成
				pre_converted_dir.mkdir()

				#個別変換用事前変換
				configure_progress_bar(0.01, i18n.t('ui.Progress_pre_conversion'), useGUI)
				pre_convert(values, values_ex, pre_converted_dir)

				#画像解像度がスクリプト側と一致しない時用
				values_ex['input_resolution'] = title_info.get('input_resolution')

				#アイコン取得用exeのパスを取得
				values_ex['icon_exe_path'] = get_iconexepath(values, title_info)

				#個別変換フラグ
				values_ex['select_individual_settings'] = True

				#inputを変換済みのファイルが入ったディレクトリで上書き - 以下元のinput参照不可になるので注意
				values['input_dir'] = pre_converted_dir


			#選択不可の動画形式選んでたらエラー
			if (values['vid_movfmt_radio'] in values_ex['disable_video']):
				raise Exception(i18n.t('ui.Unsupported_video_for_hardware'))

			#連番変換時画像サイズ先に代入
			if (values['vid_movfmt_radio'] == i18n.t('var.numbered_images')):
				configure_progress_bar(0.02, i18n.t('ui.Progress_set_sequential_images'), useGUI)
				values_ex['renbanresper'] = getvidrenbanres(values)

			#0.txtのテキスト取得
			configure_progress_bar(0.023, i18n.t('ui.Progress_get_scenario_text'), useGUI)
			values_ex['0txtscript'] = onsscript_decode(values)

			#0.txtのテキストから各種情報取得
			configure_progress_bar(0.026, i18n.t('ui.Progress_get_scenario_info'), useGUI)
			values_ex = onsscript_check(values, values_ex)

			#0.txtのコメントアウト削除
			if values['etc_0txtremovecommentout_chk']:
				configure_progress_bar(0.029, i18n.t('ui.Progress_remove_scenario_comments'), useGUI)
				values_ex['0txtscript'] = remove_0txtcommentout(values_ex)

			#nsa/sar展開
			configure_progress_bar(0.03, i18n.t('ui.Progress_extract_archive'), useGUI)
			values_ex = extract_nsa(values, values_ex, extracted_dir, useGUI)#進捗 0.03→0.045

			#画像/音楽/動画/その他のファイルを仕分け
			configure_progress_bar(0.048, i18n.t('ui.Progress_set_extracted_data'), useGUI)
			cnvset_dict = create_cnvsetdict(values, values_ex, extracted_dir)

			#変換本処理
			configure_progress_bar(0.05, i18n.t('ui.Progress_convert_extracted_data'), useGUI)
			values_ex = convert_files(values, values_ex, cnvset_dict, extracted_dir, converted_dir, useGUI)#進捗 0.05→0.95

			#変換済ファイルをnsaに圧縮
			configure_progress_bar(0.95, i18n.t('ui.Progress_rebuild_archive'), useGUI)
			compressed_nsa(converted_dir, compressed_dir, useGUI)#進捗 0.95→0.98

			#savedataフォルダ作成(無いとエラー出す作品向け)
			create_savedatadir(values_ex, compressed_dir)

			#機種固有コンフィグファイル作成
			configure_progress_bar(0.98, i18n.t('ui.Progress_create_config'), useGUI)
			create_configfile(values, values_ex, compressed_dir)

			#アイコンPNG作成
			if values['etc_getgameicon_chk']: create_iconpng(values, values_ex, compressed_dir)

			#0.txt書き出し
			configure_progress_bar(0.982, i18n.t('ui.Progress_write_converted_scenario'), useGUI)
			create_0txt(values, values_ex, compressed_dir)

			#完成品移動
			configure_progress_bar(0.985, i18n.t('ui.Progress_move_all_data'), useGUI)
			debug_copy(values, compressed_dir)
			result_move(result_dir, compressed_dir)

			#まもなく完了します
			configure_progress_bar(0.99, i18n.t('ui.Progress_almost_done'), useGUI)

	except Exception as e:
		message_box(i18n.t('ui.Error'), e, 'error', useGUI)
	
	else:
		end_time = time.perf_counter()
		c_time = math.ceil(end_time-start_time)
		m = str(c_time // 60).zfill(2)
		s = str(c_time % 60).zfill(2)
		
		cnvmsg = i18n.t('ui.Conversion_complete_time').replace(r'{m}', m).replace(r'{s}', s)

		message_box(i18n.t('ui.Conversion_complete_title'), cnvmsg, 'info', useGUI)

		if (useGUI):
			configure_progress_bar(1, i18n.t('ui.Conversion_complete_title'), True)
			

			#入出力初期化
			dpg.set_value('input_dir', '')
			dpg.set_value('title_setting', 'None')

	#GUI時
	if (useGUI):
		configure_progress_bar(0, ' ', True)

		#再び全要素入力可能に
		for i in dpg.get_aliases():
			try: dpg.enable_item(i)
			except: pass
