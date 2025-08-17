#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import concurrent.futures
import shutil, tempfile, re


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
				raise ValueError('特殊エフェクト要作成')
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
			'一部シナリオ遷移が不自然(同じ会話が繰り返し出るなど)',
			'セーブ、ロード、コンフィグ画面など基本UIは簡略化',
			'一部エフェクト(フラッシュなど)で立ち絵が消えない',
			'おまけは回想モード以外すべて未実装'
			'回想モードは最初から全部開放',
			'アモーレ収集選択は全部固定',
			'画面遷移はフェードのみ',
			'選択肢画面簡略化',
		]
	}



# リソース自動展開 (マルチコンバータ組み込み時にのみ利用)
def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

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
		
		# [djib専用]タイトル競合防止
		Path(pack_overwritedir / 'script' / 'title' / 'img' / 'titlebg.png').unlink()

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
	from utils import extract_archive_garbro # type: ignore
	
	b_oldpath = Path(b_path.parent / f'{b_path.stem}_.b')
	shutil.move(b_path, b_oldpath)
	extract_archive_garbro(b_oldpath, b_path)
	b_oldpath.unlink()


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

effect  8,10,500
effect  9,10,1000
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

mov %1000,1;クリア判定

stop:csp -1:print 1

bgm "image/etc/endroll.b/BGM17.ogg"
mov %2,0;表示用タイマー
resettimer

lsph 100,"image/etc/endroll.b/01.png",0,0:getspsize 100,%0,%1:amsp 100,400-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/02.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i01.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/03.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i02.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/04.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/05.png",0,0:getspsize 100,%0,%1:amsp 100,400-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/06.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i03.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/07.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/08.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i04.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/09.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/10.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i05.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/11.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/12.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i06.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/13.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/14.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i07.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/15.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/16.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i08.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/17.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/18.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i09.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/19.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/20.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i10.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/21.png",0,0:getspsize 100,%0,%1:amsp 100,400-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/22.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i11.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/23.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/24.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i12.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/25.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/26.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i13.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/27.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/28.png",0,0:getspsize 100,%0,%1:amsp 100,200-(%0/2),300-(%1/2):vsp 100,1
lsph 101,"image/etc/endroll.b/i14.png",0,0:getspsize 101,%0,%1:amsp 101,600-(%0/2),300-(%1/2):vsp 101,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2
lsph 100,"image/etc/endroll.b/29.png",0,0:getspsize 100,%0,%1:amsp 100,400-(%0/2),300-(%1/2):vsp 100,1
print 9
mov %2,%2+3800:waittimer %2
csp 100:csp 101
print 9
mov %2,%2+1900:waittimer %2

