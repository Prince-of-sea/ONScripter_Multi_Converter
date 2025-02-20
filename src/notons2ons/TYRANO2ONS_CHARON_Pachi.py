#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageEnhance
import subprocess as sp
import concurrent.futures
import tempfile, shutil, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'CHARON',
		'date': 20230813,
		'title': '掴め、人生の右打ち!GOGO全回転 嵐を呼ぶ!炎のパチンカスロード',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'掴め、人生の右打ち!GOGO全回転 嵐を呼ぶ!炎のパチンカスロード DLsite DL版(RJ01067702 - 2023/08/13)',
		],

		'notes': [
			'UI周りはONS標準の最低限のみ、原作の仕様はほぼ無視',
			'スプライトのアニメーションはごく一部を除き未実装',
			'立ち絵の表示位置が原作と違う、また移動が未実装',
			'タイトル画面での鑑賞モードはOP再生テストに',
			'タイトル画面でのカスタムはゲーム終了に\nONScripterはその仕様上、ハード側での強制終了だと、グローバル変数(クリアフラグ等)が保存されません\nかならずこちらから終了するようにしてください'
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	input_dir = values['input_dir']

	p = Path(input_dir / 'パチンカスロード.exe')

	#なければ強制エラー
	if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))
	
	with tempfile.TemporaryDirectory() as td:
		e = Path(td / Path('dst'))
		extract_archive_garbro(p, e)
		shutil.move(Path(e / Path('data')), pre_converted_dir)

	return


