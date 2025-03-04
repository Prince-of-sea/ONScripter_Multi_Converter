#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import concurrent.futures
import chardet, shutil, glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'Supplement Time',
		'date': 20071231,
		'title': '未来のキミと、すべての歌に―',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'program_name': 'ミクキス',#一覧取得用
		'exe_name': 'miku',#一覧取得用

		'version': [
			'未来のキミと、すべての歌に― DLsite DL版(RJ038558 - 2008/04/04)',
		],

		'notes': [
			'いくつかの処理のwait時間が実際と違う',
			'立ち絵の初期位置がたまにずれる',
			'多少画像表示に抜けがあるかも',
			'画面左下のボタンは全て未実装',
			'スクロールはフェードで代用',
			'セーブ/ロード画面は簡略化',
			'CGモードは超簡易実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xp3_name in ['bgimage', 'bgm', 'data', 'fgimage', 'image', 'others', 'patch', 'rule', 'scenario', 'sound', 'system', 'video']:
			p = Path(input_dir / Path(xp3_name + '.xp3'))
			e = Path(pre_converted_dir / xp3_name)

			#なければ強制エラー
			if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))

			futures.append(executor.submit(extract_archive_garbro, p, e))
		
		concurrent.futures.as_completed(futures)

	return


#--------------------memo--------------------
'''
s0 ,ミニウインドウの名前文字
s1 ,ミニウインドウの名前欄
s2 ,ウインドウ右下ダミーのボタン郡
s3 ,カットイン
s4 ,CG上効果(回想フレーム)
s5 ,CG
s6 ,立ち絵

s10,タイトルボタン スタート
s11,タイトルボタン ロード
s12,タイトルボタン グラフィック
s13,タイトルボタン 終了

S20,CGモード 戻る
s21,CGモード 1
s22,CGモード 2
s23,CGモード 3
s24,CGモード 4
s25,CGモード 5
s26,CGモード 6
s27,CGモード 7
s28,CGモード 8
s29,CGモード 9
s30,CGモード 10

$0 ,文章 - getparam
$1 ,キャラクターの名前
$2 ,立ち絵パス - getparam
$3 ,立ち絵位置指定 - getparam
$4 ,背景パス - getparam
$5 ,playfadein - getparam
$6 ,グラフィックモード指定

%0 ,文章送り(0=初期 /1@,無 /2=＼,[w] /3=長,[w mode=l] ) - getparam
%1 ,ミニウインドウの名前欄の文字数
%2 ,ミニウインドウの名前欄のX座標
%3 ,スプライトサイズx
%4 ,スプライトサイズy
%5 ,playfadein/stopfadeout - getparam
%6 ,tatiスプライト番号 - getparam
%7 ,背景エフェクト - getparam
%8 ,スキップ判定
%9 ,btnwait
%10,layermove スプライト番号
%11,layermove time
%12,layermove x
%13,layermove y
%14,layermove 透過度(濃255←→0薄)

%200,クリアフラグ
'''