waittimer 167770
bgmstop
return
;----------------------------------------
*not_yet
lsp 10,":s;#FFFFFF#AAAAAA未実装です",334,287
lsp 11":c;>800,600,#000000",0,0,128
print 1
click
csp 11:csp 10
print 1
return
;----------------------------------------
*scenesel_start
bgmstop:csp -1:bg black,9
bg "script/scenemode/image/scenebg.png",8
lsp 200,":c;>800,600,#000000",0,0,128
bgm "bgm/BGM15.ogg"
mov %195,1
lsp 100,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０１ａ",     0,  0
lsp 101,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０１ｂ",     0, 25
lsp 102,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０１ｃ",     0, 50
lsp 103,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０２ａ",     0, 75
lsp 104,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０２ｂ",     0,100
lsp 105,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０２ｃ",     0,125
lsp 106,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０３ａ",     0,150
lsp 107,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０３ｂ",     0,175
lsp 108,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０３ｃ",     0,200
lsp 109,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０４ａ",     0,225
lsp 110,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０４ｂ",     0,250
lsp 111,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０４ｃ",     0,275
lsp 112,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０５ａ",     0,300
lsp 113,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０５ｂ",     0,325
lsp 114,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０５ｃ",     0,350
lsp 115,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０６ａ",     0,375
lsp 116,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０６ｂ",     0,400
lsp 117,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０６ｃ",     0,425
lsp 118,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０７ａ",     0,450
lsp 119,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０７ｂ",     0,475
lsp 120,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０７ｃ",     0,500
lsp 121,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０８ａ",     0,525
lsp 122,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０８ｂ",     0,550
lsp 123,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０８ｃ",     0,575
lsp 124,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０９ａ",   250,  0
lsp 125,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０９ｂ",   250, 25
lsp 126,":s;#FFFFFF#AAAAAAＲｉｋＨ＿０９ｃ",   250, 50
lsp 127,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１０ａ",   250, 75
lsp 128,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１０ｂ",   250,100
lsp 129,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１０ｃ",   250,125
lsp 130,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１１ａ",   250,150
lsp 131,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１１ｂ",   250,175
lsp 132,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１１ｃ",   250,200
lsp 133,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１２ａ",   250,225
lsp 134,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１２ｂ",   250,250
lsp 135,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１２ｃ",   250,275
lsp 136,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１３ａ",   250,300
lsp 137,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１３ｂ",   250,325
lsp 138,":s;#FFFFFF#AAAAAAＲｉｋＨ＿１３ｃ",   250,350
lsp 139,":s;#FFFFFF#AAAAAAｏｐ",               250,375
lsp 140,":s;#FFFFFF#AAAAAAＢａｔ＿１＿０１",   250,400
lsp 141,":s;#FFFFFF#AAAAAAＢａｔ＿１＿０２",   250,425
lsp 142,":s;#FFFFFF#AAAAAAＢａｔ＿２＿０１",   250,450
lsp 143,":s;#FFFFFF#AAAAAAＢａｔ＿２＿０２",   250,475
lsp 144,":s;#FFFFFF#AAAAAAＢａｔ＿３＿０１",   250,500
lsp 145,":s;#FFFFFF#AAAAAAＢａｔ＿３＿０２",   250,525
lsp 146,":s;#FFFFFF#AAAAAAＢａｔ＿４＿０１",   250,550
lsp 147,":s;#FFFFFF#AAAAAAＢａｔ＿４＿０２",   250,575
lsp 148,":s;#FFFFFF#AAAAAAＲｉｋ＿５",         500,  0
lsp 149,":s;#FFFFFF#AAAAAAＲｉｋ＿６",         500, 25
lsp 150,":s;#FFFFFF#AAAAAAｈｅｎｓｈｉｎ",     500, 50
lsp 151,":s;#FFFFFF#AAAAAAｌｏｖ＿４＿０１",   500, 75
lsp 152,":s;#FFFFFF#AAAAAAｌｏｖ＿５＿０１",   500,100
lsp 153,":s;#FFFFFF#AAAAAAｌｏｖ＿ｅｎｄ",     500,125
lsp 154,":s;#FFFFFF#AAAAAAＭｅｉ＿１＿０１ｂ", 500,150
lsp 155,":s;#FFFFFF#AAAAAAＭｅｉＨ＿１＿０１", 500,175
lsp 156,":s;#FFFFFF#AAAAAAＭｅｉＨ＿２＿０１", 500,200
lsp 157,":s;#FFFFFF#AAAAAAＭｅｉＨ＿２＿０２", 500,225
lsp 158,":s;#FFFFFF#AAAAAAＭｅｉＨ＿３＿０１", 500,250
lsp 159,":s;#FFFFFF#AAAAAAＭｅｉＨ＿３＿０２", 500,275
lsp 160,":s;#FFFFFF#AAAAAAＭｅｉＨ＿４＿０１", 500,300
lsp 161,":s;#FFFFFF#AAAAAAＭｅｉ＿５＿０３",   500,325
lsp 162,":s;#FFFFFF#AAAAAAＭｅｉ＿５＿０７",   500,350
lsp 163,":s;#FFFFFF#AAAAAAＭｅｉ＿５＿０７ｃ", 500,375

;めんどくなったので
lsp 164,":s;#FFFFFF☆☆☆☆☆☆☆☆☆☆", 525,425
lsp 165,":s;#FFFFFF再生後はメニューから", 525,450
lsp 166,":s;#FFFFFFタイトルに戻ってね　", 525,475
lsp 167,":s;#FFFFFF一部シーンは読み続け", 525,500
lsp 168,":s;#FFFFFFると強制終了するかも", 525,525
lsp 169,":s;#FFFFFF☆☆☆☆☆☆☆☆☆☆", 525,550

print 1