def default_txt():
	s = ''';$V2000G200S1280,720L10000
*define

caption "パチンカスロード for ONScripter"

rmenu "Ｓａｖｅ",save,"Ｌｏａｄ",load,"Ｓｋｉｐ",skip,"Ｌｏｇ",lookback,"Ｃｌｏｓｅ",windowerase,"Ｔｉｔｌｅ",reset
savenumber 11
transmode alpha
globalon
rubyon
humanz 8
nsa
windowback

;---------- NSC2ONS4PSP強制変換機能ここから ----------
; 以下の文字列を認識すると、解像度に関わらず
; ONScripter_Multi_Converterの変換が可能になります
; PSP変換時でも座標ズレが発生しないようにしてください
; 
; <ONS_RESOLUTION_CHECK_DISABLED>
; 
;---------- NSC2ONS4PSP強制変換機能ここまで ----------
effect  9,10,100
effect 10,10,500

defsub voconfig_def
defsub charahide_def
defsub charashow_def
defsub charamod_def
defsub name_set
defsub swin
defsub csp

;<<-EFFECT->>

game
;----------------------------------------
*charahide_def
	getparam $1
	if $10==$1 csp 10
	if $11==$1 csp 11
	
return

*charashow_def
	getparam $1,$2
	
	getspsize 11,%0,%1
	getspsize 10,%2,%3
	
	if $11==$2 if %2==1 mov %0,1
	;ここ適当謎仕様すぎるので後日修正したほうがいいかも
	if %199!=1 if %0==1 mov $11,$2:lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,640-(%12/2):amsp 11,%8/%190,%191
	if %199!=1 if %0!=1 mov $10,$2:lsp 10,"data/fgimage/"+$1,0,0:getspsize 10,%14,%15:mov %8,853-(%14/2):amsp 10,%8/%190,%191
	if %199!=1 if %0!=1 getspsize 11,%12,%13:mov %8,427-(%12/2):                                         amsp 11,%8/%190,%191
	if %199==1 if %0==1 mov $11,$2:lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,640-(%12/2):amsp 11,%8*3/4/%190,%191
	if %199==1 if %0!=1 mov $10,$2:lsp 10,"data/fgimage/"+$1,0,0:getspsize 10,%14,%15:mov %8,853-(%14/2):amsp 10,%8*3/4/%190+30,%191
	if %199==1 if %0!=1 getspsize 11,%12,%13:mov %8,427-(%12/2):                                         amsp 11,%8*3/4/%190-30,%191

return

*charamod_def
	getparam $1,$2
	
	getspsize 11,%0,%1
	getspsize 10,%2,%3
	
	if $11==$2 if %2==1 mov %0,1
	;ここも適当謎仕様すぎるので後日修正したほうがいいかも
	if %199!=1 if %0==1 if $11==$2 lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,640-(%12/2):amsp 11,%8/%190,%191
	if %199!=1 if %0!=1 if $10==$2 lsp 10,"data/fgimage/"+$1,0,0:getspsize 10,%14,%15:mov %8,853-(%14/2):amsp 10,%8/%190,%191
	if %199!=1 if %0!=1 if $11==$2 lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,427-(%12/2):amsp 11,%8/%190,%191
	if %199==1 if %0==1 if $11==$2 lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,640-(%12/2):amsp 11,%8*3/4/%190,%191
	if %199==1 if %0!=1 if $10==$2 lsp 10,"data/fgimage/"+$1,0,0:getspsize 10,%14,%15:mov %8,853-(%14/2):amsp 10,%8*3/4/%190+30,%191
	if %199==1 if %0!=1 if $11==$2 lsp 11,"data/fgimage/"+$1,0,0:getspsize 11,%12,%13:mov %8,427-(%12/2):amsp 11,%8*3/4/%190-30,%191
return

*name_set
	getparam $1,$2
	if %199!=1 lsp 7,":s/26,26,0;#ffffff"+$2,150/%190  ,524/%190+%191	;名前の表示
	if %199==1 lsp 7,":s/14,14,0;#ffffff"+$2,150/%190-2,524/%190+%191	;名前の表示
	
;<<-VOICE_IF1->>
return

*voconfig_def
	getparam $1,%1
;<<-VOICE_IF2->>
return


*swin
	if %199!=1 setwindow 150/%190,570/%190+%191,37,3,25,25,1,2,25,0,1,"data/frame_message.png",0,445/%190+%191
	if %199==1 setwindow 150/%190,570/%190+%191,37,3,14,14,0,1,25,0,1,"data/frame_message.png",0,445/%190+%191+1
return

*csp
	;元のcspではgetspsizeが初期化されないので
	getparam %0
	lsph %0,":c;>1,1,#ffffff",0,0
	_csp %0
return
;----------------------------------------
*start

csp -1:print 1

;解像度が本来のものに一致しない場合PSP仕様へ
lsph 0,"data/bgimage_/title2.png",0,0

getspsize 0,%0,%1
if %0==1280 mov %199,0
if %0!=1280 mov %199,1

if %199==1 mov %190,2:mov %191,3
if %199!=1 mov %190,1:mov %191,0

;多分これで720pは誤魔化せる
;	普通の場合xy	:/%190
;	下辺合わせy		:/%190+%191

;（MP3(BGM) voice(DWAVE 0) SE(DWAVE 1～)
bgmvol 100		;BGM音量
voicevol 50	;ボイス音量
defsevol 80		;効果音音量
;mov %334,1		;クリア判定
swin
;----------------------------------------
bgm "data/bgm/m1.ogg"
dwave 1,"data/sound/yuria.ogg"

if %334==0 goto *1syu
if %334!=0 goto *2syu
;----------------------------------------
*1syu
lsp 9,"data/video/kin.webm.png",0,0
bg "data/bgimage_/title5.png",9

lsp 41,"data/image/title_/start.png", 1000/%190+%191,300/%190+%191
lsp 42,"data/image/title_/load.png",  1000/%190+%191,370/%190+%191
lsp 43,"data/image/title_/cgmode.png",1000/%190+%191,440/%190+%191
lsp 44,"data/image/title_/option.png",1000/%190+%191,510/%190+%191

lsp 51,"data/image/title/start.png", 1000/%190+%191,300/%190+%191
lsp 52,"data/image/title/load.png",  1000/%190+%191,370/%190+%191
lsp 53,"data/image/title/cgmode.png",1000/%190+%191,440/%190+%191
lsp 54,"data/image/title/option.png",1000/%190+%191,510/%190+%191

print 1

*title_loopA
	bclear
	btrans
	
	exbtn_d     "C41C42C43C44"
	exbtn 41,41,"P41C42C43C44"
	exbtn 42,42,"C41P42C43C44"
	exbtn 43,43,"C41C42P43C44"
	exbtn 44,44,"C41C42C43P44"
	
	print 1
	btnwait %50
	if %50==41 csp -1:stop:goto *game_start1
	if %50==42 systemcall load
	if %50==43 csp -1:stop:bg black,9:mpegplay "data/video/op.webm",1:reset
	if %50==44 csp -1:stop:bg black,9:end
	
goto *title_loopA
;----------------------------------------
*2syu

bg "data/bgimage_/title2.png",9

lsp 41,"data/image/title_/start2.png", 1000/%190+%191,300/%190+%191
lsp 42,"data/image/title_/load2.png",  1000/%190+%191,370/%190+%191
lsp 43,"data/image/title_/cgmode2.png",1000/%190+%191,440/%190+%191
lsp 44,"data/image/title_/option2.png",1000/%190+%191,510/%190+%191
lsp 45,"data/image/title_/extra2.png", 1000/%190+%191,580/%190+%191

lsp 51,"data/image/title/start2.png", 1000/%190+%191,300/%190+%191
lsp 52,"data/image/title/load2.png",  1000/%190+%191,370/%190+%191
lsp 53,"data/image/title/cgmode2.png",1000/%190+%191,440/%190+%191
lsp 54,"data/image/title/option2.png",1000/%190+%191,510/%190+%191
lsp 55,"data/image/title/extra2.png", 1000/%190+%191,580/%190+%191

print 1

*title_loopB
	bclear
	btrans
	
	exbtn_d     "C41C42C43C44C45"
	exbtn 41,41,"P41C42C43C44C45"
	exbtn 42,42,"C41P42C43C44C45"
	exbtn 43,43,"C41C42P43C44C45"
	exbtn 44,44,"C41C42C43P44C45"
	exbtn 45,45,"C41C42C43C44P45"
	
	print 1
	btnwait %50
	if %50==41 csp -1:stop:goto *game_start1
	if %50==42 systemcall load
	if %50==43 csp -1:stop:bg black,9:mpegplay "data/video/op.webm",1:reset
	if %50==44 csp -1:stop:bg black,9:end
	if %50==45 csp -1:stop:goto *game_start2
	
goto *title_loopB
;----------------------------------------
*game_start1
gosub *SCR_tatie_ks
gosub *SCR_purorogu_ks
reset
;----------------------------------------
*game_start2
gosub *SCR_tatie_ks
gosub *SCR_ex_ks
reset
;----------------------------------------
'''
	return s