#--------------------def--------------------
def default_txt():
	s = ''';mode800
*define

caption "未来のキミと、すべての歌に― for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa

defsub playfadein
defsub stopfadeout
defsub layermove
defsub tati
defsub cltati
defsub bgdef
defsub msg
defsub msgNamePos

effect 2,10,100
effect 3,10,1000
;<<-EFFECT->>

game

*playfadein
	;ttps://chappy.exblog.jp/5872275/
	getparam $5,%5
	bgmfadein %5
	bgm $5
	bgmfadein 0
return


*stopfadeout
	;ttps://chappy.exblog.jp/5872275/
	getparam %5
	bgmfadeout %5
	stop
	bgmfadeout 0
return


*layermove
	;スクロールやろうとしたけど技術力がなかった
	saveoff
	getparam %10,%11,%12,%13,%14

	amsp %10,%12,%13
	print %11

	if %14==0 vsp %10,0:print 2
	saveon
return


;立ち絵表示
*tati
	;lsp2のレイヤー表示順指定がONSでうまくいかないため
	;仕方なく相対指定をlspで再現する感じ
	;誰かもっと良いやり方知ってたら教えて...

	getparam $2,$3,%6
	vsp 1,0:vsp 0,0

	lsph %6,$2,0,0		;仮呼び出し
	getspsize %6,%3,%4	;サイズ取得

	;相対位置計算
	mov %3,400-(%3/2)
	mov %4,300-(%4/2)

	amsp %6,%3,%4	;本来の位置に移動
	vsp %6,1			;表示
return


;背景表示
*bgdef
	getparam $4,%7

	vsp 0,0:vsp 1,0:vsp 2,0:vsp 6,0
	csp 5:csp 4:csp 3
	print 0

	bg $4,%7
return


;立ち絵削除
*cltati
	csp 6
	print 2

	csp 5:csp 4:csp 3
	monocro off
	print 0
return


;メッセージ表示
*msg
	getparam $0,%0

	vsp 2,1:vsp 6,1
	print 0

	if $1!="" vsp 1,1:msgNamePos:strsp 0,$1,%2,417,7,1,26,26,2,3,0,1
	if $1=="" vsp 1,0:vsp 0,0

	if %0!=3 setwindow3 15,460,24,3,26,26,2,3,30,0,1,"others\\frame01.png",0,450	;通常表示
	if %0==3 setwindow3 15,460,24,3,26,26,2,3,60,0,1,"others\\frame01.png",0,450	;低速表示

	if %0==1 $0@
	if %0==2 $0\\
	if %0==3 $0\\

	mov $1,""
return


;キャラ名中央表示用座標取得
*msgNamePos
	;文字26px+幅2px=28px
	;len取得数/2=文字数(一文字で2判定っぽい)
	;文字数x28px-2px=名前全体の文字サイズ

	;frame02の横幅は153px
	;(frame02の横幅-名前全体の文字サイズ)/2=X座標

	len %1,$1
	mov %2,(153-(%1/2)*(26+2)-2)/2
return


*start

abssetcursor 1,":a/8,210,0;system\\linebreak_a.png",740,520
lsph 1,"others\\frame02.png",0,417
lsph 2,"others\\frame03.png",530,570


;クリア状態テスト
;mov %200,1

bg black,0
bg "others\\logo.jpg",3
wait 1000
*title
	bg black,3
	bgm "bgm\\bgm_op.ogg"
	bg "others\\title.jpg",3
	
	lsp 10,":a/3,0,3;others\\bt_start.png",26,29
	lsp 11,":a/3,0,3;others\\bt_load.png" ,26,70
	if %200==1 lsp 12,":a/3,0,3;others\\bt_graph.png",26,112
	lsp 13,":a/3,0,3;others\\bt_end.png"  ,26,196

	print 0

*title_loop
	bclear
	
	spbtn 10,10
	spbtn 11,11
	if %200==1 spbtn 12,12
	spbtn 13,13

	btnwait %9
	print 0

	if %9==10 gosub *titlebtn:goto *sn_01_01_ks
	if %9==11 systemcall load:goto *title_loop
	if %200==1 if %9==12 gosub *titlebtn:goto *grpmode
	if %9==13 gosub *titlebtn:bg black,3:end
	
goto *title_loop


*titlebtn
	;<<-SE-DWAVE->>
	stopfadeout 1000
	csp 10:csp 11:csp 12:csp 13
return


*grpmode
bg "others\\cg_mode.jpg",3
select "ＣＧ０１",*CG01,
       "ＣＧ０２",*CG02,
       "ＣＧ０３",*CG03,
       "ＣＧ０４",*CG04,
       "ＣＧ０５",*CG05,
       "ＣＧ０６",*CG06,
       "ＣＧ０７",*CG07,
       "ＣＧ０８",*CG08,
       "ＣＧ０９",*CG10,
       "ＣＧ１０",*CG12,
       "ＥＸＩＴ",*title

*CG01
	mov $6,"01":goto *grpview
*CG02
	mov $6,"02":goto *grpview
*CG03
	mov $6,"03":goto *grpview
*CG04
	mov $6,"04":goto *grpview
*CG05
	mov $6,"05":goto *grpview
*CG06
	mov $6,"06":goto *grpview
*CG07
	mov $6,"07":goto *grpview
*CG08
	mov $6,"08":goto *grpview
*CG10
	mov $6,"10":goto *grpview
*CG12
	mov $6,"12":goto *grpview

*grpview
;<<-GRAPHIC_VIEW->>
goto *grpmode


;----------ここまでdefault.txt----------
'''
	return s


