#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': '羊おじさん倶楽部',
		'date': 20200803,
		'title': '魔女魔少魔法魔',
		'cli_arg': 'unclesheep_mgirlm',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'exe_name': ['mgirlm'],

		'version': [
			'魔女魔少魔法魔 DLsite DL版(RJ291856 - 2020/08/03)',
		],

		'notes': [
			'低解像度機種での文字潰れを防ぐため文字は原作より大きめ',
			'一部特殊な立ち絵表示/特定場面での文字拡大未実装',
			'音楽再生モード未実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	input_dir = values['input_dir']

	p = Path(input_dir / Path('data.xp3'))
	e = Path(pre_converted_dir / 'data')

	#なければ強制エラー
	if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))
	extract_archive_garbro(p, e, 'png')
	return


def default_txt():
	return ''';mode800
*define

caption "魔女魔少魔法魔 for ONScripter"

rmenu "記憶",save,"追想",load,"疾駆",skip,"隠蔽",windowerase,"冒頭",reset
savename "セーブ","ロード","データ"
savenumber 18
transmode alpha
globalon
rubyon
nsa
humanz 10
windowback


pretextgosub *pretext_lb
loadgosub *loadlb
defsub title_mmmm
defsub rsf

effect  8,10,1000
effect  9,10,200
effect 10,10,500

;<<-EFFECT->>

game
;----------------------------------------
*pretext_lb
	lsp 10,":s/24,24,0;#ffffff"+$11,32,440 ;名前の表示
	saveon
return

*loadlb
	setwindow3 32,470,30,4,24,24,0,2,20,1,1,#999999,16,424,783,583
return

*title_mmmm
	bg "data\\image\\魔女魔少魔法魔1.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔2.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔3.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔4.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔5.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔6.png",9
	wait 200
	bg "data\\image\\魔女魔少魔法魔7.png",9
	wait 1000
	
	dwave 0,"data\\sound\\きしみ2.ogg"
	
	bg "data\\image\\魔女魔少魔法魔7'.png",8
	wait 1000
	bg "data\\image\\魔女魔少魔法魔7''.png",9
	wait 1000
	bg black,8
return

*rsf
	setwindow3 32,470,30,4,24,24,0,2,20,1,1,#999999,16,424,783,583
return
;----------------------------------------
*staffroll
	
	;%150 再生時間
	;%151 ロール画像x - 使わん
	;%152 ロール画像y
	;%153 gettimer
	;%154 下記参照
	
	;zigoku11endの再生時間
	mov %150,110078
	
	lsp 13,"data\\staffroll_create.png",0,0
	getspsize 13,%151,%152
	sub %152,600
	
	resettimer
	
	*staffroll_loop
		gettimer %153
		
		;(経過時間/再生時間)*ロール画像y
		mov %154,%153*%152/%150
		
		if %153<%150 amsp 13,0,0-%154:print 1
		if %153>%150 bgmstop:amsp 13,0,0-%152:print 1:goto *staffroll_end
	goto *staffroll_loop
	*staffroll_end
return
;----------------------------------------
*start

rsf

;debug
;mov %200,1

;初回起動時 - 音量用変数すべて100
fileexist %130,"gloval.sav"
if %130==0 if %230==0 if %231==0 if %232==0 mov %230,100:mov %231,100:mov %232,100

bgmvol   60*%230/100
sevol    60*%231/100
voicevol 60*%232/100

setcursor 0,":a/11,80,2;data\\system\\LineBreak_a.png"
setcursor 1,":a/11,80,2;data\\system\\PageBreak_a.png"

bg "data\\image\\title.png",8
wait 1000
bg black,8

bgm "data\\bgm\\zigoku10.ogg"

if %200!=1 bg "data\\image\\mgirlm_title1.png",8
if %200==1 bg "data\\image\\mgirlm_title_B_86.png",8

if %200!=1 lsp 11,":a/3,0,3;data\\image\\start_mgirlm.png" ,666+24,344+24
if %200!=1 lsp 12,":a/3,0,3;data\\image\\load_mgirlm.png"  ,666+24,399+24
if %200!=1 lsp 13,":a/3,0,3;data\\image\\config_mgirlm.png",667+24,454+24
if %200!=1 lsp 14,":a/3,0,3;data\\image\\music_mgirlm.png" ,666+24,509+24

if %200==1 lsp 11,":a/3,0,3;data\\image\\start_mgirlm_B_86.png" ,666+24,344+24
if %200==1 lsp 12,":a/3,0,3;data\\image\\load_mgirlm_B_86.png"  ,666+24,399+24
if %200==1 lsp 13,":a/3,0,3;data\\image\\config_mgirlm_B_86.png",667+24,454+24
if %200==1 lsp 14,":a/3,0,3;data\\image\\music_mgirlm_B_86.png" ,666+24,509+24

lsp 15,":s#FFFFFF#888888Ｘ",775,2

print 1

*title_loop
	bclear
	
	spbtn 11,11
	spbtn 12,12
	spbtn 13,13
	spbtn 14,14
	spbtn 15,15
	
	btnwait %0
	
	if %0==11 dwave 0,"data\\sound\\凛.ogg":bgmstop:csp -1:goto *scenario
	if %0==12 bgmstop:csp -1:bg "data\\image\\title1.png",1:systemcall load:reset
	if %0==13 bgmstop:csp -1:bg black,9:goto *volmenu_GUI
	;if %0==14 bgmstop:csp -1:bg black,9:bgm "data\\bgm\\zigoku11end.ogg":gosub *staffroll:reset	;スタッフロールテスト
	if %0==15 bgmstop:csp -1:bg black,9:end
	
goto *title_loop
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意
	
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
	
	;文字列変換
	itoa2 $141,%230
	itoa2 $142,%231
	itoa2 $143,%232
	
	;バー代入
	if %230==  0 mov $146,$130
	if %230== 10 mov $146,$131
	if %230== 20 mov $146,$132
	if %230== 30 mov $146,$133
	if %230== 40 mov $146,$134
	if %230== 50 mov $146,$135
	if %230== 60 mov $146,$136
	if %230== 70 mov $146,$137
	if %230== 80 mov $146,$138
	if %230== 90 mov $146,$139
	if %230==100 mov $146,$140
	if %231==  0 mov $147,$130
	if %231== 10 mov $147,$131
	if %231== 20 mov $147,$132
	if %231== 30 mov $147,$133
	if %231== 40 mov $147,$134
	if %231== 50 mov $147,$135
	if %231== 60 mov $147,$136
	if %231== 70 mov $147,$137
	if %231== 80 mov $147,$138
	if %231== 90 mov $147,$139
	if %231==100 mov $147,$140
	if %232==  0 mov $148,$130
	if %232== 10 mov $148,$131
	if %232== 20 mov $148,$132
	if %232== 30 mov $148,$133
	if %232== 40 mov $148,$134
	if %232== 50 mov $148,$135
	if %232== 60 mov $148,$136
	if %232== 70 mov $148,$137
	if %232== 80 mov $148,$138
	if %232== 90 mov $148,$139
	if %232==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400,450
	lsp 132,":s;#FFFFFF#666666戻る",     550,450
	
	lsp 135,":s;#FFFFFFＢＧＭ",           50,150
	lsp 136,":s;#FFFFFF#666666＜",       200,150
	lsp 137,$146,                        250,150
	lsp 138,":s;#FFFFFF#666666＞",       550,150
	lsp 139,":s;#FFFFFF#666666"+$141,    600,150
	
	lsp 140,":s;#FFFFFFＳＥ１",           50,250
	lsp 141,":s;#FFFFFF#666666＜",       200,250
	lsp 142,$147,                        250,250
	lsp 143,":s;#FFFFFF#666666＞",       550,250
	lsp 144,":s;#FFFFFF#666666"+$142,    600,250
	
	lsp 145,":s;#FFFFFFＳＥ２",           50,350
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
	
	if %140==131 mov %230,100:mov %231,100:mov %232,100
	if %140==132 csp -1:reset
	if %140==136 if %230!=  0 sub %230,10
	if %140==138 if %230!=100 add %230,10
	if %140==141 if %231!=  0 sub %231,10
	if %140==143 if %231!=100 add %231,10
	if %140==146 if %232!=  0 sub %232,10
	if %140==148 if %232!=100 add %232,10
	
goto *volmenu_loop
;----------------------------------------
*scenario
'''


