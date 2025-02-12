from pathlib import Path
import concurrent.futures
import dearpygui.dearpygui as dpg
import tempfile, time, math, os

from requiredfile_locations import exist_env, exist_all
from hardwarevalues_config import gethardwarevalues
from conversion_video import getvidrenbanres, convert_video_renban2
from nsa_operations import extract_nsa, compressed_nsa
from conversion_etc import tryconvert, create_cnvsetdict
from process_notons import get_titledict, pre_convert
from ons_script import onsscript_decode, onsscript_check
from utils import configure_progress_bar, message_box, convert_askmsg
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

	#並列ファイル変換
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for f_path_re, f_dict in cnvset_dict.items():
			futures.append(executor.submit(tryconvert, values, values_ex, f_dict, f_path_re, converted_dir))
		
		for i,ft in enumerate(concurrent.futures.as_completed(futures)):
			if useGUI: configure_progress_bar(0.12 + (float(i / len(list(cnvset_dict))) * 0.78),'')#進捗 0.12→0.90

	#圧縮先チェック1 - arc1かarc2があるのにarcが無いなら
	if (not 'arc' in compchklist) and ( ('arc1' in compchklist) or ('arc2' in compchklist)):
		dummy_dir = Path(converted_dir / 'arc' / 'arc_' )
		dummy_dir.mkdir(parents=True, exist_ok=True)#とりあえずarc作って
		with open(Path(dummy_dir / '.dummy'), 'wb') as s: s.write(b'\xff')#ダミー突っ込んどく(ここ意味があるのか不明、未検証)
	
	#圧縮先チェック2 - arc2があるのにarc1が無いなら
	if (not 'arc1' in compchklist) and ('arc2' in compchklist):
		dummy_dir = Path(converted_dir / 'arc1' / 'arc_' )
		dummy_dir.mkdir(parents=True, exist_ok=True)#とりあえずarc1作って
		with open(Path(dummy_dir / '.dummy'), 'wb') as s: s.write(b'\xff')#ダミー突っ込んどく(ここ意味があるのか不明、未検証)

	#連番動画利用時はその画像を並列圧縮
	if isrenban:
		for f_dict in cnvset_dict.values():
			if (f_dict['fileformat'] == 'video'):
				#convert_video内で実装するとThreadPoolExecutorが競合しそうなのでこっちで処理
				convert_video_renban2(values, values_ex, f_dict)
	
	#エラーログ収集
	allerrlog = ''
	for errlogpath in converted_dir.glob('ERROR*'):
		with open(errlogpath, 'r') as er: allerrlog += er.read()
	
	values_ex['allerrlog'] = allerrlog
	return values_ex


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
		required_soft_list = ['GARBro', 'smjpeg_encode', 'nsaed']

		#タイトル個別処理辞書取得
		titledict = get_titledict()

		#個別選択時
		if values['title_setting'] in titledict.keys():
			title_info = titledict[ values['title_setting'] ]

			#確認
			if useGUI: configure_progress_bar(0, '個別設定変換確認...')
			if not convert_askmsg(useGUI, title_info): raise ValueError('変換がキャンセルされました')

			#必要ソフトを配列に代入
			required_soft_list += title_info['requiredsoft']

		#必要ソフトチェック
		if not exist_env('ffmpeg'): raise ValueError('ffmpegが用意されていません')
		if not exist_env('ffprobe'): raise ValueError('ffprobeが用意されていません')
		if not exist_all(required_soft_list): raise ValueError('必要なソフトが用意されていません')
		
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
			if useGUI: configure_progress_bar(0, '機種固有設定取得...')
			values_ex = gethardwarevalues(values['hardware'], 'values_ex')
			
			#並列処理用スレッド設定
			values_ex['num_workers'] = math.ceil(os.cpu_count() / 4) if (values.get('lower_cpu_usage')) else (os.cpu_count() + 4)#low時スレッド数/4繰り上げ、通常時スレッド数+4(初期値)

			#個別選択時
			if values['title_setting'] in titledict.keys():

				#個別タイトルが非4:3&変換先ハードが4:3限定(PSP除く)の場合
				if (not title_info['is_4:3']) and (values_ex['aspect_4:3only']) and (values['hardware'] != 'PSP'):

					#非対応解像度エラー
					raise ValueError('非対応解像度のため、このソフトは変換できません')

				#事前変換用ディレクトリパス
				pre_converted_dir = Path(temp_dir / 'pre_converted')

				#事前変換用ディレクトリ作成
				pre_converted_dir.mkdir()

				#個別変換用事前変換
				if useGUI: configure_progress_bar(0, '個別設定を元に事前変換...')
				pre_convert(values, values_ex, pre_converted_dir)

				#画像解像度がスクリプト側と一致しない時用
				values_ex['input_resolution'] = title_info.get('input_resolution')

				#inputを変換済みのファイルが入ったディレクトリで上書き - 以下元のinput参照不可になるので注意
				values['input_dir'] = pre_converted_dir

			#選択不可の動画形式選んでたらエラー
			if (values['vid_movfmt_radio'] in values_ex['disable_video']):
				raise ValueError('{hw}は動画を{v}形式に変換できません'.format(hw = values['hardware'], v = values['vid_movfmt_radio']))

			#連番変換時画像サイズ先に代入
			if (values['vid_movfmt_radio'] == '連番画像'):
				if useGUI: configure_progress_bar(0.01, '連番画像設定...')
				values_ex['renbanresper'] = getvidrenbanres(values)

			#0.txtのテキスト取得
			if useGUI: configure_progress_bar(0.02, 'シナリオテキスト取得...')
			values_ex['0txtscript'] = onsscript_decode(values)

			#0.txtのテキストから各種情報取得
			if useGUI: configure_progress_bar(0.03, 'シナリオ情報取得...')
			values_ex = onsscript_check(values, values_ex)

			#0.txtのコメントアウト削除
			if values['etc_0txtremovecommentout_chk']:
				if useGUI: configure_progress_bar(0.04, 'シナリオコメント削除...')
				values_ex['0txtscript'] = remove_0txtcommentout(values_ex)

			#nsa/sar展開
			if useGUI: configure_progress_bar(0.05, 'アーカイブ展開...')
			values_ex = extract_nsa(values, values_ex, extracted_dir, useGUI)		

			#画像/音楽/動画/その他のファイルを仕分け
			if useGUI: configure_progress_bar(0.10, '展開データ設定...')
			cnvset_dict = create_cnvsetdict(values, values_ex, extracted_dir)

			#変換本処理
			if useGUI: configure_progress_bar(0.12, '展開データ変換...')
			values_ex = convert_files(values, values_ex, cnvset_dict, extracted_dir, converted_dir, useGUI)
			
			#変換済ファイルをnsaに圧縮
			if useGUI: configure_progress_bar(0.90, 'アーカイブ再構築...')
			compressed_nsa(converted_dir, compressed_dir, useGUI)
			
			#savedataフォルダ作成(無いとエラー出す作品向け)
			create_savedatadir(values_ex, compressed_dir)
			
			#機種固有コンフィグファイル作成
			if useGUI: configure_progress_bar(0.96, 'コンフィグ作成...')
			create_configfile(values, values_ex, compressed_dir)

			#0.txt書き出し
			if useGUI: configure_progress_bar(0.97, '変換済みシナリオ書込み...')
			create_0txt(values, values_ex, compressed_dir)

			#完成品移動
			if useGUI: configure_progress_bar(0.98, '全データ移動...')
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