# https://gist.github.com/PC-CNT/843e79e439a4dcba72f32602feafecf7
def conv1(moji :str) -> str:
	"""
	convert string to dictionary
	example:
	>>> conv1('a=test b="hoge hoge" c=true')
	{'a': 'test', 'b': 'hoge hoge', 'c': 'true'}
	"""
	outdic = {}
	for line in re.findall(r'(\S+?=(?:\".+\"|\S+))', moji):
		key, value = re.split(r'=', line, 1)
		outdic[key] = value.strip('"')
	return outdic

def effect_edit(t, f, effect_startnum, effect_list):

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num), effect_startnum, effect_list


#-------------------パッチ適用--------------------
def patch(patch_dir, scenario_dir, image_dir):
	for patch_path in glob.glob(os.path.join(patch_dir, '*')):
		ext = (os.path.splitext(patch_path)[1]).lower()
		if ext == '.ks':
			extdir = scenario_dir
		elif ext == '.png':
			extdir = image_dir
		else:
			extdir = ''

		if extdir:
			patch_path2 = os.path.join(extdir,os.path.basename(patch_path))
			shutil.move(patch_path, patch_path2)


#-------------------音源リネーム--------------------
def music_rename(sound_dir):
	sound_dict = {}
	for i,sound_path in enumerate( glob.glob(os.path.join(sound_dir, '*')) ):
		sound_path2 = os.path.join(os.path.dirname(sound_path), 'sound'+str(i)+os.path.splitext(sound_path)[1])
		os.rename(sound_path, sound_path2)

		sound_dict[(os.path.splitext(os.path.basename(sound_path))[0]).lower()] = 'sound'+str(i)
	
	return sound_dict


#-------------------ウィンドウ画像修正用--------------------
def image_convert_msgwin(image_dir):
	f = os.path.join(os.path.dirname(image_dir),'others','frame01.png')
	im = Image.open(f)
	im3 = Image.new("RGBA", (im.width*2, im.height*2), (0, 0, 0, 0))
	im3.paste(im, (0, 0))
	im3.save(f)