*scenesel_loop
	bclear
	spbtn 100,100
	spbtn 101,101
	spbtn 102,102
	spbtn 103,103
	spbtn 104,104
	spbtn 105,105
	spbtn 106,106
	spbtn 107,107
	spbtn 108,108
	spbtn 109,109
	spbtn 110,110
	spbtn 111,111
	spbtn 112,112
	spbtn 113,113
	spbtn 114,114
	spbtn 115,115
	spbtn 116,116
	spbtn 117,117
	spbtn 118,118
	spbtn 119,119
	spbtn 120,120
	spbtn 121,121
	spbtn 122,122
	spbtn 123,123
	spbtn 124,124
	spbtn 125,125
	spbtn 126,126
	spbtn 127,127
	spbtn 128,128
	spbtn 129,129
	spbtn 130,130
	spbtn 131,131
	spbtn 132,132
	spbtn 133,133
	spbtn 134,134
	spbtn 135,135
	spbtn 136,136
	spbtn 137,137
	spbtn 138,138
	spbtn 139,139
	spbtn 140,140
	spbtn 141,141
	spbtn 142,142
	spbtn 143,143
	spbtn 144,144
	spbtn 145,145
	spbtn 146,146
	spbtn 147,147
	spbtn 148,148
	spbtn 149,149
	spbtn 150,150
	spbtn 151,151
	spbtn 152,152
	spbtn 153,153
	spbtn 154,154
	spbtn 155,155
	spbtn 156,156
	spbtn 157,157
	spbtn 158,158
	spbtn 159,159
	spbtn 160,160
	spbtn 161,161
	spbtn 162,162
	spbtn 163,163
	
	btnwait %196
	
	;全部
	if %196!=-1 if %196!=0 stop:csp -1:bg black,10
	
	if %196==100 goto *l_RikH_01a_replay
	if %196==101 goto *l_RikH_01b_replay
	if %196==102 goto *l_RikH_01c_replay
	if %196==103 goto *l_RikH_02a_replay
	if %196==104 goto *l_RikH_02b_replay
	if %196==105 goto *l_RikH_02c_replay
	if %196==106 goto *l_RikH_03a_replay
	if %196==107 goto *l_RikH_03b_replay
	if %196==108 goto *l_RikH_03c_replay
	if %196==109 goto *l_RikH_04a_replay
	if %196==110 goto *l_RikH_04b_replay
	if %196==111 goto *l_RikH_04c_replay
	if %196==112 goto *l_RikH_05a_replay
	if %196==113 goto *l_RikH_05b_replay
	if %196==114 goto *l_RikH_05c_replay
	if %196==115 goto *l_RikH_06a_replay
	if %196==116 goto *l_RikH_06b_replay
	if %196==117 goto *l_RikH_06c_replay
	if %196==118 goto *l_RikH_07a_replay
	if %196==119 goto *l_RikH_07b_replay
	if %196==120 goto *l_RikH_07c_replay
	if %196==121 goto *l_RikH_08a_replay
	if %196==122 goto *l_RikH_08b_replay
	if %196==123 goto *l_RikH_08c_replay
	if %196==124 goto *l_RikH_09a_replay
	if %196==125 goto *l_RikH_09b_replay
	if %196==126 goto *l_RikH_09c_replay
	if %196==127 goto *l_RikH_10a_replay
	if %196==128 goto *l_RikH_10b_replay
	if %196==129 goto *l_RikH_10c_replay
	if %196==130 goto *l_RikH_11a_replay
	if %196==131 goto *l_RikH_11b_replay
	if %196==132 goto *l_RikH_11c_replay
	if %196==133 goto *l_RikH_12a_replay
	if %196==134 goto *l_RikH_12b_replay
	if %196==135 goto *l_RikH_12c_replay
	if %196==136 goto *l_RikH_13a_replay
	if %196==137 goto *l_RikH_13b_replay
	if %196==138 goto *l_RikH_13c_replay
	if %196==139 goto *l_op_replay
	if %196==140 goto *l_Bat_1_01_replay
	if %196==141 goto *l_Bat_1_02_replay
	if %196==142 goto *l_Bat_2_01_replay
	if %196==143 goto *l_Bat_2_02_replay
	if %196==144 goto *l_Bat_3_01_replay
	if %196==145 goto *l_Bat_3_02_replay
	if %196==146 goto *l_Bat_4_01_replay
	if %196==147 goto *l_Bat_4_02_replay
	if %196==148 goto *l_Rik_5_replay
	if %196==149 goto *l_Rik_6_replay
	if %196==150 goto *l_henshin_replay
	if %196==151 goto *l_lov_4_01_replay
	if %196==152 goto *l_lov_5_01_replay
	if %196==153 goto *l_lov_end_replay
	if %196==154 goto *l_Mei_1_01b_replay
	if %196==155 goto *l_MeiH_1_01_replay
	if %196==156 goto *l_MeiH_2_01_replay
	if %196==157 goto *l_MeiH_2_02_replay
	if %196==158 goto *l_MeiH_3_01_replay
	if %196==159 goto *l_MeiH_3_02_replay
	if %196==160 goto *l_MeiH_4_01_replay
	if %196==161 goto *l_Mei_5_03_replay
	if %196==162 goto *l_Mei_5_07_replay
	if %196==163 goto *l_Mei_5_07c_replay

	if %196==-1 reset
	if %196==0  reset
