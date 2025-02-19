#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import dearpygui.dearpygui as dpg
import tempfile, shutil, time, math, os

from requiredfile_locations import exist_env, exist_all
from hardwarevalues_config import gethardwarevalues, gethardwarevalues_full
from conversion_video import getvidrenbanres, convert_video_renban2
from nsa_operations import extract_nsa, compressed_nsa
from conversion_etc import tryconvert, create_cnvsetdict
from process_notons import get_titledict, pre_convert
from ons_script import onsscript_decode, onsscript_check
from utils import configure_progress_bar, message_box, get_dir_size
from misc import in_out_dir_check, remove_0txtcommentout, create_savedatadir, create_configfile, create_0txt, debug_copy, result_move


def convert_files(values: dict, values_ex: dict, cnvset_dict: dict, extracted_dir: Path, converted_dir: Path, useGUI: bool):
	num_workers = values_ex['num_workers']

	#圧縮先チェック用リスト
	compchklist = []

	#連番かな
	isrenban = bool(values['vid_movfmt_radio'] == '連番画像')

	#先にパスの代入&ディレクトリ作成
	for f_path_re, f_dict in cnvset_dict.items():
		#元nbzにフラグ付け
		f_dict['nbz'] = bool(f_path_re.with_suffix('.nbz') in values_ex['nbzlist'])

		#パスの代入
		f_dict['extractedpath'] = extracted_dir / f_path_re
		f_dict['convertedpath'] = converted_dir / f_dict['comp'] / 'arc_' / f_path_re

		#ディレクトリ作成
		f_dict['convertedpath'].parent.mkdir(parents=True, exist_ok=True)

		#圧縮先チェック用リスト追加
		compchklist.append(f_dict['comp'])

	#圧縮先チェック用リスト重複削除
	compchklist = list(set(compchklist))
	
	#並列ファイル変換時プログレスバー最大数設定
	cnvbarnum = 0.90 if (not isrenban) else 0.30

	#並列ファイル変換
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for f_path_re, f_dict in cnvset_dict.items():
			futures.append(executor.submit(tryconvert, values, values_ex, f_dict, f_path_re, converted_dir))
		
		for i,ft in enumerate(concurrent.futures.as_completed(futures)):
			if useGUI: configure_progress_bar(0.05 + (float(i / len(list(cnvset_dict))) * cnvbarnum),'')#進捗 0.05→0.95(連番時0.35)

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
				
	#2GB超えてるやつはnsa化させない
	for arc_dir_name in compchklist:
		arc_dir = Path(converted_dir / arc_dir_name / 'arc_' )
		dir_size_MB = math.ceil(get_dir_size(Path(arc_dir)) / 1024 / 1024)
	
		if (dir_size_MB >= 2000):#2000MB(≒2GB)以上なら
			compchklist.remove(arc_dir_name)#圧縮先チェック配列から削除

			for p in arc_dir.glob('**/*'):#中身全部移動
				if p.is_file():
					p_moved = Path(converted_dir / 'no_comp' / 'arc_' / p.relative_to(arc_dir))#移動先パス
					p_moved.parent.mkdir(parents=True, exist_ok=True)#移動先ディレクトリ作成
					shutil.move(p, p_moved)
			
			shutil.rmtree(arc_dir)#ディレクトリ削除			

	#圧縮先チェック1 - arc1かarc2があるのにarcが無いなら
	if (not 'arc' in compchklist) and ( ('arc1' in compchklist) or ('arc2' in compchklist)):
		dummy_dir = Path(converted_dir / 'arc' / 'arc_' )
		dummy_dir.mkdir(parents=True)#とりあえずarc作って
		with open(Path(dummy_dir / '.dummy'), 'wb') as s: s.write(b'\xff')#ダミー突っ込んどく(ここ意味があるのか不明、未検証)
	
	#圧縮先チェック2 - arc2があるのにarc1が無いなら
	if (not 'arc1' in compchklist) and ('arc2' in compchklist):
		dummy_dir = Path(converted_dir / 'arc1' / 'arc_' )
		dummy_dir.mkdir(parents=True)#とりあえずarc1作って
		with open(Path(dummy_dir / '.dummy'), 'wb') as s: s.write(b'\xff')#ダミー突っ込んどく(ここ意味があるのか不明、未検証)
	
	#エラーログ収集
	allerrlog = ''
	for errlogpath in converted_dir.glob('ERROR*'):
		with open(errlogpath, 'r', encoding='cp932') as er: allerrlog += er.read()
	
	values_ex['allerrlog'] = allerrlog
	return values_ex


