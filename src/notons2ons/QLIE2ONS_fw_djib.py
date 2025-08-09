#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import concurrent.futures
import shutil, tempfile, re
import subprocess as sp


# if文管理用
class IfClass:
	"""if文管理用 多重ifに対応、caseにも一応対応だが、多重caseはめんどいので非対応(そんなのあるのか？)"""

	# コンストラクタ
	def __init__(self):
		self.useiflist = []
		self.count = 0

		self.casevar = ''
		self.casecount = 0

	#####
	def appendUseif(self, useif):
		self.useiflist.append(useif)
	
	def getUseif(self):
		return self.useiflist[-1]
	
	def popUseif(self):
		return self.useiflist.pop()

	def incrementCount(self):
		self.count += 1
	
	def getCount(self):
		return self.count
	
	#####
	def setCaseVar(self, casevar):
		self.casevar = casevar

	def getCaseVar(self):
		return self.casevar
	
	def incrementCaseCount(self):
		self.casecount += 1
	
	def resetCaseCount(self):
		self.casecount = 0
	
	def getCaseCount(self):
		return self.casecount


# 変数管理用
class VarClass:
	"""変数管理用"""

	# コンストラクタ
	def __init__(self):
		self.vardict = {}
		self.num  =  50

	# 変数名数字変換
	def str2var(self, str):
		if re.fullmatch(r'[0-9]+', str): return str
		
		str = lower_AtoZ(str)

		if not self.vardict.get(str):
			self.vardict[str] = self.num
			self.num += 1
		
		# ResultStr[0] ← こいつ以外文字なさそうなんで
		if (str in [r'resultstr[0]']):
			r = f'${self.vardict[str]}'

		else:
			r = f'%{self.vardict[str]}'
	
		return r

	# デバッグ用	
	def getverdict(self):
		return self.vardict


# エフェクト管理用
class EffectClass:
	"""エフェクト管理用"""

	# コンストラクタ
	def __init__(self):
		self.eflist = []
		self.num  =  10

	# 数値化
	def getefdict(self, str, num):

		for t in self.eflist:
			if ((str == t[0]) and (num == t[1])):
				return t[2]
		
		self.num += 1
		self.eflist.append((str, num, self.num))
		return self.num

	# リスト返却
	def geteflisttxt(self):
		txt = ''
		for t in self.eflist:
			if t[0]:
				print('特殊エフェクト要作成')
			else:
				txt += f'effect {t[2]},10,{t[1]}\n'
		
		return txt


# 作品について
def title_info():
	return {
		'brand': 'FrontWing',
		'date': 20040423,
		'title': '魔界天使ジブリール',
		'cli_arg': 'fw_djib',
		'requiredsoft': [],
		'is_4:3': True,
		'exe_name': ['Djibril'],

		'version': [
			'魔界天使ジブリール DLsite DL版(VJ005527)',
		],

		'notes': [
			'旧パッケージ版(Vista対応版ではないもの)はそもそも変換非対応',
			'好感度調整の実装が不完全なため分岐はすべて選択肢で実装',
			'一部シナリオ遷移が不自然(同じ日常会話が繰り返し出るなど)',
			'アモーレ収集選択は全部固定(一応クリア後回想から全て閲覧可)',#タイトル画面作るまでは無理
		]

		# !!! まだマルチコンバータ組み込みでは動作しません !!!
		# 単体動作は可能、BAD以外のルートは一通り動作確認済み
	}