goto *scenesel_loop
;----------------------------------------
*start

;初回起動時 - 音量用変数すべて100
fileexist %130,"gloval.sav"
if %130==0 if %1030==0 if %1031==0 if %1032==0 mov %1030,60:mov %1031,60:mov %1032,60

bgmvol   %1030
sevol    %1031
voicevol %1032

mov %40,0
bg black,1
mov {rs},"test"
setwindow  50,470,25,2,26,26,0, 5,10,1,1,"library/avgsystem/img/outmessagewindow.png",  9,430
erasetextwindow 0	;0でエフェクト時window出っぱなし

bg black,1
bg "script/logo/img/logo.b/logo.png",9
wait 2500
bg black,9
bg "script/logo/img/caution.b/Cation.png",9
wait 2500
bg black,9

;タイトルbgm
bgm "bgm/BGM15.ogg"

lsp 61,":a/3,0,3;script/title/img/menu00_.png",458,244
lsp 62,":a/3,0,3;script/title/img/menu01_.png",458,304
lsp 63,":a/3,0,3;script/title/img/menu02_.png",458,364
lsp 64,":a/3,0,3;script/title/img/menu09_.png",458,424
lsp 65,":a/3,0,3;script/title/img/menu03_.png",458,484
lsp 66,":s;#FFFFFF#AAAAAA★",                  770,  5

lsp 99,"script/title/img/menuback01.png",430,210

bg "script/title/img/titlebg.png",8

*titlemenu_loop1
	bclear

	spbtn 61,61
	spbtn 62,62
	spbtn 63,63
	spbtn 64,64
	spbtn 65,65
	spbtn 66,66

	btnwait %0
	if %0!=-1 if %0!=0 dwave 1,"script/title/img/titlebutton.b/se502.ogg"

	if %0==61 csp -1:bg black 9:stop:mov %195,0:goto *l_op_op	;最初から
	if %0==62 systemcall load:goto *titlemenu_loop1				;続きから
	if %0==63 goto *titlemenu_2									;おまけ
	if %0==64 goto *titlemenu_3									;ｲﾝﾌｫﾒｰｼｮﾝ
	if %0==65 goto *titlemenu_4									;終わり
	if %0==66 csp -1:bg black 9:goto *volmenu_GUI				;音量設定(勝手に作った)
goto *titlemenu_loop1
;----------------------------------------
*titlemenu_2	;おまけ

vsp 61,0:vsp 62,0:vsp 63,0:vsp 64,0:vsp 65,0:vsp 66,0
print 8

lsp 71,":a/3,0,3;script/title/img/menu04_.png",458,244
lsp 72,":a/3,0,3;script/title/img/menu05_.png",458,304
lsp 73,":a/3,0,3;script/title/img/menu06_.png",458,364
lsp 74,":a/3,0,3;script/title/img/menu07_.png",458,424
lsp 75,":a/3,0,3;script/title/img/menu08_.png",458,484
print 8

*titlemenu_loop2
	bclear
	spbtn 71,71
	spbtn 72,72
	spbtn 73,73
	spbtn 74,74
	spbtn 75,75

	btnwait %0
	if %0!=-1 if %0!=0 dwave 1,"script/title/img/titlebutton.b/se502.ogg"

	if %0==71 gosub *not_yet:goto *titlemenu_loop2		;CG鑑賞
	if %0==72 goto *scenesel_start						;シーン回想
	if %0==73 gosub *not_yet:goto *titlemenu_loop2		;BGM鑑賞
	if %0==74 gosub *not_yet:goto *titlemenu_loop2		;ｴﾝﾃﾞｨﾝｸﾞﾁｪｯｸ

	;戻る
	if %0==75 bclear:csp 71:csp 72:csp 73:csp 74:csp 75:print 8
	if %0==75 vsp 61,1:vsp 62,1:vsp 63,1:vsp 64,1:vsp 65,1:vsp 66,1:goto *titlemenu_loop1