#--------------------def--------------------
#ffmpeg存在チェック
def start_check():
	try: sp.run(['ffmpeg'])
	except: return False
	else: return True


# effect生成時に使う関数
def effect_edit(t,f, effect_startnum, effect_list):

	# 「何ミリ秒間」、「どの画像効果で」フェードするかを引数で受け取りeffect_listに記録、
	# エフェクト番号を(effect_startnumからの)連番で発行
	# また、過去に同一の秒数/画像の組み合わせを利用した場合は再度同じエフェクト番号になる
	list_num = 0
	if re.fullmatch(r'[0-9]+', t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum + 1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t, f])
			list_num = len(effect_list) + effect_startnum
	
	else:
		print('ERROR: effect指定ミス')

	return str(list_num), effect_startnum, effect_list


#吉里吉里の命令文及び変数指定をざっくりpythonの辞書に変換するやつ
def krcmd2krdict(c):
	kr_dict = {}

	for p in re.findall(r'([A-z0-9-_]+?)=(["|”|″](.*?)["|”|″]|([^\t\s]+))', c):
		kr_dict[p[0]] = p[2] if p[2] else p[3]

	return kr_dict


# ディレクトリの存在チェック関数
def dir_check(path_list):

	CHK = True
	for p in path_list:
		if not p.exists():
			print('ERROR: "' + str(p) + '" is not found!')
			CHK = False
			
	return CHK


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
		['/', '／'], ['\\', '￥'], 

		['ｺ', 'コ'], ['ﾎﾟ', 'ポ'], ['ﾎﾞ', 'ボ'], ['ｿ', 'ソ'], ['ｯ', 'ッ'], 
	]

	for v in cnvl: txt = txt.replace(v[0], v[1])
	return txt