# リソース自動展開 (マルチコンバータ組み込み時にのみ利用)
def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	# from utils import extract_archive_garbro # type: ignore

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	gamedata_dir = Path(input_dir / 'GameData')

	# 動画コピー
	Path(pre_converted_dir / 'movie').mkdir(parents=True, exist_ok=True)
	for mov_path in Path(gamedata_dir / 'movie').glob('*.mpg'):
		mov_copypath = Path(pre_converted_dir / 'movie' / mov_path.name)
		if not mov_copypath.exists(): shutil.copy(mov_path, mov_copypath)

	# 一時ディレクトリ作成
	with tempfile.TemporaryDirectory() as pack_tmpdir:
		pack_tmpdir = Path(pack_tmpdir)

		# pack展開
		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
			futures = []

			for pack_path in gamedata_dir.glob('data*.pack'):
				pack_copypath = Path(pack_tmpdir / pack_path.stem)
				futures.append(executor.submit(extract_archive_garbro, pack_path, pack_copypath))
			
			concurrent.futures.as_completed(futures)

		# 展開物をpack順に上書きし統合
		pack_overwritedir = Path(pack_tmpdir / 'overwrite')
		for i in range(10):#本来pack3まででいいが念の為pack9まで対応
			pack_copypath = Path(pack_tmpdir / f'data{i}')
			if pack_copypath:
				for f in pack_copypath.glob('**/*'):
					if f.is_file():
						f2 = Path(pack_overwritedir / f.relative_to(pack_copypath))
						f2.parent.mkdir(parents=True, exist_ok=True)
						shutil.move(f, f2)

		# 拡張子".b"を探索し全てGARbroで展開する(元のファイルは削除)
		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
			futures = []

			for b_path in pack_overwritedir.glob('**/*.b'):
				futures.append(executor.submit(extract_archive_b, b_path))

			concurrent.futures.as_completed(futures)

		# 拡張子".bmp"のファイルを隔離
		pack_overwritebmpdir = Path(pack_tmpdir / 'overwrite_bmp')
		for f in pack_overwritedir.glob('**/*.bmp'):
			if f.is_file():
				f2 = Path(pack_overwritebmpdir / f.relative_to(pack_overwritedir))
				f2.parent.mkdir(parents=True, exist_ok=True)

				# 同名のpngがすでにある場合は競合防止の為bmpを削除
				f_png = Path(f.parent / f'{f.stem}.png')
				if f_png.is_file():
					f.unlink()
				else:
					shutil.move(f, f2)

		# 隔離したbmpファイルをzipで圧縮
		shutil.make_archive(pack_overwritebmpdir, format='zip', root_dir=pack_overwritebmpdir)
		shutil.rmtree(pack_overwritebmpdir)

		# 圧縮したzipをGARbroで(PNGへ変換しながら)展開
		pack_overwritebmpzip = Path(pack_tmpdir / 'overwrite_bmp.zip')
		extract_archive_garbro(pack_overwritebmpzip, pack_overwritebmpdir, 'png')
		pack_overwritebmpzip.unlink()

		# 展開ファイルをpack_overwritedirへ戻す
		for f in pack_overwritebmpdir.glob('**/*'):
			if f.is_file():
				f2 = Path(pack_overwritedir / f.relative_to(pack_overwritebmpdir))
				shutil.move(f, f2)
		
		# pre_converted_dirへ移動
		for f in pack_overwritedir.glob('*'):
			f2 = Path(pre_converted_dir / f.relative_to(pack_overwritedir))
			shutil.move(f, f2)

	return


# .bファイル展開処理用関数
def extract_archive_b(b_path: Path):
	b_oldpath = Path(b_path.parent / f'{b_path.stem}_.b')
	shutil.move(b_path, b_oldpath)
	extract_archive_garbro(b_oldpath, b_path)
	b_oldpath.unlink()



#################### kari #####################
# 正式組み込み時に消す
def extract_archive_garbro(p: Path, e: Path, f: str = ''):
	GARbro_Path = Path(r'C:/_software/_zisaku/NSC2ONS4PSP/tools/Garbro_console/GARbro.Console.exe')#location('GARbro')
	e.mkdir()
	if f:
		l = [GARbro_Path, 'x', '-if', f.lower(), '-ca', '-o', e, p]
	else:
		l = [GARbro_Path, 'x', '-ca', '-o', e, p]
	sp.run(l)  # 展開
	return
###############################################