goto *titlemenu_loop2
;----------------------------------------
*titlemenu_3	;info

;menubackもかえる
vsp 61,0:vsp 62,0:vsp 63,0:vsp 64,0:vsp 65,0:vsp 66,0
print 8

lsp 99,"script/title/img/menuback00.png",430,240
print 1

lsp 81,":a/3,0,3;script/title/img/menu12_.png",458,274
lsp 82,":a/3,0,3;script/title/img/menu13_.png",458,364
lsp 83,":a/3,0,3;script/title/img/menu08_.png" 458,454
print 8


*titlemenu_loop3
	bclear
	spbtn 81,81
	spbtn 82,82
	spbtn 83,83

	btnwait %0
	if %0!=-1 if %0!=0 dwave 1,"script/title/img/titlebutton.b/se502.ogg"

	if %0==81 gosub *not_yet:goto *titlemenu_loop3	;ﾌﾛﾝﾄｳｲﾝｸﾞHP
	if %0==82 goto *titlemenu_5						;ゲームアワード

	;戻る
	if %0==83 bclear:csp 81,csp 82,csp 83:print 8
	if %0==83 lsp 99,"script/title/img/menuback01.png",430,210
	if %0==83 vsp 61,1:vsp 62,1:vsp 63,1:vsp 64,1:vsp 65,1:vsp 66,1:goto *titlemenu_loop1
goto *titlemenu_loop3
;----------------------------------------
*titlemenu_4	;終わり

lsp 29,"script/customexit/img/goend.png",170,240
lsp 21,":a/3,0,3;script/customexit/img/yes_.png",296,332
lsp 22,":a/3,0,3;script/customexit/img/no_.png",448,332
print 1

*titlemenu_loop4
	bclear
	spbtn 21,21
	spbtn 22,22

	btnwait %0
	if %0!=-1 if %0!=0 dwave 1,"script/title/img/titlebutton.b/se502.ogg"
	if %0!=-1 if %0!=0 csp 21:csp 22:csp 29:print 1	;どっちでも消すので

	if %0==21 wait 500:end			;はい
	if %0==22 goto *titlemenu_loop1	;いいえ
goto *titlemenu_loop4
;----------------------------------------
*titlemenu_5	;ゲームアワード

lsp 39,"image/bg/black.png",0,0
print 8

bgmstop
lsp 39,"script/award/awardbg.png",0,0
lsp 31,":a/3,0,3;script/award/url.b/discless01_URL_.png",100,400
lsp 32,":a/3,0,3;script/award/exit.b/exit_.png",410,512
print 8

*titlemenu_loop5
	bclear
	spbtn 31,31
	spbtn 32,32

	btnwait %0
	if %0!=-1 if %0!=0 dwave 1,"script/award/exit.b/ボタン効果音2.ogg"

	if %0==31 gosub *not_yet:goto *titlemenu_loop5	;link

	;exit
	if %0==32 csp 31:csp 32:lsp 39,"image/bg/black.png",0,0:print 8
	if %0==32 csp 39:print 8:bgm "bgm/BGM15.ogg":goto *titlemenu_loop3
goto *titlemenu_loop5
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意

	;背景
	lsp 200,":c;>800,600,#000000",0,0,192
	lsp 201"script/customconfig/img/soundbg.png",0,0
	
	;バー文字列定義
	mov $130,":s;#FFFFFF#666666○――――――――――"
	mov $131,":s;#FFFFFF#666666―○―――――――――"
	mov $132,":s;#FFFFFF#666666――○――――――――"
	mov $133,":s;#FFFFFF#666666―――○―――――――"
	mov $134,":s;#FFFFFF#666666――――○――――――"
	mov $135,":s;#FFFFFF#666666―――――○―――――"
	mov $136,":s;#FFFFFF#666666――――――○――――"
	mov $137,":s;#FFFFFF#666666―――――――○―――"
	mov $138,":s;#FFFFFF#666666――――――――○――"
	mov $139,":s;#FFFFFF#666666―――――――――○―"
	mov $140,":s;#FFFFFF#666666――――――――――○"
	