def mov2PNG(p, x, y, values):
	p_tmp = Path(str(str(p) + '.png'))

	if values:
		from requiredfile_locations import location_env # type: ignore
		from utils import subprocess_args # type: ignore
		ffmpeg_Path = location_env('ffmpeg')
		sp.run([ffmpeg_Path, '-i', p, '-s', (str(x)+'x'+str(y)), '-frames:v', '1', '-y', p_tmp], shell=True, **subprocess_args())

	else:
		sp.run(['ffmpeg', '-i', p, '-s', (str(x)+'x'+str(y)), '-frames:v', '1', '-y', p_tmp], shell=True)

	im = Image.open(p_tmp)
	im.putalpha(im.convert('L'))
	im.save(p_tmp)
	p.unlink()#debug時消し


def mov2PNG_zugara2(p, values):#特別
	p_tmp = Path(str(str(p) + '_%02d.png'))
	p_result = Path(str(str(p) + '.png'))
	
	if values:
		from requiredfile_locations import location_env # type: ignore
		from utils import subprocess_args # type: ignore
		ffmpeg_Path = location_env('ffmpeg')
		sp.run([ffmpeg_Path, '-i', p, '-to', '00:00:05.666', '-vf', 'crop=250:140:0:0', '-r', '3', '-vcodec', 'png', '-y', p_tmp], text=True, shell=True, **subprocess_args(True))

	else:
		sp.run(['ffmpeg', '-i', p, '-to', '00:00:05.666', '-vf', 'crop=250:140:0:0', '-r', '3', '-vcodec', 'png', '-y', p_tmp], text=True, shell=True)

	im_tmp = Image.new('RGBA', size=(250*17, 140))
	for i,f in enumerate(Path(p.parent).glob('zugara2.webm_*.png')):
		im = Image.open(f)
		im.putalpha(im.convert('L'))
		im_tmp.paste(im,((250*i),0))
		f.unlink()

	im_tmp.save(p_result)


def bg_brightness_main(b):
	br = Path(b.parent.parent / 'title_' / b.name)
	if (b.suffix == '.png'):
		im = Image.open(b)
		imr = im.convert('RGBA')
		ime = ImageEnhance.Brightness(imr)  
		imr = ime.enhance(0.3)
		imr.save(br, format="PNG")
	
	return


def bg_brightness(image):
	Path(image.parent / 'title_').mkdir(exist_ok=True)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		for b in (image.glob('*.*')): futures.append(executor.submit(bg_brightness_main, b))
		concurrent.futures.as_completed(futures)

	return


def bg_resize_main(b):
	if ('koukoku' in str(b.name)):return#広告画像変換不要
	br = Path(b.parent.parent / 'bgimage_' / b.name)
	im = Image.open(b)
	imr = im.convert('RGBA').resize((1280, 720), Image.Resampling.LANCZOS)
	imr.save(br, format="PNG")
	return


def bg_resize(bgimage):
	Path(bgimage.parent / 'bgimage_').mkdir(exist_ok=True)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		for b in (bgimage.glob('*.*')): futures.append(executor.submit(bg_resize_main, b))
		concurrent.futures.as_completed(futures)

	return


def junk_del(PATH_DICT):

	#リスト内のディレクトリパスでfor
	for d in [PATH_DICT['scenario'], PATH_DICT['bgimage'], PATH_DICT['system'], PATH_DICT['others']]:
		shutil.rmtree(d)

	PATH_DICT['bgimage_zip'].unlink()
	PATH_DICT['DS_Store'].unlink()
	return


# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, scenario):

	# effect管理用変数
	effect_startnum = 10
	effect_list = []

	#default.txtを読み込み
	#with open(default, encoding='cp932', errors='ignore') as f: txt = f.read()
	txt = default_txt()

	#select文の選択肢文字列保持
	sel = []

	#キャラ設定管理 - どうせ初回に一括読み込みなのでpython側で変数取っちゃっていいかなって
	chara = {}
	chara_num = 151

	l = [
		Path(scenario / 'tatie.ks'),
		Path(scenario / 'purorogu.ks'),
		Path(scenario / 'ex.ks')
	]

	#シナリオファイルを読み込み
	for p in l:
		with open(p, encoding='utf-8', errors='ignore') as f:
			fr = f.read()

			fr = re.sub(r';(.*?)\n', '', fr)
			fr = fr.replace(r'[', '\n' + r'[')

			#これ絶対誤字でしょ
			fr = fr.replace(r'[chara_mod  name="yuria" face="1]', r'[chara_mod  name="yuria" face="1"]')

			#デコード済みtxt一つごとに開始時改行&サブルーチン化
			if DEBUG_MODE: txt += '\n;--------------- '+ str(p.name) +' ---------------'
			txt += ('\n*SCR_'+ str(p.name).replace('.', '_') +'\n\n')

			for line in fr.splitlines():
				kakko_line = re.search(r'\[(.+?)\]', line)
				kakko_line2 = re.search(r'@(.+)', line)
				name_line = re.match(r'#([A-z_]*)', line)

				#改行は無視
				if re.match(r'[\t\s]+\n', line + '\n'):
					line = ''

				#名前
				elif name_line:
					jname = chara[name_line[1]]['jname'] if name_line[1] else ''
					line = 'name_set "' + name_line[1] + '","' + jname + '"'

				#jump
				elif re.match(r'\*', line):
					line = ('*SCR_'+ line[1:])

				#命令文 - []内
				elif kakko_line or kakko_line2:
					
					if kakko_line: d = krcmd2krdict('kr_cmd=' + kakko_line[1])
					else:  d = krcmd2krdict('kr_cmd=' + kakko_line2[1])
					kr_cmd = d['kr_cmd']

					if kr_cmd == 'bg':
						d_method = d.get('method') if d.get('method') else 'crossfade'
						d_time = d.get('time') if d.get('time') else '500'
						if DEBUG_MODE: d_time = str(int(int(d_time) / 10))
						if d_time == '0': d_time = '1'
						
						s, effect_startnum, effect_list = effect_edit(d_time, d_method, effect_startnum, effect_list)
						line = 'csp 11:csp 10:bg "data\\bgimage_\\' + d['storage'] + '",' + s

					elif (kr_cmd == 'glink'):
						sel.append({'text':d['text'], 'target':d['target']})
						line = (';' + line) if DEBUG_MODE else ''

					elif (kr_cmd == 's'):
						if sel:
							line = 'select '
							for sd in sel: line += ('"'+sd['text']+'",*SCR_'+sd['target'][1:]+',')
							line = line[:-1]

						else:
							line = ''

						sel = []

					elif (kr_cmd == 'chara_new'):
						chara[d['name']] = {'jname': d['jname'], 'index': chara_num ,'face': {'default': d['storage']}}
						line = 'mov $' + str(chara_num) + ',"' + d['storage'] + '"'
						chara_num += 1

					elif (kr_cmd == 'chara_face'):
						chara[d['name']]['face'][d['face']] = d['storage']
						line = (';' + line) if DEBUG_MODE else ''

					elif (kr_cmd == 'chara_show'):
						d_method = d.get('method') if d.get('method') else 'crossfade'
						d_time = d.get('time') if d.get('time') else '500'
						s, effect_startnum, effect_list = effect_edit(d_time, d_method, effect_startnum, effect_list)
						line = 'charashow_def $' + str(chara[d['name']]['index']) + ',"' + d['name'] + '":print ' + s

					elif (kr_cmd == 'chara_mod'):
						line = 'mov $' + str(chara[d['name']]['index']) + ',"' + chara[d['name']]['face'][d['face']] + '":'
						line += 'charamod_def $' + str(chara[d['name']]['index']) + ',"'+d['name']+'":print 9'

					elif (kr_cmd == 'chara_hide'):
						line = 'charahide_def "'+d['name']+'":print 9'

					elif (kr_cmd == 'chara_hide_all'):
						line = 'csp 11:csp 10:print 10'

					elif (kr_cmd == 'p'):
						line = '\\'
					
					elif (kr_cmd == 'r'):
						line = r'@'

					elif (kr_cmd == 'voconfig'):
						line = 'voconfig_def "' + d['name'] + '",' + d['number']

					elif (kr_cmd == 'quake'):
						hmax = d.get('hmax') if d.get('hmax') else '2'
						line = 'quake ' + hmax + ',' + d['time']

					elif (kr_cmd == 'layopt'):
						line = ''#使うのほぼウィンドウ関係だから消してるけど本来レイヤー表示命令

					elif (kr_cmd == 'eval'):
						line = 'mov %334,1'#本来は変数管理全般 だが今作だとTrueEndチェックくらいしかしてなさそう

					elif (kr_cmd == 'jump'):
						#storage指定がある→別ファイル呼び出し→多分gameover→ならreturnでいいよね
						if d.get('storage'): line = 'return'
						else: line = 'goto *SCR_' + d['target'][1:]

					elif (kr_cmd == 'wait'):
						d_time = d.get('time') if d.get('time') else '500'
						if DEBUG_MODE: d_time = str(int(int(d_time) / 10))
						line = 'wait ' + d_time

					elif (kr_cmd == 'playbgm'):
						if (d['loop'] == 'true'):
							line = 'bgm "data/bgm/' + d['storage'] + '"'
						elif (d['storage'] == 'nanairo2ban.ogg'):#ここbgmだと動画と競合するので例外
							line = 'dwave 2,"data/bgm/' + d['storage'] + '"'
						else:
							line = 'bgmonce "data/bgm/' + d['storage'] + '"'

					elif (kr_cmd in ['stopbgm', 'fadeoutbgm']):
						line = 'bgmstop'

					elif (kr_cmd == 'playse'):
						if (d['loop'] == 'true'):
							line = 'dwaveloop 1,"data/sound/' + d['storage'] + '"'
						else:
							line = 'dwave 1,"data/sound/' + d['storage'] + '"'

					elif (kr_cmd == 'stopse'):
						line = 'dwavestop 1'

					elif (kr_cmd == 'movie'):
						line = 'mpegplay "data/video/' + d['storage'] + '",0'
						if (d['storage'] =='zenkaiten.webm'): line += ':dwavestop 2'#↑例外の後処理

					elif (kr_cmd == 'layermode_movie'):
						if(d['loop']=='false'):#これic.webmなので一般動画と同じ扱いで良い
							line = 'mpegplay "data/video/' + d['video'] + '",0'
						elif(d['video']=='zugara2.webm'):#図柄回転は意地でもアニメーション再現したかった
							line = 'lsp 9,":a/17,333,0;data/video/' + d['video'] + '.png",0,0:print 1'
						else:
							line = 'lsp 9,"data/video/' + d['video'] + '.png",0,0:print 1'

					elif (kr_cmd == 'free_layermode'):
						line = 'csp 9:print 10'

					elif (kr_cmd == 'l'):
						line = ''#ほぼrと出るタイミング一緒

					elif (kr_cmd == 'cg'):
						line = ''#CG開放 今回アルバム封印のため未使用

					elif (kr_cmd == 'mtext'):
						line = ''#text="BAD END『相合傘』"との表記 没シナリオ？別作品の流用？

					elif (kr_cmd in ['mask_off', 'resetfont', 'font', 'wa', 'cm','clearfix','anim','start_keyconfig','vostart', 'chara_move', 'showmenubutton', 'add_theme_button', 'hidemenubutton', 'button']):
						line = ''#めんどくなってきたのでまとめて削除

					#他
					else:
						if DEBUG_MODE: print(kr_cmd)
						line = (';' + line) if DEBUG_MODE else ''

				#その他 - たぶんこれ文章
				else:
					line = message_replace(line)

				#変換した命令行が空ではない場合
				if line: txt += (line + '\n')#入力




	# エフェクト定義用の配列を命令文に&置換
	add0txt_effect = ''
	add0txt_voiceif1 = ''
	add0txt_voiceif2 = ''

	for k, v in chara.items():
		add0txt_voiceif1 += ('if $1=="' + k + '" itoa $0,%' + str(v['index']) + ':wait 30:dwave 0,"data/sound/' + k + '/"+$0+".ogg":inc %' + str(v['index']) + '\n')
		add0txt_voiceif2 += ('if $1=="' + k + '" mov %' + str(v['index']) + ',%1\n')

	for i,e in enumerate(effect_list,effect_startnum+1): add0txt_effect +='effect ' + str(i) + ',10,'+e[0]+'\n'
	txt = txt.replace(r';<<-VOICE_IF1->>', add0txt_voiceif1)
	txt = txt.replace(r';<<-VOICE_IF2->>', add0txt_voiceif2)
	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)
	txt += '\nreturn'

	#出力結果を書き込み
	open(zero_txt, 'w', encoding='cp932', errors='ignore').write(txt)

	return


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	elif not start_check():
		print('ffmpeg is not exist.')
		return

	# デバッグモード
	debug = 0

	#同一階層のパスを変数へ代入
	same_hierarchy = pre_converted_dir#Path.cwd()

	#debug時にtestフォルダに入れないやつ(default.txt等)はこっちを利用
	#same_hierarchy_const = same_hierarchy

	#デバッグ時はtestディレクトリ直下
	if debug: same_hierarchy = (same_hierarchy / '_test')

	#利用するパスを辞書に入れ一括代入
	PATH_DICT = {
		#先に準備しておくべきファイル一覧
		'bgimage' :(same_hierarchy / 'data' / 'bgimage'),
		'bgm' :(same_hierarchy / 'data' / 'bgm'),
		'fgimage' :(same_hierarchy / 'data' / 'fgimage'),
		'image' :(same_hierarchy / 'data' / 'image'),
		'others' :(same_hierarchy / 'data' / 'others'),
		'scenario' :(same_hierarchy / 'data' / 'scenario'),
		'sound' :(same_hierarchy / 'data' / 'sound'),
		'system' :(same_hierarchy / 'data' / 'system'),
		'video' :(same_hierarchy / 'data' / 'video'),

		'bgimage_zip' :(same_hierarchy / 'data' / 'bgimage.zip'),
		'DS_Store' :(same_hierarchy / 'data' / '.DS_Store'),

		#'default':(same_hierarchy_const / 'default.txt'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'0_txt' :(same_hierarchy / '0.txt'),
	}

	#ディレクトリの存在チェック
	dir_check_result = dir_check(PATH_DICT.values())

	#存在しない場合終了
	if not dir_check_result: return

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT['scenario'])

	#背景リサイズ
	bg_resize(PATH_DICT['bgimage'])
	bg_brightness(Path(PATH_DICT['image'] / 'title'))

	#動画連番変換
	mov2PNG(Path(PATH_DICT['video'] / 'kin.webm'), 1280, 720, values)
	mov2PNG(Path(PATH_DICT['video'] / 'sakura.webm'), 1280, 720, values)
	mov2PNG(Path(PATH_DICT['video'] / 'rain1.webm'), 1280, 720, values)
	mov2PNG(Path(PATH_DICT['video'] / 'sakura2.webm'), 1280, 720, values)
	mov2PNG_zugara2(Path(PATH_DICT['video'] / 'zugara2.webm'), values)

	#メッセージウィンドウ移動
	if not debug: Path(PATH_DICT['others'] / 'plugin' / 'theme_kopanda_09_1' / 'image' / 'frame_message.png').rename(Path(same_hierarchy / 'data' / 'frame_message.png'))

	#不要データ削除
	if not debug: junk_del(PATH_DICT)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()