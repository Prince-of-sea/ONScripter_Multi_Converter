#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp
import concurrent.futures
import tempfile, shutil, i18n, re

from requiredfile_locations import location
from utils import configure_progress_bar, extract_archive_garbro, subprocess_args, dir_allmove


def checknbz_nsa(p: Path):
	GARbro_Path = location('GARbro')
	garbrolist_raw = sp.check_output([
		GARbro_Path, 'l', p,
	],text=True, **subprocess_args(False))#check_output時はFalse 忘れずに

	l = []
	for f in re.findall(r'\[[A-F0-9]{8}\]\s+[0-9]+\s+(.+?)\n', garbrolist_raw):
		if str(Path(f).suffix).lower() == '.nbz': l.append(Path(f))

	return l


def getnsasar_pathlist(input_dir: Path):
	nsasar_pathlist = []
	
	if Path(input_dir / '00.ns2').exists():
		for i in range(1, 100):
			p = Path(input_dir / f'{str(i).zfill(2)}.ns2')
			if p.exists(): nsasar_pathlist.append(p)
			else: break

	elif Path(input_dir / 'arc.nsa').exists():
		nsasar_pathlist.append( Path(input_dir / 'arc.nsa') )
		for i in range(1, 10):
			p = Path(input_dir / f'arc{i}.nsa')
			if p.exists(): nsasar_pathlist.append(p)
			else: break

	elif Path(input_dir / 'arc.sar').exists():
		nsasar_pathlist += reversed(list(input_dir.glob('*.sar')))

	return nsasar_pathlist


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
		nsasar_pathlist = getnsasar_pathlist(input_dir)

		#arcな拡張子だけどarcとして使われてなさそうならno_archiveへコピー
		for p in (list(input_dir.glob('**/*.ns2')) + list(input_dir.glob('**/*.nsa'))):
			if (not p in nsasar_pathlist):	
				pdir = (no_archive / p.parent.relative_to(input_dir))
				pdir.mkdir(exist_ok=True)
				shutil.copy(p, pdir)

		#nbzリスト作成
		values_ex['nbzlist'] = []
		if (values['etc_0txtnbz_radio'] == i18n.t('var.convert_and_keep_both')):
			for nsasar_path in nsasar_pathlist:
				values_ex['nbzlist'] += checknbz_nsa(nsasar_path)

		#一度全て並列展開
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = []
			for nsasar_path in nsasar_pathlist:
				deftempnsasar_path = Path(deftemp_dir / nsasar_path.name)
				futures.append(executor.submit(extract_archive_garbro, nsasar_path, deftempnsasar_path))#nsaやsarを展開

			for i,ft in enumerate(concurrent.futures.as_completed(futures)):
				configure_progress_bar(0.03 + float(i / len(nsasar_pathlist) * 0.012), '', useGUI)#進捗 0.03→0.042
		
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
		
		configure_progress_bar(0.045, '', useGUI)#進捗 0.042→0.045

	return values_ex


def compressed_nsa_main(arc_dir: Path, compressed_dir: Path):
	nsaed_Path = location('nsaed')

	#nsaedコピー先パス
	nsaedcopy_Path = (arc_dir / 'nsaed.exe')

	#nsaedコピー
	shutil.copy(nsaed_Path, nsaedcopy_Path)

	#コピーしたnsaedを走らせる
	try: sp.call([nsaedcopy_Path, (arc_dir / 'arc_')], **subprocess_args())
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
			configure_progress_bar(0.95 + float(i / len(list(converted_dir.glob('arc*'))) * 0.03), '', useGUI)#進捗 0.95→0.98
			
		concurrent.futures.as_completed(futures)

	#圧縮しないやつが存在する場合移動
	no_comp_dir = (converted_dir / 'no_comp' / 'arc_')
	if no_comp_dir.exists(): dir_allmove(no_comp_dir, compressed_dir)

	return