# -ONS変数メモ-
# $11  発言時キャラ名
# $21  場所
# $22  音楽
# %200 クリア変数


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

	return str(list_num), effect_list


#吉里吉里の命令文及び変数指定をざっくりpythonの辞書に変換するやつ
def krcmd2krdict(c):
	kr_dict = {}

	for p in re.findall(r'([A-z0-9-_]+?)=("(.*?)"|([^\t\s]+))', c):
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

		['ｺ', 'コ'], ['ﾎﾟ', 'ポ'], ['ﾎﾞ', 'ボ'], ['ｿ', 'ソ'], ['ｯ', 'ッ'], 
	]

	for v in cnvl:
		txt = txt.replace(v[0], v[1])

	return txt


#画像傾けて新規で保存
def image_angle(storage, angle, same_hierarchy):
	p = (same_hierarchy / Path(storage.replace(r'"', '')))
	p_save = str(p) + '_' + str(angle) + '.png'

	im = Image.open(p)
	im_rotate = im.rotate(angle, resample=Image.BICUBIC, center=(im.width, 300))
	im_rotate.save(p_save)

	return


# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, same_hierarchy, zero_txt, scenario):

	# effect管理用変数
	effect_startnum = 10
	effect_list = []

	#default.txtを読み込み
	# with open(default, encoding='cp932', errors='ignore') as f:
	# 	txt = f.read()
	txt = default_txt()

	#シナリオファイルを読み込み
	p = Path(scenario / 'のろいルート.ks')
	with open(p, encoding='cp932', errors='ignore') as f:
		fr = f.read()
		fr = re.sub(r'\[ruby\stext\s?=\s?"(.+?)"\](.+?)', r'(\2/\1)', fr)
		fr = re.sub(r'\[serihu (.+?)\]', r'[serihu \1]\n', fr)# 文章とセリフ名が1行になってることが多いので剥がす
		fr = re.sub(r'\[font (.+?)\]', r'[font \1]\n', fr)# 文章とfont指定が1行になってることが多いので剥がす
		fr = fr.replace(r'[resetfont]', '\n' + r'[resetfont]')# resetfontも同様
		fr = re.sub(r'\@(.+?)\n', r'[\1]\n', fr)# @からの命令も[]同様に処理したいので
		fr = fr.replace(r'[pcm]', '\\\nmov $11,""' + r':rsf')# セリフの名前部分を空に
		fr = fr.replace(r'[lr]', '@')# 文章停止


		for line in fr.splitlines():
			kakko_line = re.search(r'\[(.+?)\]', line)

			#改行は無視
			if re.match('\n', line):
				pass

			#アイキャッチ
			elif re.search('あいきゃっち', line): 
				line = 'title_mmmm'

			#元々コメントアウトのやつ目立たせる
			elif re.match(r';', line):
				line = (r';;;;' + line) if DEBUG_MODE else ''

			#gotoと間違えそうなやつ
			elif re.match(r'\*', line): 
				line = (';' + line) if DEBUG_MODE else ''

			#既に置換済み
			elif re.match('mov ', line): 
				pass

			#多分セリフとか
			elif not re.match(r'\[', line):
				#半角置換予定
				line = message_replace(line)

			#命令文 - []内
			elif kakko_line:
				d = krcmd2krdict('kr_cmd=' + kakko_line[1])
				kr_cmd = d['kr_cmd']

				#発言キャラ名
				if kr_cmd == 'serihu':
					line = ('mov $11,"' + message_replace(d['by']) + '"')

				#吉里吉里での変数代入的な
				elif kr_cmd == 'eval':

					#本来f.musicdummyってのもあるがmusicとループの有無以外変わらないので除外(同一視)
					f_place = re.match(r'f\.place\s?=\s?\'(.+?)\'', d['exp'])
					f_music = re.match(r'f\.music\s?=\s?\'(.+?)\'', d['exp'])
					sf_lastflag = re.match(r'sf\.lastflag\s?=\s?(.+?)', d['exp'])

					if f_place:
						line = ('mov $21,"data\\bgimage\\' + f_place[1] + '.png"')

					elif f_music:
						line = ('mov $22,"data\\bgm\\' + f_music[1] + '.ogg"')

					elif sf_lastflag:
						line = ('mov %200,' + sf_lastflag[1])

					else:
						#print(d['exp'])
						line = (';' + line) if DEBUG_MODE else ''
						
				#待ち
				elif kr_cmd == 'wait':
					line = ('wait ' + d['time'])

				#画面揺れ
				elif kr_cmd == 'quake':
					qmax = max(int(d['hmax']), int(d['vmax']))
					line = ('quake ' + str(qmax) + ',' + d['time'])
				
				#場面転換
				elif re.match(r'newscene[1-5](ar)?', kr_cmd):
					bgimage = '$21' if (d['bgimage'] == r'&f.place') else ('"data\\bgimage\\' + d['bgimage'] + '.png"')

					time1 = '500' if (not d.get('time1')) else d['time1']
					rule1 = 'fade' if (not d.get('rule1')) else d['rule1']

					ee, effect_list = effect_edit(time1, rule1, effect_startnum, effect_list)
					line = 'csp -1:bg ' + bgimage + ',' + ee

					if d.get('bgm'):
						bgm = '$22' if (d['bgm'] == r'&f.music') else ('"data\\bgm\\' + d['bgm'] + '.ogg"')
						line += ('\nbgm ' + bgm)
				
				# 画面切り替え
				elif kr_cmd == 'trans':
					if (d['method'] == 'universal'):
						ee, effect_list = effect_edit(d['time'], d['rule'], effect_startnum, effect_list)
						line = 'print ' + ee

					else:
						ee, effect_list = effect_edit(d['time'], 'fade', effect_startnum, effect_list)
						line = 'print ' + ee

				# 画面切り替え
				elif kr_cmd == 'antenar':
					time1 = '500' if (not d.get('time1')) else d['time1']
					rule1 = 'fade' if (not d.get('rule1')) else d['rule1']

					ee, effect_list = effect_edit(time1, rule1, effect_startnum, effect_list)
					line = 'print ' + ee

				# 立ち絵?
				elif kr_cmd == 'image' or kr_cmd == 'eximage':
					left = d.get('left') if d.get('left') else '0'
					top = d.get('top') if d.get('top') else '0'

					if (d['layer'] == 'base') or (d['layer'] == '0'):
						storage = ('"data\\bgimage\\' + d['storage'].replace('\'', '') + '.png"') if (not d['storage'] == r'&f.place') else '$21'
					else:
						storage = ('"data\\fgimage\\' + d['storage'].replace('\'', '') + '.png"') if (not d['storage'] == r'&f.place') else '$21'

					if (d['layer'] == '0'):
						var = ('$30')
						var_left = ('%40')
						var_top = ('%50')
						var_layer = ('10')

					if (d['layer'] == '1'):
						var = ('$31')
						var_left = ('%41')
						var_top = ('%51')
						var_layer = ('11')

					if (d['layer'] == '2'):
						var = ('$32')
						var_left = ('%42')
						var_top = ('%52')
						var_layer = ('12')

					if (d['layer'] == 'base'):
						var = ('$35')
						var_left = ('%45')
						var_top = ('%55')
						var_layer = ('13')

					var_left2 = False
					var_top2 = False

					if kr_cmd == 'eximage':
						angle = int(d.get('angle'))
						
						if (not angle == 0):
							angle *= -1
							#ななめ 座標は画像見て合わせただけ　てきとう
							image_angle(storage, angle, same_hierarchy)
							#x+83 y-150
							storage = (storage[:-1] + '_' + str(angle) + r'.png"')
							var_left2 = var_left + '+83'
							var_top2 = var_top + '-150'
					
					if not var_left2:
						var_left2 = var_left
						var_top2 = var_top

					if (d.get('visible') == 'true') or (d['layer'] == 'base'):
						line = ('mov ' + var + ',' + storage + ':mov ' + var_left + ',' + left + ':mov ' + var_top + ',' + top + ':lsp ' + var_layer + ',' + var + ',' + var_left2 + ',' + var_top2 + ':print 9')
			
					else:
						line = ('mov ' + var + ',' + storage + ':mov ' + var_left + ',' + left + ':mov ' + var_top + ',' + top + ':lsph ' + var_layer + ',' + var + ',' + var_left2 + ',' + var_top2 + ':print 9')

				#画像移動
				elif kr_cmd == 'move':
					path = d.get('path')

					if (d['layer'] == '0'):
						var = ('$30')
						var_left = ('%40')
						var_top = ('%50')
						var_layer = ('10')

					if (d['layer'] == '1'):
						var = ('$31')
						var_left = ('%41')
						var_top = ('%51')
						var_layer = ('11')

					if (d['layer'] == '2'):
						var = ('$32')
						var_left = ('%42')
						var_top = ('%52')
						var_layer = ('12')

					if (d['layer'] == 'base'):
						var = ('$35')
						var_left = ('%45')
						var_top = ('%55')
						var_layer = ('13')

					if path:
						x = re.findall(r'\((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)', path)
						line = 'print 1'
						for a in x:

							if (a[2] == '0'):
								line += (':mov ' + var_left + ',' + a[0] + ':mov ' + var_top + ',' + a[1] + ':lsph ' + var_layer + ',' + var + ',' + var_left + ',' + var_top + ':print 9')

							else:
								line += (':mov ' + var_left + ',' + a[0] + ':mov ' + var_top + ',' + a[1] + ':lsp ' + var_layer + ',' + var + ',' + var_left + ',' + var_top + ':print 9')
					
					else:
						line = (';' + line) if DEBUG_MODE else ''
				
				#次回立ち絵読み込み
				elif re.match(r'[1-2]ch', kr_cmd):
					next = ('"data\\fgimage\\' + d['next'].replace('\'', '') + '.png"')
					ch = re.match(r'([1-2])ch', kr_cmd)

					if ch:

						if (ch[1] == '1'):
							var = ('$31')
							var_left = ('%41')
							var_top = ('%51')
							var_layer = ('11')

						if (ch[1] == '2'):
							var = ('$32')
							var_left = ('%42')
							var_top = ('%52')
							var_layer = ('12')

						line = ('lsp ' + var_layer + ',' + next + ',' + var_left + ',' + var_top + ':' + 'print 10')

					else:
						line = (';' + line) if DEBUG_MODE else ''
				
				#bgm
				elif kr_cmd == 'playbgm' or kr_cmd == 'fadeinbgm':
					storage = ('"data\\bgm\\' + d['storage'].replace('\'', '') + '.ogg"') if (not d['storage'] == r'&f.music') else '$22'

					line = ('bgm ' + storage)

					#ED用ゴリ押し措置
					if d['storage'] == 'zigoku11end':
						line += ':gosub *staffroll'

				#se
				elif kr_cmd == 'playse' or kr_cmd == 'fadeinse':
					storage = ('"data\\sound\\' + d['storage'].replace('\'', '') + '.ogg"') if (not d['storage'] == r'&f.music') else '$22'
					loop = True if (d.get('loop') == 'true') else False

					if loop:
						line = ('dwaveloop 1,' + storage)

					else:
						line = ('dwave 0,' + storage)
				
				#bgm止める
				elif kr_cmd == 'fadeoutbgm':
					line = 'bgmstop'

				#se止める
				elif kr_cmd == 'stopse' or kr_cmd == 'fadeoutse':
					line = ('dwavestop 1')

				#bgm音量調整
				elif kr_cmd == 'bgmopt' or kr_cmd == 'fadebgm':
					volume = d['volume']
					line = ('bgmvol ' + volume + r'*%230/100')

				#se音量調整
				elif kr_cmd == 'seopt' or kr_cmd == 'fadese':
					volume = d['volume']
					line = ('sevol ' + volume + r'*%231/100:voicevol ' + volume + r'*%232/100')

				#クリック待ち
				elif kr_cmd == 'waitclick':
					line = 'click'
				
				#レイヤー初期化？
				elif kr_cmd == 'freeimage':
					if (d['layer'] == '0'):
						var_layer = ('10')

					if (d['layer'] == '1'):
						var_layer = ('11')

					if (d['layer'] == '2'):
						var_layer = ('12')

					if (d['layer'] == 'base'):
						var_layer = ('13')

					line = ('vsp ' + var_layer + ',0')

				#暗転
				elif kr_cmd == 'anten' or kr_cmd == 'anten1':
					line = 'csp -1:bg black,9'

				#フォントサイズ変更
				elif kr_cmd == 'font':
					line = r'setwindow3 32,470,15,4,'+d['size']+r'/3*2,'+d['size']+r'/3*2,0,2,20,1,1,#999999,16,424,783,583'

				#フォントサイズ戻す
				elif kr_cmd == 'resetfont':
					line = r'rsf'

				#特殊画像移動...のはずなんだけどいろいろめんどくさくなったので
				elif kr_cmd == 'exmove':
					line = r'vsp 10,0:vsp 11,0:print 9'

				#他
				else:
					if DEBUG_MODE:
						print(kr_cmd)

					line = (';' + line) if DEBUG_MODE else ''
				
			#その他 - エラー防止の為コメントアウト(多分ない)
			else:
				line = (';' + line) if DEBUG_MODE else ''
			
			#変換した命令行が空ではない場合
			if line:
				txt += (line + '\n')#入力


	# エフェクト定義用の配列を命令文に&置換
	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):

		if e[1] == 'fade':
			add0txt_effect +='effect ' + str(i) + ',10,'+e[0]+'\n'

		else:
			add0txt_effect +='effect ' + str(i) + ',18,'+e[0]+',"data\\rule\\'+str(e[1]).replace('"','')+'.png"\n'

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)
	txt += '\nreset'

	#出力結果を書き込み
	open(zero_txt, 'w', encoding='cp932', errors='ignore').write(txt)

	return