*volmenu_loop
	;取得
	getbgmvol   %1030
	getsevol    %1031
	getvoicevol %1032
	
	;文字列変換
	itoa2 $141,%1030
	itoa2 $142,%1031
	itoa2 $143,%1032
	
	;バー代入
	if %1030==  0 mov $146,$130
	if %1030== 10 mov $146,$131
	if %1030== 20 mov $146,$132
	if %1030== 30 mov $146,$133
	if %1030== 40 mov $146,$134
	if %1030== 50 mov $146,$135
	if %1030== 60 mov $146,$136
	if %1030== 70 mov $146,$137
	if %1030== 80 mov $146,$138
	if %1030== 90 mov $146,$139
	if %1030==100 mov $146,$140
	if %1031==  0 mov $147,$130
	if %1031== 10 mov $147,$131
	if %1031== 20 mov $147,$132
	if %1031== 30 mov $147,$133
	if %1031== 40 mov $147,$134
	if %1031== 50 mov $147,$135
	if %1031== 60 mov $147,$136
	if %1031== 70 mov $147,$137
	if %1031== 80 mov $147,$138
	if %1031== 90 mov $147,$139
	if %1031==100 mov $147,$140
	if %1032==  0 mov $148,$130
	if %1032== 10 mov $148,$131
	if %1032== 20 mov $148,$132
	if %1032== 30 mov $148,$133
	if %1032== 40 mov $148,$134
	if %1032== 50 mov $148,$135
	if %1032== 60 mov $148,$136
	if %1032== 70 mov $148,$137
	if %1032== 80 mov $148,$138
	if %1032== 90 mov $148,$139
	if %1032==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400,450
	lsp 132,":s;#FFFFFF#666666戻る",     550,450
	
	lsp 135,":s;#FFFFFFＢＧＭ",           50,150
	lsp 136,":s;#FFFFFF#666666＜",       200,150
	lsp 137,$146,                        250,150
	lsp 138,":s;#FFFFFF#666666＞",       550,150
	lsp 139,":s;#FFFFFF#666666"+$141,    600,150
	
	lsp 140,":s;#FFFFFFＳＥ",             50,250
	lsp 141,":s;#FFFFFF#666666＜",       200,250
	lsp 142,$147,                        250,250
	lsp 143,":s;#FFFFFF#666666＞",       550,250
	lsp 144,":s;#FFFFFF#666666"+$142,    600,250
	
	lsp 145,":s;#FFFFFFＶＯＩＣＥ",       50,350
	lsp 146,":s;#FFFFFF#666666＜",       200,350
	lsp 147,$148,                        250,350
	lsp 148,":s;#FFFFFF#666666＞",       550,350
	lsp 149,":s;#FFFFFF#666666"+$143,    600,350
	
	print 1
	
	;ボタン定義
	bclear
	spbtn 131,131
	spbtn 132,132
	spbtn 136,136
	spbtn 138,138
	spbtn 141,141
	spbtn 143,143
	spbtn 146,146
	spbtn 148,148
	
	;入力待ち
	btnwait %140
	if %140!=-1 if %140!=0 dwave 1,"script/customconfig/img/se901.ogg"
	
	if %140==131 bgmvol 100:sevol 100:voicevol 100
	if %140==132 csp -1:reset
	if %140==136 if %1030!=  0 sub %1030,10:bgmvol %1030
	if %140==138 if %1030!=100 add %1030,10:bgmvol %1030
	if %140==141 if %1031!=  0 sub %1031,10:sevol %1031
	if %140==143 if %1031!=100 add %1031,10:sevol %1031
	if %140==146 if %1032!=  0 sub %1032,10:voicevol %1032
	if %140==148 if %1032!=100 add %1032,10:voicevol %1032
	