# 0.txtにはじめから書いておくもの (旧コンバータdefault.txt相当)
def default_txt(txt: str, val_txt: str = '', add0txt_effect: str = '', rs:str = '', sb:str = ''):

	return f''';mode800,value1000
*define
caption "魔界天使ジブリール Vista対応版 for ONScripter"
rmenu "ＳＡＶＥ",save,"ＬＯＡＤ",load,"ＳＫＩＰ",skip,"ＬＯＧ",lookback,"タイトル",reset
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
windowback
humanz 20
windowchip 8

{val_txt}


effect 10,10,50
{add0txt_effect}

pretextgosub *pretext_lb
defsub chara_def
defsub select_def
game
;----------------------------------------
*pretext_lb
	gettag $10,$11

	if $10!="" dwave 0,"voice/"+$10+".ogg"
	if $11!="" lsp 8,":s;#FFFFFF"+$11,80,440

	print 1
	saveon ;pretextgosub時終わりのsaveonは必須!!!!!!!!
return

*chara_def
	getparam $0,$1,$2
	;名前も変数管理しろ

	if $0=="" mov $21,"":mov $22,"":mov $23,"":csp 21:csp 22:csp 23

	if $0==$21 mov $21,"":csp 21
	if $0==$22 mov $22,"":csp 22
	if $0==$23 mov $23,"":csp 23

	if $0!="" if $2=="center" mov $21,$0:lsph 21,"image/ch/"+$0+"/long/"+$1+".png",0,0:getspsize 21,%0,%1:amsp 21,400-(%0/2),0:vsp 21,1
	if $0!="" if $2=="left"   mov $22,$0:lsph 22,"image/ch/"+$0+"/long/"+$1+".png",0,0:getspsize 22,%0,%1:amsp 22,200-(%0/2),0:vsp 22,1
	if $0!="" if $2=="right"  mov $23,$0:lsph 23,"image/ch/"+$0+"/long/"+$1+".png",0,0:getspsize 23,%0,%1:amsp 23,600-(%0/2),0:vsp 23,1
	;lsp 24,":s;#FFFFFF"+$21+" "+$22+" "+$23,80,410

	;例
	;"./image/ch/mei/long/meit000.png"
	;"mei", "meiT000", "center"

return

*select_def
	getparam $0,$1,$2,$3

	;とりあえず名前削除
	lsp 8,":s;#FFFFFF　",80,440

	;◆選択肢
	select $0,*sel0,
	       $1,*sel1,
		   $2,*sel2,
		   $3,*sel3
	
	*sel0
		mov {sb},0:return
	*sel1
		mov {sb},1:return
	*sel2
		mov {sb},2:return
	*sel3
		mov {sb},3:return
return
;----------------------------------------
*hselectmenu
mov %40,%40+1

;以下順番に流す
;2作るときは当然全変更

if %40==1  gosub *l_rikh_01a_op
if %40==2  gosub *l_rikh_02a_op
if %40==3  gosub *l_rikh_03a_op
if %40==4  gosub *l_rikh_01b_op
if %40==5  gosub *l_rikh_04a_op
if %40==6  gosub *l_rikh_09a_op
if %40==7  gosub *l_rikh_04b_op
if %40==8  gosub *l_rikh_09b_op
if %40==9  gosub *l_rikh_10a_op
if %40==10 gosub *l_rikh_05a_op
if %40==11 gosub *l_rikh_10b_op
if %40==12 gosub *l_rikh_05b_op
if %40==13 gosub *l_rikh_02b_op
if %40==14 gosub *l_rikh_06a_op
if %40==15 gosub *l_rikh_12a_op
if %40==16 gosub *l_rikh_12b_op
if %40==17 gosub *l_rikh_12c_op
if %40==18 gosub *l_rikh_08a_op
if %40==19 gosub *l_rikh_08b_op
if %40==20 gosub *l_rikh_08c_op

;エラー対策用 本来は選択したシナリオから直接gotoへ飛ぶ
goto *l_control_Hselect
;----------------------------------------
*ans_jump_192_1
;規定回数以上無駄行動取ったときそのまま例外飛ぶのでそれ対策
goto *l_control_Hselect
;----------------------------------------
*staffroll
;ルートフラグの変数取ってそれによって出す画像変える予定
すたっふろーる\\
return
;----------------------------------------
*start
mov %40,0
bg black,1
mov {rs},"test"
setwindow  50,470,25,2,26,26,0, 5,10,1,1,"library/avgsystem/img/outmessagewindow.png",  9,430
erasetextwindow 0	;0でエフェクト時window出っぱなし


;todo: タイトル作る
;本編で全シーン見れない以上回想モード実装は必須
;クリアフラグはスタッフロールに登録、どれか一つでもクリアしたら全回想開放で
;回想一括開放ボタンつけてもいいかもしれない

;debug
goto *l_op_op

end
;----------------------------------------
{txt}
'''