def junk_del(PATH_DICT):

	#リスト内のディレクトリパスでfor
	for d in [PATH_DICT['scenario'], PATH_DICT['video']]:

		#ディレクトリパス内のファイル一覧でfor
		for p in d.glob('*'):

			#削除
			p.unlink()
		
		#ディレクトリも削除
		d.rmdir()

	for d in [PATH_DICT['system'], PATH_DICT['bgm'], PATH_DICT['rule']]:

		for p in d.glob('*.sli'):
			p.unlink()
		for p in d.glob('*.tjs'):
			p.unlink()
		for p in d.glob('*.asd'):
			p.unlink()
		for p in d.glob('*.txt'):
			p.unlink()
	
	return


def staffroll_create(same_hierarchy):
	s_path = Path(same_hierarchy / Path(r'data/scenario/スタッフロール.ks'))
	i_path = Path(same_hierarchy / Path(r'data/staffroll_create.png'))
	t_path = Path(same_hierarchy / Path(r'data/image/title.png'))
	ttf = "C:\\Windows\\Fonts\\BIZ-UDMinchoM.ttc" #str必須

	if not Path(ttf).exists():#古いwindowsとかでBIZ-UD明朝がない場合
		ttf = "C:\\Windows\\Fonts\\msmincho.ttc"#MS明朝なら大体入ってるでしょ
		
	with open(s_path, encoding='cp932', errors='ignore') as f:
		s = f.read()
		s = s.replace(r'[', '\n'+r'[')

		im = Image.new("RGB", (800, 10000), (0, 0, 0))#とりあえず10000
		draw = ImageDraw.Draw(im)
		fsize = 22
		txt_y = 600

		for l in s.splitlines()[1:]:# 最初の*スタッフロール文字列←これいらないので[1:](最初の行飛ばす)
			if l == '[resetfont]':
				fsize = 22
			elif l == '[r]':
				txt_y += int(fsize * 1.1)#文字と文字との隙間が0.1文字分と計算
			elif '[font size=' in l:
				fsize = int(l[11:13])#フォントサイズだけ取ってくる
			elif '[' in l:
				pass
			else:
				font = ImageFont.truetype(ttf, fsize)
				txt_x = 400 - (len(l) * int(fsize * 1.1) / 2)
				draw.text((txt_x, txt_y), message_replace(l), fill=(255, 255, 255), font=font)

		#画像一番下画像なので
		im_title = Image.open(t_path)
		im.paste(im_title, (0, txt_y + fsize))
		
		#ここで下の余分なところを消す
		im_crop = im.crop((0, 0, 800, txt_y + fsize + im_title.height))
		im_crop.save(i_path)


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)
	
	# デバッグモード
	debug = 0

	#同一階層のパスを変数へ代入
	same_hierarchy = pre_converted_dir#Path.cwd()

	#debug時にtestフォルダに入れないやつ(default.txt等)はこっちを利用
	#same_hierarchy_const = same_hierarchy

	if debug:
		#デバッグ時はtestディレクトリ直下
		same_hierarchy = (same_hierarchy / '_test')

	#利用するパスを辞書に入れ一括代入
	PATH_DICT = {
		#先に準備しておくべきファイル一覧
		'bgimage' :(same_hierarchy / 'data' / 'bgimage'),
		'bgm' :(same_hierarchy / 'data' / 'bgm'),
		'fgimage' :(same_hierarchy / 'data' / 'fgimage'),
		'image' :(same_hierarchy / 'data' / 'image'),
		'rule' :(same_hierarchy / 'data' / 'rule'),
		'scenario' :(same_hierarchy / 'data' / 'scenario'),
		'sound' :(same_hierarchy / 'data' / 'sound'),
		'system' :(same_hierarchy / 'data' / 'system'),
		'video' :(same_hierarchy / 'data' / 'video'),

		'startup_tjs' :(same_hierarchy / 'data' / 'startup.tjs'),

		#'default':(same_hierarchy_const / 'default.txt'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'0_txt'  :(same_hierarchy / '0.txt'),
	}

	#ディレクトリの存在チェック
	dir_check_result = dir_check(PATH_DICT.values())

	#存在しない場合終了
	if not dir_check_result:
		return

	#txt置換→0.txt出力
	text_cnv(debug, same_hierarchy, PATH_DICT2['0_txt'], PATH_DICT['scenario'])

	#スタッフロール作成
	staffroll_create(same_hierarchy)

	#不要データ削除
	if not debug:
		junk_del(PATH_DICT)

#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()