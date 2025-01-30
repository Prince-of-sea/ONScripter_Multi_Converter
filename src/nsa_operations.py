from pathlib import Path
import subprocess as sp
import concurrent.futures
import tempfile, shutil, re

from requiredfile_locations import location
from utils import configure_progress_bar, extract_archive_garbro, subprocess_args, dir_allmove


def checknbz_nsa(p: Path):
	GARBro_Path = location('GARBro')
	garbrolist_raw = sp.check_output([
		GARBro_Path, 'l', p,
	],text=True, shell=True, **subprocess_args(False))#check_output時はFalse 忘れずに

	l = []
	for f in re.findall(r'\[[A-F0-9]{8}\]\s+[0-9]+\s+(.+?)\n', garbrolist_raw):
		if str(Path(f).suffix).lower() == '.nbz': l.append(Path(f))

	return l


def extract_nsa(values: dict, values_ex: dict, extracted_dir: Path, useGUI: bool):
	input_dir = Path(values['input_dir'])

	#一時ディレクトリ作成	
	with tempfile.TemporaryDirectory() as deftemp_dir:
		deftemp_dir = Path(deftemp_dir)
		
		#まずnsa外、その他ファイルをコピー
		no_archive = Path(deftemp_dir / 'no_archive')
		shutil.copytree(input_dir, no_archive, ignore=shutil.ignore_patterns(
			'gloval.sav', 'envdata', 'nscript.dat', 'kidoku.dat', 'NScrflog.dat', 'NScrllog.dat',
			'*.sar', '*.nsa', '*.ns2', '*.exe', '*.txt', '*.ini', '*.ttf'))

		#存在するarcのパスをここで全てリスト化(もちろん上書き順は考慮)
		nsasar_pathlist = []
		nsasar_pathlist += sorted(list(input_dir.glob('*.ns2')))
		nsasar_pathlist += reversed(list(input_dir.glob('*.nsa')))
		nsasar_pathlist += reversed(list(input_dir.glob('*.sar')))

		#nbzリスト作成
		values_ex['nbzlist'] = []
		if (values['etc_0txtnbz_radio'] == '変換後のファイルを拡張子nbzとwavで両方用意しておく'):
			for nsasar_path in nsasar_pathlist:
				values_ex['nbzlist'] += checknbz_nsa(nsasar_path)

		#一度全て並列展開
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = []
			for nsasar_path in nsasar_pathlist:
				deftempnsasar_path = Path(deftemp_dir / nsasar_path.name)
				futures.append(executor.submit(extract_archive_garbro, nsasar_path, deftempnsasar_path))#nsaやsarを展開

			for i,ft in enumerate(concurrent.futures.as_completed(futures)):
				if useGUI: configure_progress_bar(0.05 + float(i / len(nsasar_pathlist) * 0.05), '')#進捗 0.05→0.10
		
			concurrent.futures.as_completed(futures)
		
		#移動用に直置きファイル置き場を配列最後に追加
		nsasar_pathlist.append(Path('no_archive'))

		#展開したやつをnsa読み取り優先順に上書き移動
		for nsasar_path in nsasar_pathlist:
			deftempnsasar_path = Path(deftemp_dir / nsasar_path.name)	
			for f_path in deftempnsasar_path.glob('**/*'):
				if f_path.is_file():#ファイル(＝ディレクトリではない)なら処理
					f_movedpath = Path(str(extracted_dir / f_path.relative_to(deftempnsasar_path)).lower())#念の為全部小文字に
					f_movedpath.parent.mkdir(parents=True, exist_ok=True)
					if (values['etc_fileexdll_chk']) and (str(f_movedpath.suffix) == '.dll'): pass#dll無視
					elif (values['etc_fileexdb_chk']) and (str(f_movedpath.name) == 'thumbs.db'): pass#thumbs.db無視
					else: shutil.move(f_path, f_movedpath)

	return values_ex


def compressed_nsa_main(arc_dir: Path, compressed_dir: Path):
	nsaed_Path = location('nsaed')

	#nsaedコピー先パス
	nsaedcopy_Path = (arc_dir / 'nsaed.exe')

	#nsaedコピー
	shutil.copy(nsaed_Path, nsaedcopy_Path)

	#コピーしたnsaedを走らせる
	try: sp.call([nsaedcopy_Path, (arc_dir / 'arc_')], shell=True, **subprocess_args(True))
	except: dir_allmove((arc_dir / 'arc_'), compressed_dir)#異常終了時  - そのまま移動
	else: shutil.move((arc_dir / 'arc.nsa'), (compressed_dir / (str(arc_dir.name) + '.nsa')))#正常終了時 - nsa移動

	return


def compressed_nsa(converted_dir: Path, compressed_dir: Path, useGUI: bool):

	#並列圧縮処理
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []

		for arc_dir in converted_dir.glob('arc*'):
			futures.append(executor.submit(compressed_nsa_main, arc_dir, compressed_dir))

		for i,ft in enumerate(concurrent.futures.as_completed(futures)):
			if useGUI: configure_progress_bar(0.90 + float(i / len(list(converted_dir.glob('arc*'))) * 0.06), '')#進捗 0.90→0.96
			
		concurrent.futures.as_completed(futures)

	#圧縮しないやつが存在する場合移動
	no_comp_dir = (converted_dir / 'no_comp' / 'arc_')
	if no_comp_dir.exists(): dir_allmove(no_comp_dir, compressed_dir)

	return