# アルファベットのみ小文字に変換する関数
def lower_AtoZ(s: str):

	# 変換を適用して返す
	return s.translate( str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') )


# 文字列置換
def message_replace(txt):
	cnvl = [
		['1', '１'], ['2', '２'], ['3', '３'], ['4', '４'], ['5', '５'], ['6', '６'], ['7', '７'], ['8', '８'], ['9', '９'], ['0', '０'],

		['a', 'ａ'], ['b', 'ｂ'], ['c', 'ｃ'], ['d', 'ｄ'], ['e', 'ｅ'], ['f', 'ｆ'], ['g', 'ｇ'], ['h', 'ｈ'], ['i', 'ｉ'], ['j', 'ｊ'],
		['k', 'ｋ'], ['l', 'ｌ'], ['m', 'ｍ'], ['n', 'ｎ'], ['o', 'ｏ'], ['p', 'ｐ'], ['q', 'ｑ'], ['r', 'ｒ'], ['s', 'ｓ'], ['t', 'ｔ'], 
		['u', 'ｕ'], ['v', 'ｖ'], ['w', 'ｗ'], ['x', 'ｘ'], ['y', 'ｙ'], ['z', 'ｚ'], 

		['A', 'Ａ'], ['B', 'Ｂ'], ['C', 'Ｃ'], ['D', 'Ｄ'], ['E', 'Ｅ'], ['F', 'Ｆ'], ['G', 'Ｇ'], ['H', 'Ｈ'], ['I', 'Ｉ'], ['J', 'Ｊ'], 
		['K', 'Ｋ'], ['L', 'Ｌ'], ['M', 'Ｍ'], ['N', 'Ｎ'], ['O', 'Ｏ'], ['P', 'Ｐ'], ['Q', 'Ｑ'], ['R', 'Ｒ'], ['S', 'Ｓ'], ['T', 'Ｔ'], 
		['U', '∪'], ['V', '∨'], ['W', 'Ｗ'], ['X', 'Ｘ'], ['Y', 'Ｙ'], ['Z', 'Ｚ'], 

		['%', '％'], ['!', '！'], ['?', '？'], [' ', '　'], 
		['/', '／'], ['\\', '￥'], ['(', '（'], [')', '）'], 
	]

	for v in cnvl: txt = txt.replace(v[0], v[1])
	return txt


# テキスト変換関数
def text_cnv(pre_converted_dir: Path, debug: bool):

	#　クラス
	ifclass = IfClass()
	varclass = VarClass()
	effectclass = EffectClass()

	# 結果テキスト行リスト
	resulttxtline = []
	
	# デバッグ用
	playcomlist = []
	varcomlist = []

	# フォルダ内のすべての.sファイルを探索して処理する
	for s_path in sorted(Path(pre_converted_dir / 'scenario').glob('*')):

		# sファイルを読み込み
		with open(s_path, 'r', encoding='cp932') as f:

			# 複数行コメントアウトフラグ
			multi_line_comment_flag = False
			
			# 文字列読み込み
			s = f.read()

			# 先頭に来てくれてない命令文を仕方なくここで置換
			# 他作品に使い回す場合ここのチェックできてないと一発アウトなので注意
			s = re.sub(r'//(.*?)\\then(.*?)\n', r'//\1＼then\2\n', s)
			s = re.sub(r'//(.*?)\\jmp(.*?)\n', r'//\1＼jmp\2\n', s)
			s = s.replace('\\then', '\n\\then')
			s = s.replace('\\jmp', '\n\\jmp')

			#topへ
			startlabelname = lower_AtoZ(f'l_{s_path.stem}_TOP')

			#感嘆符削除
			startlabelname = startlabelname.replace('!', '_')
			startlabelname = startlabelname.replace('&', '_')

			# ラベル名文字列チェック
			if not re.fullmatch(r'[A-z0-9_]+', startlabelname):
				print(f'ERROR: ラベル名が不正です. {startlabelname}')

			resulttxtline.append(f'*{startlabelname}')

			# 1行ずつ分割でfor
			for line in s.split('\n'):

				# 行頭行末スペースと行末の改行を削除
				line = re.fullmatch(r'(\s*)?(.+?)?(\s*)', line).group(2) or ''

				# コメント切り離し
				cmt_chk = re.fullmatch(r'(.*?)//(.*)', line)
				comment = ''
				if cmt_chk:
					line = cmt_chk.group(1) or ''
					comment = cmt_chk.group(2) or ''

				# 行頭行末スペースと行末の改行を削除(コメント切り離し後)
				line = re.fullmatch(r'(\s*)?(.+?)?(\s*)', line).group(2) or ''

				# lineがある(=空行ではない)場合
				if line:
					linelist = line.split(',')
										
					# マルチラインコメントアウトフラグ有効化
					if line.startswith('/*'):
						multi_line_comment_flag = True
						line = f';{line}'

					# マルチラインコメントアウトフラグ無効化
					elif line.startswith('*/'):
						multi_line_comment_flag = False
						line = f';{line}'

					# コメントフラグTrue時強制全コメント化
					elif multi_line_comment_flag:
						line = f';{line}'

					# 関数事前読み込み
					elif line.startswith('@@@'):
						# 全部 @@@Library\AVGSystem\header.s (システム関数事前読み込み)なので無視でおｋ
						line = f';{line}'

					# ラベル
					elif line.startswith('@@'):
						# memo:	別ファイルで同じ名前が使われることは全然ある
						# 		ファイル名+ラベル名→全部lowerが妥当か
						labelname = lower_AtoZ(f'l_{s_path.stem}_{line[2:]}')

						#感嘆符削除
						labelname = labelname.replace('!', '_')
						labelname = labelname.replace('&', '_')

						# ラベル名文字列チェック
						if not re.fullmatch(r'[A-z0-9_]+', labelname):
							print(f'ERROR: ラベル名が不正です. {labelname}')

						line = f'*{labelname}'
						

					# 表示、再生命令
					elif line.startswith('^'):
						line = lower_AtoZ(line) # 大文字小文字を揃える
						ll0 = lower_AtoZ(linelist[0]) # 先頭の命令を小文字に変換

						# bg0
						if (ll0 == '^bg0'):
							
							if (len(linelist) == 4):
								if (lower_AtoZ(linelist[2]) != 'overlap'): print('overlapじゃないよ')
								bg = linelist[1]
								t = int(linelist[3])
							elif (len(linelist) == 2):
								bg = linelist[1]
								t = 500
							elif (len(linelist) == 1):
								bg = 'black'
								t = 500
							else:
								print(f'エラーです: {linelist}')
							
							if debug: t /= 10
							
							line = (f'csp 8:csp 21:csp 22:csp 23:csp 99:erasetextwindow 1:bg "image/bg/{bg}.png",{effectclass.getefdict('', int(t))}:erasetextwindow 0')
						
						# cg0
						elif (ll0 == '^cg0'):
							if (len(linelist) >= 3):
								line = (f'csp 21:csp 22:csp 23:lsp 99,"image/evg/{linelist[1]}/{linelist[2]}.png",0,0')
							elif (len(linelist) == 1):
								line = ('csp 21:csp 22:csp 23:csp 99:print 10')
							else:
								print(f'エラーです: {linelist}')
						
						# chara
						elif (ll0 == '^chara'):
							# 無印/2はlongのみらしい 3はnearとtopで遠近差分合計3種
							# 後々のこと考えて全部ons変数持ちのほうがいいんじゃないかな

							if (len(linelist) == 5):#wait表示? 最後に数字あるけど無視
								line = (f'chara_def "{lower_AtoZ(linelist[1])}","{lower_AtoZ(linelist[2])}","{lower_AtoZ(linelist[3])}"')
								if not lower_AtoZ(linelist[3]) in ['center','left','right']:
									print(f'Error立ち絵: {linelist}')
							elif (len(linelist) == 4):#表示
								line = (f'chara_def "{lower_AtoZ(linelist[1])}","{lower_AtoZ(linelist[2])}","{lower_AtoZ(linelist[3])}"')
								if not lower_AtoZ(linelist[3]) in ['center','left','right']:
									print(f'Error立ち絵: {linelist}')
							elif (len(linelist) == 2):#削除?
								#print(line)
								line = (f'chara_def "","",""')
							elif (len(linelist) == 1):#削除
								# print(line)
								line = (f'chara_def "","",""')
							else:
								print(f'Error立ち絵: {linelist}')

						# effect
						elif (ll0 == '^effect'):
							
							if (lower_AtoZ(linelist[1]) == 'overlap'):
								
								if (len(linelist) == 4):
									ll2 = int(int(linelist[3]) / (debug*2))	
								elif (len(linelist) == 3):
									ll2 = int(int(linelist[2]) / (debug*2))
								elif (len(linelist) == 2):
									ll2 = 100
								else:
									print(f'Error effect: {linelist}')
									ll2 = 1
								
								line = f'print {effectclass.getefdict('', ll2)}'

							elif (lower_AtoZ(linelist[1]) == 'stop'):
								line = f'print 1'

							elif (lower_AtoZ(linelist[1]) == 'quake'):
								line = f'quake 4,{int(int(linelist[2]) / (debug*2))}'

							elif (lower_AtoZ(linelist[1]) == 'flash_$ffffffff'):
								line = f'lsp 98,"image/bg/white.png",0,0:print 10:wait 200:csp 98,print 10'

							elif (lower_AtoZ(linelist[1]) == 'flash_$ffff0000'):
								line = f'lsp 98,"image/bg/white.png",0,0:print 10:wait 200:csp 98,print 10'

							elif (lower_AtoZ(linelist[1]) == 'wipe_09'):
								line = f'print {effectclass.getefdict('', linelist[2])}'

							else:
								print(f'Error effect: {linelist}')

						# bgm
						elif (ll0 == '^bgm'):
							if (len(linelist) >= 2):
								line = f'bgm "bgm/{linelist[1]}.ogg"'
							elif (len(linelist) == 1):
								line = 'bgmstop'
							else:
								print(f'Error bgm: {linelist}')

						# movie
						elif (ll0 == '^movie'):
							if (len(linelist) == 3):
								line = f'stop:mpegplay "movie/{linelist[1].replace('"', '')}",{linelist[2]}'
								
						# se0
						elif (ll0 == '^se0'):
							if (len(linelist) >= 2):
								line = (f'dwave 1,"se/{linelist[1]}.ogg"')
							elif (len(linelist) == 1):
								line = 'dwavestop 1'
							else:
								print(f'Error se0: {linelist}')
						
						# se1
						elif (ll0 == '^se1'):
							if (len(linelist) >= 2):
								line = (f'dwave 2,"se/{linelist[1]}.ogg"')
							elif (len(linelist) == 1):
								line = 'dwavestop 2'
							else:
								print(f'Error se1: {linelist}')
						
						# voicedir
						elif (ll0 == '^voicedir'):
							if (linelist[1] == '"voice\\"') or (linelist[1] == '"voice\\""'):
								line = f';{line}'
							else:
								print(f'Error voicedir: {linelist}')

						# staffroll
						elif (ll0 == '^staffroll'):
							line = f'gosub *staffroll'
						
						# select
						elif (ll0 == '^select'):
							ll1 = linelist[1] if (len(linelist) > 1) else ''
							ll2 = linelist[2] if (len(linelist) > 2) else ''
							ll3 = linelist[3] if (len(linelist) > 3) else ''
							ll4 = linelist[4] if (len(linelist) > 4) else ''
							if (len(linelist) > 5): print(f'Error select: {linelist}')

							line = f'select_def "{ll1}","{ll2}","{ll3}","{ll4}"'

						#余り物
						else:
							if not (linelist[0] in [
								'^savetext', # セーブ時のタイトル 使う機会ないので無視
							]): playcomlist.append(linelist[0])
								
							line = f';{line}'
							
					# 変数制御、シナリオジャンプ命令
					elif line.startswith('\\'):
						line = lower_AtoZ(line) # 大文字小文字を揃える
						ll0 = lower_AtoZ(linelist[0]) # 先頭の命令を小文字に変換

						# if
						if (ll0 == '\\if'):
							ifmatch = re.fullmatch(r'([A-z0-9_\[\]]+|"(.*?)")[\t\s]*([<>!=]{1,2})[\t\s]*([A-z0-9_\[\]]+|"(.*?)")', linelist[1])

							# 左辺
							if re.fullmatch(r'([0-9]+|"(.*?)")', ifmatch.group(1)):
								lhs = ifmatch.group(1)
							else:
								lhs = f'{varclass.str2var(ifmatch.group(1))}'

							# 右辺
							if re.fullmatch(r'([0-9]+|"(.*?)")', ifmatch.group(4)):
								rhs = ifmatch.group(4)
							else:
								rhs = f'{varclass.str2var(ifmatch.group(4))}'

							line = (f'if {lhs}{ifmatch.group(3)}{rhs} goto *if_jump_{ifclass.getCount()}_true\n' +\
								f'goto *if_jump_{ifclass.getCount()}_false')
							
							ifclass.appendUseif(ifclass.getCount())
							ifclass.incrementCount()
						
						# ifが真
						elif (ll0 == '\\then'):
							line = (f'*if_jump_{ifclass.getUseif()}_true')

						# ifが偽
						elif (ll0 == '\\else'):
							line = (f'goto *if_end_{ifclass.getUseif()}\n' +\
								f'*if_jump_{ifclass.getUseif()}_false')
						
						# ifまたはcaseが終了
						elif (ll0 == '\\end'):
							if ifclass.getCaseCount():
								line = (f'*ans_jump_{ifclass.getCount()}_{ifclass.getCaseCount()}\n')
								ifclass.resetCaseCount()

							else:
								line = (f'*if_end_{ifclass.popUseif()}')

						# case
						elif (ll0 == '\\case'):
							if lower_AtoZ(linelist[1]) == 'g_day':
								line = (f';{line}')

							else:
								line = (f';{line}')

							ifclass.resetCaseCount()
							ifclass.setCaseVar(f'{varclass.str2var(linelist[1])}')
							ifclass.appendUseif(ifclass.getCount())
							ifclass.incrementCount()

						# ans
						elif (ll0 == '\\ans'):

							# ◯◯なら実行、ではなく◯◯ではないなら飛ばす、みたいな書き方
							line = (f'*ans_jump_{ifclass.getCount()}_{ifclass.getCaseCount()}\n' +\
			 							f'if {ifclass.getCaseVar()}!={linelist[1]} goto *ans_jump_{ifclass.getCount()}_{ifclass.getCaseCount()+1}')
							ifclass.incrementCaseCount()
						
						# jmp
						elif (ll0 == '\\jmp'):
							if (len(linelist) > 2):
								if (linelist[2] == '"Script\\HSelect\\HSelect.s"'):
									line = ('goto *hselectmenu')

								else:
									fn = re.fullmatch(r'"Scenario\\([A-z0-9-_]+)\.s"', linelist[2]).group(1)
									line = (f'goto *l_{fn}_{linelist[1][2:]}')

							else:
								line = (f'goto *l_{s_path.stem}_{linelist[1][2:]}')
						
						#cal
						elif (ll0 == '\\cal'):
							calstr = ''
							for n in re.findall(r'[a-zA-Z_]\w*|\d+|[=+-]', linelist[1]):
								calstr += n if (n in ['=', '+', '-']) else f'{varclass.str2var(n)}'

							calstrs = calstr.split('=')
							line = (f'mov {calstrs[0]},{calstrs[1]}')

						#wait
						elif (ll0 == '\\wait'):
							# 一個引数いっぱいあったのあるけど無視
							wt = int(linelist[1])
							if debug: wt /= 10# debug時短く	
							line = (f'wait {int(wt)}')
						
						#余り物
						else:
							if (linelist[0] in [
								'\\var', # ['\\var', 'img', 'nBlackBG'] のみ 詳細不明
								'\\del', # ['\\del', 'nBlackBG'] のみ 詳細不明
								'\\d',   # アクチ処理っぽい 消す
								'\\ret', # エフェクト終了待ち？ とりあえず消す
								'\\play',# エンド処理のなにか？ とりあえず消す
								'\\sub', # ['\\sub', '@@!FWActivateCheck', '"FW\\FWSystem.s"'] アクチ処理っぽい 消す
								'\\scp', # 多分回想フラグ関係 めんどいので消す
								'\\sc',  # 多分回想フラグ関係 めんどいので消す
								'\\?sr', # 多分回想フラグ関係 めんどいので消す
								'\\clk', # クリック待ちっぽい 引数は知らん
								'\\lkc', # 機能ロック関連 めんどいので消す
								'\\lk',  # 機能ロック関連2 めんどいので消す
								'\\l',   # エンディングでしか使ってないなにか めんどいので消す
								'\\r',   # エンディングでしか使ってないなにか めんどいので消す
								'\\i',   # エンディングでしか使ってないなにか めんどいので消す
								'\\e',   # エンディングでしか使ってないなにか めんどいので消す
								'\\p',   # エンディングでしか使ってないなにか めんどいので消す
							]):
								line = f';{line}'
							else:
								varcomlist.append(linelist[0])

					# 文章
					else:
						if (len(linelist) == 1):
							line = f'[/　]{
									message_replace(linelist[0].replace(r'[n]', '\n'))
								}\\'
						else:
							line = f'[{
									linelist[0]
								}/{
									re.fullmatch(r'(.+?)(＠.+)?', linelist[1]).group(1)#名前＠別名 表記なんで別名取る
								}]{
									message_replace(linelist[2].replace(r'[n]', '\n'))
								}\\'

				# コメントがある場合
				if comment:
					line += f';;;;;{comment}'

				# 行追加
				resulttxtline.append(line)
			
			resulttxtline.append('reset')

	# 0.txt作成
	txt = default_txt(
		txt = '\n'.join(resulttxtline),
		add0txt_effect = effectclass.geteflisttxt(),
		rs = varclass.str2var('ResultStr[0]'),
		sb = varclass.str2var('_selectButton'),
	)
	
	# ガバガバ修正シリーズ
	txt = txt.replace(r'if %51<%52', '') # よく分からんけどこれ潰すと動くので
	txt = txt.replace(r'ミスティメイ＠芽衣美', r'ミスティメイ')#名前修正
	txt = txt.replace(r'if %57==1 ', r'')#必殺習得とそれ以外で分岐あるシーン強制的に潰す
	txt = txt.replace(r'if %57==2 ', r'')#必殺習得とそれ以外で分岐あるシーン強制的に潰す
	txt = txt.replace(r'if %57==3 ', r'')#必殺習得とそれ以外で分岐あるシーン強制的に潰す
	txt = txt.replace(r'if %57==4 ', r'')#必殺習得とそれ以外で分岐あるシーン強制的に潰す
	txt = txt.replace(r'if %57==5 ', r'')#必殺習得とそれ以外で分岐あるシーン強制的に潰す
	txt = txt.replace(r'if %53==1 goto *if_jump_1_true',#1-1
		r'goto *l_bat_1_01_Bat_1_01_D')#r'select "必殺技を覚えている", *l_bat_1_01_Bat_1_01_C,"必殺技を覚えていない",*l_bat_1_01_Bat_1_01_D')
	txt = txt.replace(r'if %53==1 goto *if_jump_5_true',#1-2
		r'select "必殺技を覚えている", *l_bat_1_02_Bat_1_02_C,"必殺技を覚えていない",*l_bat_1_02_Bat_1_02_D')
	txt = txt.replace(r'if %53==1 goto *if_jump_9_true',#2-1
		r'goto *l_bat_2_01_Bat_2_01_D')#r'select "エンジェリック分身を覚えている", *l_bat_2_01_Bat_2_01_C,"覚えていない",*l_bat_2_01_Bat_2_01_D')
	txt = txt.replace(r'if %53==0 goto *if_jump_13_true',#2-2
		r'select "必殺技を覚えている", *l_bat_2_02_Bat_2_02_D,"必殺技を覚えていない",*l_bat_2_02_Bat_2_02_E')
	txt = txt.replace(r'if %53==1 goto *if_jump_17_true',#3-1
		r'goto *l_bat_3_01_Bat_3_01_D')#r'select "天使の秘儀を覚えている", *l_bat_3_01_Bat_3_01_C,"天使の秘儀を覚えていない",*l_bat_3_01_Bat_3_01_D')
	txt = txt.replace(r'if %53==1 goto *if_jump_21_true',#3-2
		r'select "天使の秘儀を覚えている", *l_bat_3_02_Bat_3_02_C,"天使の秘儀を覚えていない",*l_bat_3_02_Bat_3_02_D')
	txt = txt.replace(r'if %53==1 goto *if_jump_25_true',#4-1
		r'goto *l_bat_4_01_Bat_4_01_D')#r'select "天使の秘儀を覚えている", *l_bat_4_01_Bat_4_01_C,"天使の秘儀を覚えていない",*l_bat_4_01_Bat_4_01_D')
	txt = txt.replace(r'if %53==1 goto *if_jump_33_true',#4-2
		r'select "天使の秘儀を覚えている", *l_bat_4_02_Bat_4_02_C,"天使の秘儀を覚えていない",*l_bat_4_02_Bat_4_02_D')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_4_true',
		r'select "アモーレがたまっている", *l_bat_1_02_Bat_1_02_A,"アモーレがたまってない",*l_bat_1_02_Bat_1_02_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_0_true',
		r'select "アモーレがたまっている", *l_bat_1_01_Bat_1_01_A,"アモーレがたまってない",*l_bat_1_01_Bat_1_01_B')
	txt = txt.replace(r'goto *if_jump_4_false',
		r'select "アモーレがたまっている", *l_bat_1_02_Bat_1_02_A,"アモーレがたまってない",*l_bat_1_02_Bat_1_02_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_8_true',
		r'select "アモーレが貯まっている", *l_bat_2_01_Bat_2_01_A,"アモーレが貯まっていない",*l_bat_2_01_Bat_2_01_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_12_true',
		r'select "アモーレが貯まっている", *l_bat_2_02_Bat_2_02_A,"アモーレが貯まっていない",*l_bat_2_02_Bat_2_02_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_16_true',
		r'select "アモーレが貯まっている", *l_bat_3_01_Bat_3_01_A,"アモーレが貯まっていない",*l_bat_3_01_Bat_3_01_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_20_true',
		r'select "アモーレが貯まっている", *l_bat_3_02_Bat_3_02_A,"アモーレが貯まっていない",*l_bat_3_02_Bat_3_02_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_24_true',
		r'select "アモーレがたまっている", *l_bat_4_01_Bat_4_01_A,"アモーレがたまってない",*l_bat_4_01_Bat_4_01_B')
	txt = txt.replace(r'if %51>=%52 goto *if_jump_32_true',
		r'select "アモーレがたまっている", *l_bat_4_02_Bat_4_02_A,"アモーレがたまってない",*l_bat_4_02_Bat_4_02_B')
	txt = txt.replace(r'if %85<%86 goto *if_jump_212_true',
		r'select "ノーマルエッチを数多く行った場合", *l_rik_6_RikGoodEnd,"鬼畜エッチを数多く行った場合",*l_rik_6_RikBadEnd')
	txt = txt.replace(r'goto *l_control_Tale3Day7_4', r'goto *l_ntalk_day19ni')
	txt = txt.replace(r'goto *if_jump_168_false', r';goto *if_jump_168_false')
	txt = txt.replace(r'if %70==1 goto *if_jump_201_true',
		r'select "ラヴと過ごした場合", *l_ntalk_day1ni_A,"ラヴと過ごしてない",*l_ntalk_day1ni_B')
	txt = txt.replace(r'goto *l_control_LoveCheck',
		r'select "リカルートへ",*l_control_RikRoute,"メイルートへ",*l_control_MeiRoute,"ラヴリエルルートへ",*l_control_LovRoute')
	txt = txt.replace(r'select_def "３', r'goto *l_mselect_SMplay;')#最終シーン選択固定(同じシーン繰り返しを避けるため)
	txt = txt.replace(r'lsp 99,"image/evg/Rik/RI045b.png",0,0', r'lsp 99,"image/evg/Rik/RI045b.png",0,0:print 10:click')#鬼畜ENDCG即切れ防止
	txt = txt.replace(r'*l_bat_3_02_end', r'reset')#ここ負けても先進んでるので
	txt = txt.replace(r'*l_meih_4_01_return', r'goto *l_mei_4_06_op')
	txt = txt.replace(r'if %74==1 goto *if_jump_129_true',
		r'select "メイ純愛エンドへ",*l_mei_5_07_op,"メイ鬼畜エンドへ",*l_mei_5_07c_op,"メイＢＡＤエンドへ",*l_mei_5_07b_op')
	txt = txt.replace(r'goto *l_control_MeiBad2', r'gosub *staffroll:reset')#メイBAD強制終了するので対策
	txt = txt.replace(r'goto *if_jump_42_false', r'goto *l_ntalk_day23ni')
	txt = txt.replace(r'goto *if_jump_30_false', r'goto *l_lov_5_01_op')
	txt = txt.replace(r'*if_end_107', r'mov %58,1:goto *l_ntalk_tale5')
	txt = txt.replace('「大きなお世話だ」\\\n\n',#ラヴルート日付選択全滅なので手抜き１
		'「大きなお世話だ」\\\nprint 1:csp 8:csp 21:csp 22:csp 23:csp 99:erasetextwindow 1:bg "image/bg/Black.png",12:erasetextwindow 0:chara_def "","","":print 15:bgmstop:goto *l_control_lovtale5day2\n')
	txt = txt.replace(r'goto *if_jump_45_false', r'goto *l_ntalk_day28ni')
	txt = txt.replace('「お、おやすみ」\\\n\n', #ラヴルート日付選択全滅なので手抜き２
		'「お、おやすみ」\\\nprint 1:csp 8:csp 21:csp 22:csp 23:csp 99:erasetextwindow 1:bg "image/bg/Black.png",12:erasetextwindow 0:chara_def "","","":print 16:bgmstop:goto *l_lov_end_op\n')

	# 変換結果をファイルに保存
	with open(Path(pre_converted_dir / '0.txt'), mode='w') as f:
		f.write(txt)

	if set(varcomlist): print(f'未変換命令(変数制御):{set(varcomlist)}')
	if set(playcomlist): print(f'未変換命令(変数制御):{set(playcomlist)}')

	# print(varclass.getverdict())

	return


# メイン処理関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	# デバッグモード(_testディレクトリの有無で判断)
	debug = Path('./_test').is_dir()

	# マルチコンバータ利用時自動展開&デバッグモード強制解除
	if values:
		extract_resource(values, values_ex, pre_converted_dir)
		debug = False

	# デバッグモード時はリソース取得や0.txt作成を_testディレクトリ直下で行う
	if debug: pre_converted_dir /= '_test'

	# シナリオ変換処理
	text_cnv(pre_converted_dir, debug)

	# # 画像編集処理
	# image_processing(PATH_DICT, gauss_img_list, pre_converted_dir)

	# # 非デバッグモード時元シナリオ削除
	# if not debug: shutil.rmtree(PATH_DICT['scx'])
	
	# 終了
	return


# 単体動作 (事前にリソース手動展開必須)
if __name__ == "__main__":
	main()

	# 展開用(debug)
	# extract_resource({'input_dir': Path.cwd() / 'Djib_vista'}, {'num_workers':3}, Path.cwd() / '_test')