def ask_convert_start(arg):
	configure_progress_bar(0, '変換開始...')

	titledict = get_titledict()

	#個別選択時
	if dpg.get_value('title_setting') in titledict.keys():
		title_info = titledict[ dpg.get_value('title_setting') ]
		configure_progress_bar(0, '個別設定変換確認...')
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

		s = ('=====================================================\n'\
			f'[変換先として指定可能なハード]{h_txt}\n\n'
			'=====================================================\n'\
			f'[追加で用意するソフト]{r_txt}\n\n'\
			'=====================================================\n'\
			f'[確認済み対応タイトル]{v_txt}\n\n'\
			'=====================================================\n'\
			f'[注意事項]{n_txt}\n\n'\
			'=====================================================\n'\
			)

		with dpg.mutex():
			with dpg.window(label=f'個別設定変換確認 - {title}', modal=True, no_close=True, no_move=True) as msg_askconv:
				with dpg.child_window(height=276, width=620):
					dpg.add_text(s)
				dpg.add_text("以上を確認したうえで、変換を開始しますか？")
				with dpg.group(horizontal=True):
					dpg.add_button(label="OK", user_data=(msg_askconv, True, arg), callback=askconv_callback)
					dpg.add_button(label="キャンセル", user_data=(msg_askconv, False, arg), callback=askconv_callback)
		dpg.split_frame()
	# 未指定なら確認を飛ばして変換開始
	else:
		return convert_start(arg)
	return


def askconv_callback(sender, app_data, user_data):
	dpg.configure_item(user_data[0], show=False)
	if user_data[1]:
		return convert_start(user_data[2])
	else:
		configure_progress_bar(0, '変換がキャンセルされました')
	return