#--------------------0.txt作成--------------------
def text_cnv(same_hierarchy, scenario_dir, image_dir, sound_dict):
	effect_startnum = 10
	effect_list = []

	#[w*]系統の命令一時変数預かり
	trans_time = ''
	quake_nsc = ''
	move_nsc = ''

	txt = default_txt()

	for ks_path in glob.glob(os.path.join(scenario_dir, '*')):
		
		with open(ks_path, 'rb') as f:
			char_code =chardet.detect(f.read())['encoding']

		with open(ks_path, encoding=char_code, errors='ignore') as f:
			#ks名をそのままonsのgoto先のラベルとして使い回す
			txt += 'end\n*' + os.path.splitext(os.path.basename(ks_path))[0] + '_ks\n'

			for line in f:
				#最初にやっとくこと
				line = re.sub(r'\[ruby text="(.+?)"\](.)',r'(\2/\1)',line)#ルビ置換
		
				name_line = re.fullmatch(r'\[stName\](.+?)\[endName\]\n',line)#括弧行定義
				kakko_line = re.fullmatch(r'\[(.+?)\]\n',line)#括弧行定義
				str_line = re.fullmatch(r'(.+?)(\[w( mode=l)?\])?\n',line)#文章行定義

				if re.search('^\n', line):#空行
					#pass#そのまま放置
					line = ''

				elif re.match(r'\*', line):#nsc側でラベルと勘違いするの対策
					#line = r';' + line#エラー防止の為コメントアウト
					line = ''

				elif re.search(';', line):#元々のメモ
					#line = line.replace(';', ';;;')#分かりやすく
					line = ''

				elif name_line:
					line = 'mov $1,"'+name_line[1]+'"\n'

				elif kakko_line:
					kakko_dict = conv1('kr_cmd=' + kakko_line[1])

					linedef = line
					kr_cmd = kakko_dict['kr_cmd']

					if kr_cmd == 'jump':
						line = 'goto *' + str(kakko_dict.get('storage')).replace('.', '_')#goto先のラベル名
					
					elif kr_cmd == 'c':
						line = 'print 0'

					elif kr_cmd == 'wait':
						time = kakko_dict.get('time')
						cond = kakko_dict.get('cond')

						if re.fullmatch(r'[0-9]+',time):#timeが数字のみ＝本処理
							line = 'wait ' + time

							if cond =='kag.skipMode >= 3':
								line = 'isskip %8:if %8==1 ' + line
							elif cond =='kag.skipMode < 3':
								line = 'isskip %8:if %8!=1 ' + line

					elif kr_cmd == 'hsDispEvent':
						#visible = kakko_dict.get('visible')
						storage = kakko_dict.get('storage')
						mode = kakko_dict.get('mode') if kakko_dict.get('mode') else '0'
						time = kakko_dict.get('time') if kakko_dict.get('time') else '1500'
						time2 = str(int(int(time)/2))

						if mode == '0':#CG - 通常フェード
							s1, effect_startnum, effect_list = effect_edit(time, 'fade', effect_startnum, effect_list)
							line = 'cltati:bgdef "image\\' + storage + '.png",' + s1
						elif mode == '1':#CG - 白
							s1, effect_startnum, effect_list = effect_edit(time2, 'fade', effect_startnum, effect_list)
							line = 'cltati:bgdef ":c;bgimage\\bg_white.bmp",' + s1 + 'lsp 5,":a;image\\' + storage + '.png",0,0:print ' + s1
						elif mode == '2':#CG - 黒
							s1, effect_startnum, effect_list = effect_edit(time2, 'fade', effect_startnum, effect_list)
							line = 'cltati:bgdef ":c;bgimage\\bg_black.bmp",' + s1 + 'lsp 5,":a;image\\' + storage + '.png",0,0:print ' + s1
						elif mode == '4':#背景 - 黒
							s1, effect_startnum, effect_list = effect_edit(time2, 'fade', effect_startnum, effect_list)
							line = 'cltati:bgdef ":c;bgimage\\bg_black.bmp",' + s1 + 'bgdef "bgimage\\' + storage + '.png",' + s1

					elif kr_cmd == 'image':
						#visible = kakko_dict.get('visible')
						grayscale = kakko_dict.get('grayscale')
						storage = kakko_dict.get('storage')
						layer = kakko_dict.get('layer')

						if layer == 'base':
							line = 'cltati:bgdef "bgimage\\' + storage + '.png",2'

						else:
							#opacity = kakko_dict.get('opacity')
							#page = kakko_dict.get('page')
							left = kakko_dict.get('left') if kakko_dict.get('left') else '0'
							top = kakko_dict.get('top') if kakko_dict.get('top') else '0'
							pos = kakko_dict.get('pos')

							#kr→nscレイヤー   0=cg[s5] / 1=cg上[s4] / 2=カットイン[s3]  他は適当
							layer2 = str(int(5-int(layer)))
							if not pos:
								line = 'lsph ' + layer2 + ',":a;image\\' + storage + '.png",' + left + ',' + top + ':print 2'
							else:
								if pos == 'c':
									#今作見た感じposはfgimageのcしかなさそう
									line = 'tati ":a;fgimage\\' + storage + '.png","",' + layer2
						
						if grayscale:#今作のモノクロ全部セピアっぽい
							line = 'monocro #eeccaa:print 0:' + line

					elif kr_cmd == 'trans':
						trans_time = kakko_dict.get('time')
						#line = ';処理済\t' + line
						line = ''

					elif kr_cmd == 'wt':
						s1, effect_startnum, effect_list = effect_edit(trans_time, 'fade', effect_startnum, effect_list)
						line = 'vsp 3,1:vsp 4,1:vsp 5,1:print ' + s1

						#保険
						trans_time = ''

					elif kr_cmd == 'quake':
						time = kakko_dict.get('time')
						hmax = kakko_dict.get('hmax')#x?
						vmax = kakko_dict.get('vmax')#y?

						if (not hmax) and (not vmax):
							quake_nsc = 'quake 10,' + time
						elif hmax == vmax:
							quake_nsc = 'quake ' + hmax + ',' + time
						elif vmax == '0':
							quake_nsc = 'isskip %8:if %8==1 quakex ' + hmax + ',' + time
						elif hmax == '0':
							quake_nsc = 'isskip %8:if %8==1 quakey ' + vmax + ',' + time
						else:
							quake_nsc = 'isskip %8:if %8==1 quakex ' + hmax + ',' + time + ':quakey ' + vmax + ',' + time

						#line = ';処理済\t' + line
						line = ''

					elif kr_cmd == 'wq':
						line = quake_nsc

						#保険
						quake_nsc = ''

					elif kr_cmd == 'hsChgCutin':
						storage = kakko_dict.get('storage')
						if storage:
							line = 'tati ":a;image\\' + storage + '.png","",3'
						else:
							line = 'csp 3:print 2'

					elif kr_cmd == 'hsBlackout':
						#visible = kakko_dict.get('visible')
						time = kakko_dict.get('time') if kakko_dict.get('time') else '750'
						s1, effect_startnum, effect_list = effect_edit(time, 'fade', effect_startnum, effect_list)
						line ='cltati:bgdef ":c;bgimage\\bg_black.bmp",' + s1

					elif kr_cmd == 'hsWhiteout':
						#visible = kakko_dict.get('visible')
						time = kakko_dict.get('time') if kakko_dict.get('time') else '750'
						s1, effect_startnum, effect_list = effect_edit(time, 'fade', effect_startnum, effect_list)
						line ='cltati:bgdef ":c;bgimage\\bg_white.bmp",' + s1

					elif kr_cmd == 'hsDispMsg':
						line = 'vsp 2,1:vsp 6,1'

					elif kr_cmd == 'hsChgBgi':
						storage = kakko_dict.get('storage')
						time = kakko_dict.get('time') if kakko_dict.get('time') else '1000'
						rule = kakko_dict.get('rule') if kakko_dict.get('rule') else 'fade'
						s1, effect_startnum, effect_list = effect_edit(time, rule, effect_startnum, effect_list)
						line = 'cltati:bgdef "bgimage\\' + storage + '.png",' + s1

					elif kr_cmd == 'hsChgFgi':
						storage1 = kakko_dict.get('storage1')
						pos1 = kakko_dict.get('pos1') if kakko_dict.get('pos1') else ''

						if storage1:
							line = 'tati ":a;fgimage\\' + storage1 + '.png","' + pos1 + '",6:print 2'
						else:
							line = 'vsp 6,0'

					elif kr_cmd == 'move':
						#accel = kakko_dict.get('accel')
						layer = kakko_dict.get('layer')
						time = kakko_dict.get('time')
						path = kakko_dict.get('path')

						#kr→nscレイヤー   0=cg[s5] / 1=cg上[s4] / 2=カットイン[s3]  他は適当
						layer2 = str(int(5-int(layer)))

						path_list = re.findall(r'\(([0-9-]+),([0-9-]+),([0-9-]+)\)', path)
						time2 = str(int(int(time)/len(path_list)))

						for a in path_list:
							move_nsc += ':' if (not move_nsc == '') else ''		
							s1, effect_startnum, effect_list = effect_edit(time2, 'fade', effect_startnum, effect_list)
							move_nsc += 'layermove '+layer2+','+s1+','+a[0]+','+a[1]+','+a[2]

						#line = ';処理済\t' + line
						line = ''

					elif kr_cmd == 'wm':
						line = move_nsc
						move_nsc = ''
					
					elif kr_cmd == 'hsFlush':
						storage = kakko_dict.get('storage')#どうせ白塗り
						line = 'lsp 3,"bgimage\\' + storage + '.png":print 2:csp 3:print 2'

					elif kr_cmd == 'hsPlaySE':
						storage = kakko_dict.get('storage')
						sound_name = sound_dict.get(str(storage).lower())
						if storage and sound_name:
							line = 'dwave 0,"sound\\' + sound_name + '.ogg"'
						else:
							line = 'dwavestop 0'

					elif kr_cmd == 'hsChgBgm':
						#volume = kakko_dict.get('volume')
						#loop = kakko_dict.get('loop')
						storage = kakko_dict.get('storage')

						if storage:
							line = 'bgm "bgm\\' + storage + '.ogg"'

					elif kr_cmd == 'xchgbgm':
						#overlap = kakko_dict.get('overlap')
						#time = kakko_dict.get('time')
						storage = kakko_dict.get('storage')

						if storage:
							line = 'bgm "bgm\\' + storage + '.ogg"'

					elif kr_cmd == 'fadeinbgm':
						#loop = kakko_dict.get('loop')
						time = kakko_dict.get('time')
						storage = kakko_dict.get('storage')

						if storage:
							line = 'playfadein "bgm\\' + storage + '.ogg",' + time

					elif kr_cmd == 'fadeoutbgm':
						time = kakko_dict.get('time')

						line = 'stopfadeout '+ time

					elif kr_cmd == 'stopbgm':
						line = 'bgmstop'

					elif kr_cmd == 'playvideo':
						storage = kakko_dict.get('storage')

						line = 'mpegplay "video\\' + storage + '",%200'

					elif kr_cmd == 'hsEnd':
						line = 'mov %200,1:reset'

					#無変更時コメントアウト/変更時末尾に改行挿入
					#line = r';' + line if linedef == line else line + '\n'
					if linedef == line: line = ''
					elif line == '': pass
					else: line = (line + '\n')


				elif str_line:
					if str_line[2]:
						s='3' if str_line[3] else '2'
					else:
						s='1'

					line = 'msg "'+str_line[1]+'",'+s+'\n'

				else:#どれにも当てはまらない、よく分からない場合
					#print('err!:   '+line)
					#line = r';' + line#エラー防止の為コメントアウト
					line = ''

				txt += line

	add0txt_graphic = ''
	for im_path in glob.glob(os.path.join(image_dir, '*')):
		imname = (os.path.splitext(os.path.basename(im_path))[0])
		imfin = re.findall(r'ev_(..)_.{1,3}',imname)
		if imfin:
			add0txt_graphic += ('if $6=="'+imfin[0]+'" bg black,3:bg "image\\'+imname+'.png",3:click\n')

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換

		if e[1] == 'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

		else:
			add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"rule\\'+e[1]+'.png"\n'

	txt = txt.replace(r';<<-SE-DWAVE->>', 'dwave 0,"sound\\' + sound_dict['se_click'] + '.ogg"')
	txt = txt.replace(r';<<-GRAPHIC_VIEW->>', add0txt_graphic)
	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	open(os.path.join(same_hierarchy,'0.txt'), 'w', encoding='cp932', errors='ignore').write(txt)


#--------------------main--------------------
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	#パス代入
	#same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	same_hierarchy = str(pre_converted_dir)
	scenario_dir = os.path.join(same_hierarchy,'scenario')
	sound_dir = os.path.join(same_hierarchy,'sound')
	image_dir = os.path.join(same_hierarchy,'image')
	patch_dir = os.path.join(same_hierarchy,'patch')

	#本処理
	if not values: image_convert_msgwin(image_dir)#マルチコンバータ利用時はあとでやるので不要
	patch(patch_dir, scenario_dir, image_dir)
	sound_dict = music_rename(sound_dir)
	text_cnv(same_hierarchy, scenario_dir, image_dir, sound_dict)

	#不要ファイル削除
	for suffix in ['.ma','.asd', '.ks', '.tjs']:
		for junk in Path(pre_converted_dir).glob('**/*'+suffix): junk.unlink()


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()