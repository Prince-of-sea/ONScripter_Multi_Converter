#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageEnhance
import concurrent.futures
import subprocess as sp
import shutil, glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'Noesis',
		'date': 20130830,
		'title': 'ラブesエム',
		'cli_arg': 'noesis_loveesm',
		'requiredsoft': ['igscriptD'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'exe_name': ['ラブesエム'],
		'input_resolution': (1024, 768),#スクリプトで処理する解像度と実際の画像の解像度が合致しない場合後者をここに記入

		'version': [
			'ラブesエム FANZA DL版(gung_0004)',
		],

		'notes': [
			'強制的に1024x768→800x600に解像度が低下します',
			'画面特殊効果全般の実装が不完全(というか無)',
			'大多数の画像遷移は単純なフェードで代用',
			'wait処理の待ち時間が原作と違う',
			'セピア/モノクロ処理一切なし',
			'セーブ/ロード画面は超簡略化',
			'CG/音楽/回想モードは未実装(GALLERYはとりあえずOPを流せるようになってます)'
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for iga_name in ['bgimage', 'bgm', 'fgimage', 'script', 'se', 'system', 'video', 'voice']:
			p = Path(input_dir / Path(iga_name + '.iga'))
			e = Path(pre_converted_dir / iga_name)

			#なければ強制エラー
			if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)

	return


def default_txt():
	return ''';mode800
*define

caption "ラブesエム for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"ログ",lookback,"リセット",reset
savename "ＳＡＶＥ","ＬＯＡＤ","ＤＡＴＡ"
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
humanz 10
windowback

effect 10,10,500
effect 11,10,200

pretextgosub *pretext_lb
defsub errmsg
defsub SeVoiceLoading
defsub tati_set
defsub tati_load
defsub tati_reset
defsub def_SEset
defsub spmsg
defsub spmsg_end
defsub ADV_setting
game
;----------------------------------------
*errmsg
	csp -1:print 1
	bg black,1
	
	Ｃｏｎｖｅｒｔ　Ｅｒｒｏｒ！@
	このメッセージが見れるのはおかしいよ@
	クリックでタイトルに戻ります…\\
return


*SeVoiceLoading
	;se/voice周り
	if $11=="" return
	
	fileexist %0,"voice\\"+$11+".ogg"
	
	if %0==1 dwave 0,"voice\\"+$11+".ogg"
	if %0!=1 dwave 1,"se\\"+$11+".ogg"
	
	mov $11,""
return


*pretext_lb
	dwavestop -1
	
	;キャラ名中央表示用座標取得
	;詳細はミクキスコンバータ参照
	len %1,$10
	mov %2,(185-(%1/2)*(26+2)-2)/2
	
	lsp 8,":s;#000000"+$10,%2,425
	vsp 9,1
	print 1
	mov $10,""
	
	SeVoiceLoading
	saveon ;pretextgosub時終わりのsaveonは必須!!!!!!!!
return


*tati_set
	getparam $1,$2
	;if $18==$19 mov $17,"":mov $19,""
	
	if $16=="" mov $16,$1:mov $18,$2:goto *set_end
	if $18==$2 mov $16,$1:goto *set_end
	
	if $17=="" mov $17,$1:mov $19,$2:goto *set_end
	if $19==$2 mov $17,$1:goto *set_end
	*set_end
return


*tati_load
	vsp 9,0:vsp 8,0
	if $16!="" lsph 16 "image\\"+$16,0,0:getspsize 16,%1,%2
	if $17!="" lsph 17 "image\\"+$17,0,0:getspsize 17,%3,%4
	
	if $16!="" if $17=="" amsp 16,400-(%1/2),0:vsp 16,1
	if $16!="" if $17!="" amsp 16,250-(%1/2),0:amsp 17,550-(%3/2),0:vsp 16,1:vsp 17,1
	
	print 11
return

*tati_reset
	mov $16,"":mov $17,"":mov $18,"":mov $19,""
	csp 16:csp 17
return


*def_SEset
	getparam $0
	fileexist %0,"bgm\\"+$0+".ogg"
	
	if %0==1 bgm "bgm\\"+$0+".ogg"
	if %0!=1 mov $11,$0
return


*spmsg
	getparam $0
	bg black,1
	lsp 7 "image\\"+$0+".png",0,0
	print 10
return

*spmsg_end
	SeVoiceLoading
	click
	csp 7
	print 10
return


*ADV_setting
	csp -1:dwavestop -1:bgmstop
	setwindow 150,460,22,4,24,24,1,5,20,0,1,"image\\window_base.png",0,441
	abssetcursor 1,":a/8,100,2;image\\click_wait.png",735,535
	lsph 9 "image\\window_name.png",0,400
return
;----------------------------------------
;[memo]
;数字変数
;	%0~%9 getparam汎用
;	%100~109 途中選択肢用
;	%200 姉クリア
;	%201 恋人クリア
;	%202 全部クリア
;文字変数
;	$0~$9 getparam汎用
;	$10 キャラ名前
;	$11 se/voice
;	$16 立ち絵右
;	$17 立ち絵左
;	$18 立ち絵右name
;	$19 立ち絵左name
;	$60 途中選択肢用
;スプライト
;	8 名前
;	9 名前欄
;	16 立ち絵右
;	17 立ち絵左
;----------------------------------------
*staffroll
	
	;%150 再生時間
	;%151 ロール画像x - 使わん
	;%152 ロール画像y
	;%153 gettimer
	;%154 下記参照
	
	;ed曲の再生時間
	;mov %150,110078;今回は前段階で指定
	
	lsp 13,"image\\credit_join.png",220,0
	getspsize 13,%151,%152
	sub %152,600
	
	resettimer
	
	*staffroll_loop
		gettimer %153
		
		;(経過時間/再生時間)*ロール画像y
		mov %154,%153*%152/%150
		
		if %153<%150 amsp 13,220,0-%154:print 1
		if %153>%150 bgmstop:amsp 13,220,0-%152:print 1:goto *staffroll_end
	goto *staffroll_loop
	*staffroll_end
return
;----------------------------------------
*start
bg black,1


bg "image\\logo_n.png",10

;ブランドコール
rnd %6,3	;0~2
if %6==0 dwave 0,"se\\aya2204.ogg"
if %6==1 dwave 0,"se\\mix0002.ogg"
if %6==2 dwave 0,"se\\sis2311.ogg"

wait 1000
bg "image\\logo_n.png",10

wait 1000
bg "image\\CAUTION_02.png",10

wait 500
*title
ADV_setting

bg black,10

bg "image\\titlebase.png",10
bgm "bgm\\Lop.ogg"

;タイトルコール
rnd %7,5	;0~4   e\\s
if %7==0 dwave 0,"se\\aya2206.ogg"
if %7==1 dwave 0,"se\\aya2207.ogg"
if %7==2 dwave 0,"se\\mix0003.ogg"
if %7==3 dwave 0,"se\\sis2313.ogg"
if %7==4 dwave 0,"se\\sis2314.ogg"

lsp 30,":s;#440066#FFCCFFＮＥＷ　ＧＡＭＥ",  300,330
lsp 31,":s;#440066#FFCCFFＤＡＴＡ　ＬＯＡＤ",287,375
lsp 32,":s;#440066#FFCCFFＣＯＮＦＩＧ",      325,420
lsp 33,":s;#440066#FFCCFFＧＡＬＬＥＲＹ",    312,465
lsp 34,":s;#440066#FFCCFFＧＡＭＥ　ＥＮＤ",  300,510

lsph 40,":s;#FFFFFFＮＥＷ　ＧＡＭＥ",  300,330
lsph 41,":s;#FFFFFFＤＡＴＡ　ＬＯＡＤ",287,375
lsph 42,":s;#FFFFFFＣＯＮＦＩＧ",      325,420
lsph 43,":s;#FFFFFFＧＡＬＬＥＲＹ",    312,465
lsph 44,":s;#FFFFFFＧＡＭＥ　ＥＮＤ",  300,510


print 1

*title_loop
	bclear
	spbtn 30,30
	spbtn 31,31
	spbtn 32,32
	spbtn 33,33
	spbtn 34,34
	
	btnwait %50
	if %50!=-1 if %50!=0 dwave 1,"se\\sys_title.ogg"
	
	if %50==30 vsp 30,0:vsp 40,1:print 11:wait 500:ADV_setting:goto *SCR_start
	if %50==31 vsp 31,0:vsp 41,1:print 11:wait 500:csp -1:bg black,10:bg "image\\load_base.png",10:systemcall load:bg black,10:goto *title
	if %50==32 vsp 32,0:vsp 42,1:print 11:wait 500:csp -1:bg black,10:bg "image\\config_base.png",10:goto *volmenu_GUI
	if %50==33 vsp 33,0:vsp 43,1:print 11:wait 500:csp -1:bg black,10:goto *GALLERY_MODE
	if %50==34 vsp 34,0:vsp 44,1:print 11:wait 500:csp -1:bg black,10:end
	
goto *title_loop
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意
	;[注]上記URLのものとは完全に一致してません 若干改変入ってます
	
	
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
	getbgmvol   %130
	getsevol    %131
	getvoicevol %132
	
	;文字列変換
	itoa2 $141,%130
	itoa2 $142,%131
	itoa2 $143,%132
	
	;バー代入
	if %130==  0 mov $146,$130
	if %130== 10 mov $146,$131
	if %130== 20 mov $146,$132
	if %130== 30 mov $146,$133
	if %130== 40 mov $146,$134
	if %130== 50 mov $146,$135
	if %130== 60 mov $146,$136
	if %130== 70 mov $146,$137
	if %130== 80 mov $146,$138
	if %130== 90 mov $146,$139
	if %130==100 mov $146,$140
	if %131==  0 mov $147,$130
	if %131== 10 mov $147,$131
	if %131== 20 mov $147,$132
	if %131== 30 mov $147,$133
	if %131== 40 mov $147,$134
	if %131== 50 mov $147,$135
	if %131== 60 mov $147,$136
	if %131== 70 mov $147,$137
	if %131== 80 mov $147,$138
	if %131== 90 mov $147,$139
	if %131==100 mov $147,$140
	if %132==  0 mov $148,$130
	if %132== 10 mov $148,$131
	if %132== 20 mov $148,$132
	if %132== 30 mov $148,$133
	if %132== 40 mov $148,$134
	if %132== 50 mov $148,$135
	if %132== 60 mov $148,$136
	if %132== 70 mov $148,$137
	if %132== 80 mov $148,$138
	if %132== 90 mov $148,$139
	if %132==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］",  50, 50
	lsp 131,":s;#FFFFFF#666666テスト再生",250,450
	lsp 132,":s;#FFFFFF#666666リセット",  400,450
	lsp 133,":s;#FFFFFF#666666戻る",      550,450
	
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
	spbtn 133,133
	spbtn 136,136
	spbtn 138,138
	spbtn 141,141
	spbtn 143,143
	spbtn 146,146
	spbtn 148,148
	
	;入力待ち
	btnwait %140
	if %140!=-1 if %140!=0 dwave 1,"se\\sys_title.ogg"
	
	if %140==131 gosub *voice_test
	if %140==132 dwavestop 0:bgmvol 100:sevol 100:voicevol 100
	if %140==133 csp -1:dwavestop -1:bg black,10:goto *title
	if %140==136 if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=  0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	if %140==146 if %132!=  0 sub %132,10:voicevol %132
	if %140==148 if %132!=100 add %132,10:voicevol %132
	
goto *volmenu_loop
;----------------------------------------
*voice_test
	rnd %160,2
	if %160==0 dwave 0,"voice\\aya_voice.ogg"
	if %160==1 dwave 0,"voice\\sis_voice.ogg"
return
;----------------------------------------
*GALLERY_MODE
bg "image\\view_cg.png",10
click

bg black,10
mpegplay "video\\op.mpg",1

bg black,10
goto *title
;----------------------------------------
'''


def img_resize_main(p, DIR_IMG, values_ex):
	p_name = os.path.basename(p)
	p_r = os.path.join(DIR_IMG, p_name)

	if (not values_ex) or (str(p_name).lower() in ['window_base.png', 'load_base.png', 'config_base.png', 'view_cg.png']):

		im = Image.open(p)
		w = int(im.width * 600 / 768)
		h = int(im.height * 600 / 768)

		if values_ex: im_r = im#マルチコンバータ経由時は後で縮小
		else: im_r = im.resize((w, h), Image.Resampling.LANCZOS)

		#画像個別処理
		if str(p_name).lower() == 'window_base.png':
			im_r.putalpha(192)

		elif str(p_name).lower() == 'load_base.png':
			enhancer = ImageEnhance.Brightness(im_r)
			im_r = enhancer.enhance(0.4)

		elif str(p_name).lower() == 'config_base.png':
			enhancer = ImageEnhance.Brightness(im_r)
			im_r = enhancer.enhance(0.2)

		elif str(p_name).lower() == 'view_cg.png':
			enhancer = ImageEnhance.Brightness(im_r)
			im_r = enhancer.enhance(0.2)

		im_r.save(p_r)
	
	else:
		os.rename(p, p_r)
	
	return


def img_resize(DIR_BG, DIR_FG, DIR_SYS, DIR_IMG, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	l = []
	l += glob.glob(os.path.join(DIR_BG, '*.png'))
	l += glob.glob(os.path.join(DIR_FG, '*.png'))
	l += glob.glob(os.path.join(DIR_SYS, '*.png'))

	os.makedirs(DIR_IMG, exist_ok=True)

	#本処理 - マルチスレッドで高速化
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []
		for p in l: futures.append(executor.submit(img_resize_main, p, DIR_IMG, bool(values_ex)))
		concurrent.futures.as_completed(futures)

	#クレジット結合
	im1 = Image.open(os.path.join(DIR_IMG, 'credit_01.png'))
	im2 = Image.open(os.path.join(DIR_IMG, 'credit_02.png'))
	im3 = Image.open(os.path.join(DIR_IMG, 'credit_03.png'))
	imnew = Image.new('RGBA', (im1.width, im1.height+im2.height+im3.height))
	imnew.paste(im1, (0, 0))
	imnew.paste(im2, (0, im1.height))
	imnew.paste(im3, (0, im1.height+im2.height))
	imnew.save(os.path.join(DIR_IMG, 'credit_join.png'))


def text_dec_main(p, DIR_SCR, EXE_IGS, values_ex):
	if values_ex: from utils import subprocess_args # type: ignore
	n = (os.path.splitext(os.path.basename(p))[0])
	if values_ex: sp.run([EXE_IGS, '-p', p, n+'.txt'],  cwd=DIR_SCR, **subprocess_args())
	else: sp.run([EXE_IGS, '-p', p, n+'.txt'],  cwd=DIR_SCR)


def text_dec(DIR_SCR_DEC, DIR_SCR, EXE_IGS, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	os.makedirs(DIR_SCR_DEC, exist_ok=True)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for p in glob.glob(os.path.join(DIR_SCR, '*.s')):
			futures.append(executor.submit(text_dec_main,p, DIR_SCR, EXE_IGS, values_ex))

		concurrent.futures.as_completed(futures)

	for p in glob.glob(os.path.join(DIR_SCR, '*.txt')):
		shutil.move(p, DIR_SCR_DEC)


def text_cnv(DIR_SCR_DEC, ZERO_TXT):
	jmp_cnt = 0
	jmp_list = []

	# with open(DEFAULT_TXT) as f:
	# 	txt = f.read()
	txt = default_txt()

	for p in sorted(glob.glob(os.path.join(DIR_SCR_DEC, '*.txt'))):
		with open(p, encoding='cp932', errors='ignore') as f:

			name = os.path.splitext(os.path.basename(p))[0]
			txt += '\nerrmsg:reset\n;--------------- '+ name +' ---------------\n*SCR_'+ name +'\n'
			OPJ_flag = False

			for line in f:
				goto_line = re.search(r'[0-9\s]+\s([0-9A-z-_]+?)\.s', line)
				txt_line = re.search(r'0400\s[A-z0-9]{4}\s(＃)?(.+?)\n', line)
				bg_line = re.search(r'(040F|0410)\s[0-9A-z]{4}\s(.+?)\.bmp', line)
				tatiset_line = re.search(r'0412\s[A-z0-9]{4}\s(.+?)\n', line)
				tatiload_line = re.search(r'0814 0000 01F4 0000', line)
				tatireset_line = re.search(r'0811 0000 0000 0000', line)
				wait_line = re.search(r'080E 0000 0BB8 0000', line)
				wait2_line = re.match(r'080E 0000 05DC 0000', line)
				black_line = re.search(r'0816 0001 0000 0000', line)
				bgmstop_line = re.search(r'0824 0000 03E8 0000', line)
				se_line = re.match(r'([A-z0-9_-]+?)\n', line)
				spmsg_line = re.match(r'049C\s0901\s(.+?)\.png', line)
				spmsg_end_line = re.match(r'0475 0001 043F', line)
				OPTIONJUMP_line = re.match(r'!OPTIONJUMP!', line)
				#txt_line = re.search(r'', line)

				if re.search('^\n', line):#空行
					pass#そのまま放置

				elif goto_line:
					line = 'goto *SCR_' + goto_line[1] + '\n'

				elif txt_line:

					if txt_line[1]:
						line = 'mov $10,"' + txt_line[2] + '"\n'

					else:
						msg = re.sub(r'\<(.+?)\<(.+?)\>', r'(\1/\2)', txt_line[2])
						line = msg + '\\\n'

				elif bg_line:
					line = 'vsp 9,0:vsp 8,0:print 1:bg "image\\' + bg_line[2] + '.png",10\n'

				elif tatiset_line:
					line = 'tati_set "' + tatiset_line[1] + '","' + tatiset_line[1][:3] + '"\n'

				elif tatiload_line:
					line = 'tati_load\n'

				elif tatireset_line:
					line = 'tati_reset\n'

				elif wait_line:
					line = 'wait 2000\n'

				elif wait2_line:
					line = 'wait 2000\n'

				elif black_line:
					line = 'vsp 9,0:vsp 8,0:print 1:bg black,10\n'

				elif bgmstop_line:
					line = 'bgmstop\n'

				elif se_line:
					line = 'def_SEset "' + se_line[1] + '"\n'

				elif spmsg_line:
					line = 'spmsg "' + spmsg_line[1] + '"\n'

				elif spmsg_end_line:
					line = 'spmsg_end\n'

				elif OPTIONJUMP_line:
					OPJ_flag = True

					jmp_cnt += 1
					line = r';JMP_CNT' + str(jmp_cnt) + '_\n'
				
				elif OPJ_flag:
					OPJ_flag = False
					jmp_list.append(line[:-1])
					line = r';' + line#エラー防止の為コメントアウト

				else:
					line = '\n'
					#line = r';' + line#エラー防止の為コメントアウト

				txt += line

			txt += '\n;SCR_'+ name +'_END'

	#-----ガ バ ガ バ 修 正-----
	#OP
	txt = txt.replace(r'goto *SCR_0020', 'mpegplay "video\\op.mpg",1\ngoto *SCR_0020')
	#選択肢1
	txt = txt.replace(r';JMP_CNT1_', r'select "'+jmp_list[0]+r'",*S1A,"'+jmp_list[1]+r'",*S1B')
	txt = txt.replace(r'がっちりと腰', r'*S1A'+'\nがっちりと腰')
	txt = txt.replace(r'慌てて引', r'goto *S1END'+'\n*S1B\n慌てて引')
	txt = txt.replace('微かだった。\\', '微かだった。\\\n*S1END\n')
	#選択肢2
	txt = txt.replace(r';JMP_CNT3_', r'select "'+jmp_list[2]+r'",*S2A,"'+jmp_list[3]+r'",*S2B'+'\n*S2A')
	txt = txt.replace(r'引き抜いた―', 'goto *S2END\n*S2B\n引き抜いた―')
	txt = txt.replace(r'「……あやか、よ', '*S2END\n「……あやか、よ')
	#選択肢3
	txt = txt.replace(r';JMP_CNT5_', 'mov $60,""')
	txt = txt.replace(r';JMP_CNT6_', 'if %200==1 if %201==1 mov $60,"'+jmp_list[6]+'"')
	txt = txt.replace(r';JMP_CNT7_', r'select "'+jmp_list[4]+r'",*S3A,"'+jmp_list[5]+r'",*S3B,$60,*S3C'+'\n*S3A\nmov %100,1')
	txt = txt.replace(r'……どち', 'goto *S3END\n*S3B\nmov %100,2\n……どち')
	txt = txt.replace(r'……ダメだ。', 'goto *S3END\n*S3C\nmov %100,3\n……ダメだ。')
	txt = txt.replace('でいないと。\\', 'でいないと。\\\n*S3END\n')
	txt = txt.replace(r'goto *SCR_A0230', r'if %100==1 goto *SCR_A0230')
	txt = txt.replace(r'goto *SCR_B0450', r'if %100==2 goto *SCR_B0450')
	txt = txt.replace(r'goto *SCR_C0690', r'if %100==3 goto *SCR_C0690')
	#選択肢4
	txt = txt.replace(r';JMP_CNT8_', r'select "'+jmp_list[7]+r'",*S4A,"'+jmp_list[8]+r'",*S4B'+'\n*S4A')
	txt = txt.replace(r'正直、ち', '*S4B\n正直、ち')
	#選択肢5
	txt = txt.replace(r';JMP_CNT10_', r'select "'+jmp_list[9]+r'",*S5A,"'+jmp_list[10]+r'",*S5B'+'\n*S5A')
	txt = txt.replace('深く息をついた。\\', '深く息をついた。\\\ngoto *S5END\n*S5B')
	txt = txt.replace('体を擦り寄らせた。\\', '体を擦り寄らせた。\\\n*S5END')
	txt = txt.replace(r';SCR_a0650z_END', 'bgmstop:dwavestop -1:csp -1:reset')
	#選択肢6
	txt = txt.replace(r';JMP_CNT12_', r'select "'+jmp_list[11]+r'",*S6A,"'+jmp_list[12]+r'",*S6B'+'\n*S6B')
	txt = txt.replace(r'goto *SCR_A0420', 'goto *SCR_A0420\n*S6A')
	txt = txt.replace(r';SCR_A0660_END', 'bgmstop:dwavestop -1:csp -1:reset')
	txt = txt.replace(r';SCR_A0440Z_END', 'bgmstop:dwavestop -1:skipoff:mov %200,1:bgmonce "bgm\\Led_a.ogg":bg "image\\ed1_ayaka.png",10:mov %150,93066:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED1
	#選択肢7
	txt = txt.replace(r';JMP_CNT14_', r'select "'+jmp_list[13]+r'",*S7A,"'+jmp_list[14]+r'",*S7B'+'\n*S7A')
	txt = txt.replace(r'goto *SCR_B0540A', 'goto *SCR_B0540A\n*S7B')
	txt = txt.replace(r';SCR_B0670_END', 'bgmstop:dwavestop -1:csp -1:reset')
	#選択肢8
	txt = txt.replace(r';JMP_CNT16_', r'select "'+jmp_list[15]+r'",*S8A,"'+jmp_list[16]+r'",*S8B'+'\n*S8B')
	txt = txt.replace(r'goto *SCR_B0630', 'goto *SCR_B0630\n*S8A')
	txt = txt.replace(r';SCR_b0680z_END', 'bgmstop:dwavestop -1:csp -1:reset')
	txt = txt.replace(r';SCR_B0640Z_END', 'bgmstop:dwavestop -1:skipoff:mov %201,1:bgmonce "bgm\\Led_a.ogg":bg "image\\ed2_ayaka.png",10:mov %150,93066:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED2
	#選択肢9
	txt = txt.replace(r';JMP_CNT18_', r'select "'+jmp_list[17]+r'",*S9A,"'+jmp_list[18]+r'",*S9B'+'\n*S9A\nmov %101,1')
	txt = txt.replace('の準備を始めた。\\', 'の準備を始めた。\\\ntati_reset')
	txt = txt.replace('るさを感じた。\\', 'るさを感じた。\\\ngoto *SCR_C0700Z\n*S9B\nmov %101,2')
	txt = txt.replace('着てもらう。\\', '着てもらう。\\\nif %101==2 goto *S9SKIP')
	txt = txt.replace('かは顔を見合わせ、それからにっこりと笑って言った。\\', 'かは顔を見合わせ、それからにっこりと笑って言った。\\\ngoto *S9END\n*S9SKIP')
	txt = txt.replace('華は顔を見合わせ、それからにっこりと笑って言った。\\', '華は顔を見合わせ、それからにっこりと笑って言った。\\\n*S9END')
	txt = txt.replace(';SCR_C0700Z_END', 'tati_reset:csp -1:bgmstop:dwavestop -1:skipoff:mov %202,1:bgmonce "bgm\\Led_s.ogg":bg "image\\ed3_harem.png",10:mov %150,126007:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED3

	open(ZERO_TXT, 'w', encoding='cp932', errors='ignore').write(txt)


def file_check(EXE_IGS, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS):
	c = True
	for p in [EXE_IGS, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS]:
		if not os.path.exists(p):
			print(p+ ' is not found!')
			c = False
	
	return c


def junk_del(DIR_BG, DIR_FG, DIR_SYS, DIR_SCR, DIR_SCR_DEC, debug):
	shutil.rmtree(DIR_BG)
	shutil.rmtree(DIR_FG)
	shutil.rmtree(DIR_SYS)
	shutil.rmtree(DIR_SCR)
	shutil.rmtree(DIR_SCR_DEC)


def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	#デバッグ
	debug = 0

	same_hierarchy = str(pre_converted_dir)#(os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入

	if values:
		from requiredfile_locations import location # type: ignore
		EXE_IGS = str(location('igscriptD'))

	else:
		EXE_IGS = os.path.join(same_hierarchy,'igscriptD.exe')

	#DEFAULT_TXT = os.path.join(same_hierarchy,'default.txt')

	if debug: same_hierarchy = os.path.join(same_hierarchy,'Gungnir_loveesm_EXT')#debug
	ZERO_TXT = os.path.join(same_hierarchy,'0.txt')
	DIR_SCR = os.path.join(same_hierarchy,'script')
	DIR_SCR_DEC = os.path.join(same_hierarchy,'script_dec')

	DIR_BG = os.path.join(same_hierarchy,'bgimage')
	DIR_FG = os.path.join(same_hierarchy,'fgimage')
	DIR_SYS = os.path.join(same_hierarchy,'system')
	DIR_IMG = os.path.join(same_hierarchy,'image')

	if file_check(EXE_IGS, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS):
		img_resize(DIR_BG, DIR_FG, DIR_SYS, DIR_IMG, values_ex)
		text_dec(DIR_SCR_DEC, DIR_SCR, EXE_IGS, values_ex)
		text_cnv(DIR_SCR_DEC, ZERO_TXT)
		junk_del(DIR_BG, DIR_FG, DIR_SYS, DIR_SCR, DIR_SCR_DEC, debug)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()