goto *volmenu_loop
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
				raise ValueError(f'ERROR: ラベル名が不正です. {startlabelname}')

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
							raise ValueError(f'ERROR: ラベル名が不正です. {labelname}')

						line = f'*{labelname}'
						

					# 表示、再生命令
					elif line.startswith('^'):
						line = lower_AtoZ(line) # 大文字小文字を揃える
						ll0 = lower_AtoZ(linelist[0]) # 先頭の命令を小文字に変換

						# bg0
						if (ll0 == '^bg0'):
							
							if (len(linelist) == 4):
								if (lower_AtoZ(linelist[2]) != 'overlap'): raise ValueError('overlapじゃないよ')
								bg = linelist[1]
								t = int(linelist[3])
							elif (len(linelist) == 2):
								bg = linelist[1]
								t = 500
							elif (len(linelist) == 1):
								bg = 'black'
								t = 500
							else:
								raise ValueError(f'エラーです: {linelist}')
							
							if debug: t /= 10
							
							line = (f'csp 8:csp 21:csp 22:csp 23:csp 99:erasetextwindow 1:bg "image/bg/{bg}.png",{effectclass.getefdict('', int(t))}:erasetextwindow 0')
						
						# cg0
						elif (ll0 == '^cg0'):
							if (len(linelist) >= 3):
								line = (f'csp 21:csp 22:csp 23:lsp 99,"image/evg/{linelist[1]}/{linelist[2]}.png",0,0')
							elif (len(linelist) == 1):
								line = ('csp 21:csp 22:csp 23:csp 99:print 10')
							else:
								raise ValueError(f'エラーです: {linelist}')
						
						# chara
						elif (ll0 == '^chara'):
							# 無印/2はlongのみらしい 3はnearとtopで遠近差分合計3種
							# 後々のこと考えて全部ons変数持ちのほうがいいんじゃないかな

							if (len(linelist) == 5):#wait表示? 最後に数字あるけど無視
								line = (f'chara_def "{lower_AtoZ(linelist[1])}","{lower_AtoZ(linelist[2])}","{lower_AtoZ(linelist[3])}"')
								if not lower_AtoZ(linelist[3]) in ['center','left','right']:
									raise ValueError(f'Error立ち絵: {linelist}')
							elif (len(linelist) == 4):#表示
								line = (f'chara_def "{lower_AtoZ(linelist[1])}","{lower_AtoZ(linelist[2])}","{lower_AtoZ(linelist[3])}"')
								if not lower_AtoZ(linelist[3]) in ['center','left','right']:
									raise ValueError(f'Error立ち絵: {linelist}')
							elif (len(linelist) == 2):#削除?
								line = (f'chara_def "","",""')
							elif (len(linelist) == 1):#削除
								line = (f'chara_def "","",""')
							else:
								raise ValueError(f'Error立ち絵: {linelist}')

						# effect
						elif (ll0 == '^effect'):
							
							if (lower_AtoZ(linelist[1]) == 'overlap'):
								
								if (len(linelist) == 4):
									ll2 = int(int(linelist[3]) / (debug+1))	
								elif (len(linelist) == 3):
									ll2 = int(int(linelist[2]) / (debug+1))
								elif (len(linelist) == 2):
									ll2 = 100
								else:
									raise ValueError(f'Error effect: {linelist}')
									ll2 = 1
								
								line = f'print {effectclass.getefdict('', ll2)}'

							elif (lower_AtoZ(linelist[1]) == 'stop'):
								line = f'print 1'

							elif (lower_AtoZ(linelist[1]) == 'quake'):
								line = f'quake 4,{int(int(linelist[2]) / (debug+1))}'

							elif (lower_AtoZ(linelist[1]) == 'flash_$ffffffff'):
								line = f'lsp 98,"image/bg/white.png",0,0:print 10:wait 200:csp 98,print 10'

							elif (lower_AtoZ(linelist[1]) == 'flash_$ffff0000'):
								line = f'lsp 98,"image/bg/white.png",0,0:print 10:wait 200:csp 98,print 10'

							elif (lower_AtoZ(linelist[1]) == 'wipe_09'):
								line = f'print {effectclass.getefdict('', linelist[2])}'

							else:
								raise ValueError(f'Error effect: {linelist}')

						# bgm
						elif (ll0 == '^bgm'):
							if (len(linelist) >= 2):
								line = f'bgm "bgm/{linelist[1]}.ogg"'
							elif (len(linelist) == 1):
								line = 'bgmstop'
							else:
								raise ValueError(f'Error bgm: {linelist}')

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
								raise ValueError(f'Error se0: {linelist}')
						
						# se1
						elif (ll0 == '^se1'):
							if (len(linelist) >= 2):
								line = (f'dwave 2,"se/{linelist[1]}.ogg"')
							elif (len(linelist) == 1):
								line = 'dwavestop 2'
							else:
								raise ValueError(f'Error se1: {linelist}')
						
						# voicedir
						elif (ll0 == '^voicedir'):
							if (linelist[1] == '"voice\\"') or (linelist[1] == '"voice\\""'):
								line = f';{line}'
							else:
								raise ValueError(f'Error voicedir: {linelist}')

						# staffroll
						elif (ll0 == '^staffroll'):
							line = f'gosub *staffroll'
						
						# select
						elif (ll0 == '^select'):
							ll1 = linelist[1] if (len(linelist) > 1) else ''
							ll2 = linelist[2] if (len(linelist) > 2) else ''
							ll3 = linelist[3] if (len(linelist) > 3) else ''
							ll4 = linelist[4] if (len(linelist) > 4) else ''
							if (len(linelist) > 5): raise ValueError(f'Error select: {linelist}')

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
	txt = txt.replace('\n*l_control_hselect\n','\n*l_control_hselect\nif %195!=0 goto *scenesel_start\n')
	
	# 変換結果をファイルに保存
	with open(Path(pre_converted_dir / '0.txt'), mode='w') as f:
		f.write(txt)

	if set(varcomlist): raise ValueError(f'未変換命令(変数制御):{set(varcomlist)}')
	if set(playcomlist): raise ValueError(f'未変換命令(変数制御):{set(playcomlist)}')

	if debug: print(varclass.getverdict())

	return