def convert_start(arg):
	start_time = time.perf_counter()
	useGUI = bool(arg == r'convert_button')
	
	#GUI時
	if (useGUI):
		values = {}
		
		#一旦全要素入力不可に
		for i in dpg.get_aliases():
			try: dpg.disable_item(i)
			except: pass

			#ついでに辞書に入力値取得
			values[i] = dpg.get_value(i)
		
		configure_progress_bar(0, '変換開始...')
	
	else: values = arg

	#ここから処理
	try:
		required_soft_list = ['GARbro', 'smjpeg_encode', 'nsaed']

		#タイトル個別処理辞書取得
		titledict = get_titledict()

		#個別選択時
		if values['title_setting'] in titledict.keys():
			title_info = titledict[ values['title_setting'] ]

			#必要ソフトを配列に代入
			required_soft_list += title_info['requiredsoft']

		#必要ソフトチェック
		if not exist_env('ffmpeg'): raise FileNotFoundError('ffmpegが用意されていません')
		if not exist_env('ffprobe'): raise FileNotFoundError('ffprobeが用意されていません')
		if not exist_all(required_soft_list): raise FileNotFoundError('必要なソフトが用意されていません')
		
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
			result_dir = Path(values['output_dir'] / Path('result_{hw}_{n}'.format(hw = values['hardware'], n = str(values['input_dir'].name))))

			#データ置き場作成
			extracted_dir.mkdir()
			converted_dir.mkdir()
			compressed_dir.mkdir()

			#元valuesから計算処理かけて作った結果いれるところ+0.txt(&他)からすくい上げるもの
			if useGUI: configure_progress_bar(0.005, '機種固有設定取得...')
			values_ex = gethardwarevalues(values['hardware'], 'values_ex')
			
			#並列処理用スレッド設定
			values_ex['num_workers'] = math.ceil(os.cpu_count() / 4) if (values.get('lower_cpu_usage')) else (os.cpu_count() + 4)#low時スレッド数/4繰り上げ、通常時スレッド数+4(初期値)

			#個別選択時
			if values['title_setting'] in titledict.keys():

				#個別タイトルが非4:3&変換先ハードが4:3限定(PSP除く)の場合
				if (not title_info['is_4:3']) and (values_ex['aspect_4:3only']) and (values['hardware'] != 'PSP'):

					#非対応解像度エラー
					raise Exception('非対応解像度のため、このソフトは変換できません')

				#事前変換用ディレクトリパス
				pre_converted_dir = Path(temp_dir / 'pre_converted')

				#事前変換用ディレクトリ作成
				pre_converted_dir.mkdir()

				#個別変換用事前変換
				if useGUI: configure_progress_bar(0.01, '個別設定を元に事前変換...')
				pre_convert(values, values_ex, pre_converted_dir)

				#画像解像度がスクリプト側と一致しない時用
				values_ex['input_resolution'] = title_info.get('input_resolution')

				#inputを変換済みのファイルが入ったディレクトリで上書き - 以下元のinput参照不可になるので注意
				values['input_dir'] = pre_converted_dir

			#選択不可の動画形式選んでたらエラー
			if (values['vid_movfmt_radio'] in values_ex['disable_video']):
				raise Exception('{hw}は動画を{v}形式に変換できません'.format(hw = values['hardware'], v = values['vid_movfmt_radio']))

			#連番変換時画像サイズ先に代入
			if (values['vid_movfmt_radio'] == '連番画像'):
				if useGUI: configure_progress_bar(0.02, '連番画像設定...')
				values_ex['renbanresper'] = getvidrenbanres(values)

			#0.txtのテキスト取得
			if useGUI: configure_progress_bar(0.023, 'シナリオテキスト取得...')
			values_ex['0txtscript'] = onsscript_decode(values)

			#0.txtのテキストから各種情報取得
			if useGUI: configure_progress_bar(0.026, 'シナリオ情報取得...')
			values_ex = onsscript_check(values, values_ex)

			#0.txtのコメントアウト削除
			if values['etc_0txtremovecommentout_chk']:
				if useGUI: configure_progress_bar(0.029, 'シナリオコメント削除...')
				values_ex['0txtscript'] = remove_0txtcommentout(values_ex)

			#nsa/sar展開
			if useGUI: configure_progress_bar(0.03, 'アーカイブ展開...')
			values_ex = extract_nsa(values, values_ex, extracted_dir, useGUI)#進捗 0.03→0.045

			#画像/音楽/動画/その他のファイルを仕分け
			if useGUI: configure_progress_bar(0.048, '展開データ設定...')
			cnvset_dict = create_cnvsetdict(values, values_ex, extracted_dir)

			#変換本処理
			if useGUI: configure_progress_bar(0.05, '展開データ変換...')
			values_ex = convert_files(values, values_ex, cnvset_dict, extracted_dir, converted_dir, useGUI)#進捗 0.05→0.95
			
			#変換済ファイルをnsaに圧縮
			if useGUI: configure_progress_bar(0.95, 'アーカイブ再構築...')
			compressed_nsa(converted_dir, compressed_dir, useGUI)#進捗 0.95→0.98
			
			#savedataフォルダ作成(無いとエラー出す作品向け)
			create_savedatadir(values_ex, compressed_dir)
			
			#機種固有コンフィグファイル作成
			if useGUI: configure_progress_bar(0.98, 'コンフィグ作成...')
			create_configfile(values, values_ex, compressed_dir)

			#0.txt書き出し
			if useGUI: configure_progress_bar(0.982, '変換済みシナリオ書込み...')
			create_0txt(values, values_ex, compressed_dir)

			#完成品移動
			if useGUI: configure_progress_bar(0.985, '全データ移動...')
			debug_copy(values, compressed_dir)
			result_move(result_dir, compressed_dir)

			#まもなく完了します
			if useGUI: configure_progress_bar(0.99, 'まもなく完了します...')

	except Exception as e:
		if (useGUI): message_box('エラー', e, 'error', useGUI)
		else: print('Error: ' + str(e))
	
	else:
		if (useGUI):
			end_time = time.perf_counter()
			c_time = math.ceil(end_time-start_time)
			m = str(c_time // 60).zfill(2)
			s = str(c_time % 60).zfill(2)

			configure_progress_bar(1, '変換完了')
			message_box('変換完了', '変換処理が終了しました\n処理時間: {m}分{s}秒'.format(m = m, s = s), 'info', useGUI)

			#入出力初期化
			dpg.set_value('input_dir', '')
			dpg.set_value('title_setting', '未指定')

	#GUI時
	if (useGUI):
		configure_progress_bar(0, ' ')

		#再び全要素入力可能に
		for i in dpg.get_aliases():
			try: dpg.enable_item(i)
			except: pass