# 画像処理関数 - 本体
def image_processing_main(input: Path, output: Path):

	# 入力画像を開く（RGBAに変換しておくと安全）
	img = Image.open(input).convert("RGBA")

	# サイズ取得
	w, h = img.size
	part_h = h // 3

	# 縦3分割
	parts = [img.crop((0, i * part_h, w, (i + 1) * part_h)) for i in range(3)]

	# 横に並べるので幅は3倍、高さは1/3
	new_img = Image.new("RGBA", (w * 3, part_h), (0, 0, 0, 0))

	# 貼り付け
	for i, part in enumerate(parts):
		new_img.paste(part, (i * w, 0))

	# 保存
	new_img.save(output)

	return


# 画像処理関数
def image_processing(pre_converted_dir: Path):

	# 並列
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		
		for r in range(14):
			
			# path
			input =  Path(pre_converted_dir / 'script' / 'title' / 'img' / f'menu{str(r).zfill(2)}.png')
			output = Path(pre_converted_dir / 'script' / 'title' / 'img' / f'menu{str(r).zfill(2)}_.png')
			
			futures.append(executor.submit(image_processing_main, input, output))

		futures.append(executor.submit(image_processing_main, 
			Path(pre_converted_dir / 'script' / 'award' / 'url.b' / 'discless01_URL.png'), 
			Path(pre_converted_dir / 'script' / 'award' / 'url.b' / 'discless01_URL_.png')))

		futures.append(executor.submit(image_processing_main, 
			Path(pre_converted_dir / 'script' / 'award' / 'exit.b' / 'exit.png'), 
			Path(pre_converted_dir / 'script' / 'award' / 'exit.b' / 'exit_.png')))

		futures.append(executor.submit(image_processing_main, 
			Path(pre_converted_dir / 'script' / 'customexit' / 'img' / 'yes.png'), 
			Path(pre_converted_dir / 'script' / 'customexit' / 'img' / 'yes_.png')))

		futures.append(executor.submit(image_processing_main, 
			Path(pre_converted_dir / 'script' / 'customexit' / 'img' / 'no.png'), 
			Path(pre_converted_dir / 'script' / 'customexit' / 'img' / 'no_.png')))
		
		concurrent.futures.as_completed(futures)

	return


# 不要ファイル削除関数
def junk_del(pre_converted_dir: Path):

	for p in pre_converted_dir.glob('**/*.ico'): p.unlink()
	for p in pre_converted_dir.glob('**/*.dat'): p.unlink()
	for p in pre_converted_dir.glob('**/*.s'): p.unlink()

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

	# 画像編集処理
	image_processing(pre_converted_dir)

	# 非デバッグモード時不要ファイル削除
	if not debug: junk_del(pre_converted_dir)
	
	# 終了
	return


# 単体動作 (事前にリソース手動展開必須)
if __name__ == "__main__":
	main()