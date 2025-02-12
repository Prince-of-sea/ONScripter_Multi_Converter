#!/usr/bin/env python3
from PIL import Image, ImageEnhance
from pathlib import Path
import concurrent.futures
import subprocess as sp
import soundfile, chardet, shutil, glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'Liar-soft',
		'date': 20050218,
		'title': 'SEVEN-BRIDGE',
		'requiredsoft': ['gscScriptCompAndDecompiler-cli'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'SEVEN-BRIDGE〜セブンブリッジ〜 FANZA DL版(ggs_0251)',
		],

		'notes': [
			'立ち絵や背景にそこそこ表示/削除ミスあり',
			'背景変化時の暗転を挟む処理が行われない',
			'大多数の画像遷移は単純なフェードで代用',
			'セピア/モノクロ/色反転処理一切なし',
			'一部音声が鳴らない/消えない',
			'セーブ/ロード画面は超簡略化',
			'立ち絵はすべて瞬間表示',
			'CG/回想モードは未実装'
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	movout_dir = Path(pre_converted_dir / 'mov')
	movout_dir.mkdir()

	for file_name in ['0002.mpg', '0003.mpg', '0004.mpg']:
		p = Path(input_dir / 'mov' / file_name)
		
		#なければ強制エラー
		if not p.exists(): raise ValueError(str(p)+' not found.')
		
		shutil.copy(p, movout_dir)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xfl_name in ['wav', 'voice', 'scr', 'grps', 'grpo_bu', 'grpo', 'grpe', 'bgm']:
			p = Path(input_dir / Path(xfl_name + '.xfl'))
			e = Path(pre_converted_dir / xfl_name)

			#なければ強制エラー
			if not p.exists(): raise ValueError(str(p)+' not found.')

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)
	
	v1_outpath = Path(pre_converted_dir / 'voice' / '1.xfl')
	v1_outdir = Path(pre_converted_dir / '1')
	
	extract_archive_garbro(v1_outpath, v1_outdir, 'png')
	v1_outpath.unlink()

	return


def default_txt():
	return ''';mode800
*define

caption "SEVEN-BRIDGE for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
humanz 10
windowback

defsub tati
defsub voice
defsub flush
defsub csp_all
defsub name_img
defsub bg_change
defsub bgmfadeout_def

effect 8,10,70
effect 9,10,1800
effect 10,10,200
;<<-EFFECT->>

game
;----------------------------------------
*name_img
	getparam $50
	lsp 2,"grps\\"+$50+".png",7,479
	print 1
return

*bg_change
	csp 20
	dwavestop 0
	bg $51,%52
	csp 11
	print 1
	mov $51,"":mov %52,0
return

*bgmfadeout_def
	getparam %53
	dwavestop 1
	bgmfadeout %53
	bgmstop
	bgmfadeout 0
return

*flush
	getparam %54
	lsp 1,"grpe\\0888.png",0,0
	print 1
	wait %54
	csp 1
	print 1
return

*voice
	getparam $55,%56
	if %56==0 dwave 0,"voice_dec\\"+$55
	if %56==1 dwave 0,"1_dec\\"+$55
return

*tati
	getparam %57,%58,%59,%60
	
	;立ち絵か演出かの判定値 - 絶対20じゃないけど正解がわからないためこのまま
	if %57< 20 mov $61,"grpo\\"
	if %57>=20 mov $61,"grpo_bu\\"
	itoa $62,%58
	
	lsp %57,$61+$62+".png",%59,%60
	print 1
	mov $61,""
return

*csp_all
	for %62=11 to 50
		csp %62
	next
	print 1
return
;----------------------------------------
*start

;;;原作の「。とか、を行頭に表示させない」が
;;;再現できなかったので仕方なく横は原作+1
setwindow 153,477,21+1,4,24,24,0,5,40,0,0,#999999,0,470,799,599

;bgmvol 50		;BGM音量
;voicevol 100	;ボイス音量
;defsevol 30	;効果音音量
;mov %334,1		;クリア判定

mpegplay "mov\\0002.mpg",1
;----------------------------------------
*title
	csp -1
	bg white,8
	bg "grpe\\3001.png",10
	bgm "bgm_dec\\Track01.wav"

	lsp 71,":a/3,0,3;grpo\\9000_.png",516,105:print 8
	lsp 72,":a/3,0,3;grpo\\9010_.png",516,166:print 8
	lsp 73,":a/3,0,3;grpo\\9020_.png",516,227:print 8
	lsp 74,":a/3,0,3;grpo\\9030_.png",516,290:print 8
	if %334==1 lsp 75,":a/3,0,3;grpo\\9040_.png",516,352:print 8
	lsp 76,":a/3,0,3;grpo\\9050_.png",516,417:print 8


*title_loop
	bclear
	btrans

	spbtn 71,1
	spbtn 72,2
	spbtn 73,3
	spbtn 74,4
	if %334==1 spbtn 75,5
	spbtn 76,6

	btnwait %6
	print 1

	if %6==1 gosub *start_set:goto *scenario_0
	if %6==2 gosub *start_set:goto *scenario_1
	if %6==3 gosub *start_set:bg #4f9eff,10:systemcall load:bg black,10:goto *title
	if %6==4 gosub *start_set:bg "grps\\confback_.png",10:goto *volmenu_GUI
	if %6==5 gosub *start_set:bg black,10:gosub *mov:goto *title
	if %6==6 gosub *start_set:end
goto *title_loop

;----------------------------------------
*start_set
	dwave 1,"wav_dec\\0001.wav"
	csp 71
	csp 72
	csp 73
	csp 74
	csp 75
	csp 76
	bg black,9
	bgmfadeout_def 500
return
;----------------------------------------
*mov
	mpegplay "mov\\0003.mpg",1
	click
	mpegplay "mov\\0004.mpg",1
	click
return
;----------------------------------------
;;;シナリオ接続

*scenario_0
	gosub *2001_gsc
	mpegplay "mov\\0003.mpg",0

*scenario_1
	gosub *2002_gsc
	gosub *2003_gsc
	gosub *2004_gsc
	gosub *2005_gsc
	gosub *2006_gsc
	gosub *2007_gsc
	gosub *2008_gsc
	gosub *2009_gsc
	gosub *2010_gsc
	gosub *2011_gsc
	gosub *2024_gsc
	gosub *2025_gsc
	gosub *2026_gsc
	gosub *2027_gsc
	gosub *2028_gsc
	gosub *2029_gsc
	gosub *2030_gsc
	gosub *2031_gsc
	gosub *2032_gsc
	gosub *2033_gsc
	gosub *2034_gsc
	gosub *2035_gsc
	gosub *2036_gsc
	gosub *2037_gsc
	gosub *2052_gsc
	gosub *2053_gsc
	gosub *2054_gsc
	gosub *2055_gsc
	gosub *2056_gsc
	gosub *2057_gsc
	gosub *2058_gsc
	gosub *2059_gsc
	gosub *2060_gsc
	gosub *2065_gsc
	gosub *2066_gsc
	gosub *2401_gsc
	gosub *2402_gsc
	gosub *2403_gsc
	gosub *2404_gsc
	gosub *2405_gsc
	gosub *2406_gsc
	gosub *2407_gsc
	gosub *2501_gsc
	gosub *2502_gsc
	gosub *2601_gsc
	gosub *2602_gsc
	gosub *2603_gsc
	gosub *2701_gsc
	gosub *2702_gsc
	gosub *2703_gsc
	gosub *2801_gsc
	mpegplay "mov\\0004.mpg",0

	mov %334,1:goto *title

;----------------------------------------
*GAMEOVER01
	bg "grpe\\1140.png",10:wait 1000
	bg "grpe\\1150.png",10:wait 200
	bgm "bgm_dec\\Track02.wav"
	select "コンティニューする　",*GO01A,"コンティニューしない",*GO01B
	*GO01A
		*bgmfadeout_def 500
		return *2011_gsc
	*GO01B
		*bgmfadeout_def 500
		return *start
		
;----------------------------------------
*GAMEOVER02
	bg "grpe\\1141.png",10:wait 1000
	bg "grpe\\1151.png",10:wait 200
	bgm "bgm_dec\\Track02.wav"
	select "コンティニューする　",*GO02A,"コンティニューしない",*GO02B
	*GO02A
		*bgmfadeout_def 500
		return *2037_gsc
	*GO02B
		*bgmfadeout_def 500
		return *start
		
;----------------------------------------
*GAMEOVER03
	bg "grpe\\1142.png",10:wait 1000
	bg "grpe\\1152.png",10:wait 200
	bgm "bgm_dec\\Track02.wav"
	select "コンティニューする　",*GO03A,"コンティニューしない",*GO03B
	*GO03A
		*bgmfadeout_def 500
		return *2060_gsc
	*GO03B
		*bgmfadeout_def 500
		return *start
		
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
	
	if %140==131 bgmvol 100:sevol 100:voicevol 100
	if %140==132 csp -1:reset
	if %140==136 if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=  0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	if %140==146 if %132!=  0 sub %132,10:voicevol %132
	if %140==148 if %132!=100 add %132,10:voicevol %132
	
goto *volmenu_loop
;----------ここまでdefault.txt----------
'''

#[!]なにもかも解析途中です これをそのまま他作品に使い回さないでください


def effect_edit(t,f, el, es):

	list_num = 0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(el,es+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			el.append([t,f])
			list_num = len(el)+es

	return str(list_num), el, es


def music_cnv_main(i):
	dd = (os.path.dirname(i) + '_dec')
	dp = (os.path.join(dd, os.path.splitext(os.path.basename(i))[0] + '.wav'))
	os.makedirs(dd, exist_ok=True)
	soundfile.write(dp, soundfile.read(i)[0], soundfile.read(i)[1])
	return


def music_cnv(PATH_D, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	d1 = glob.glob(os.path.join(PATH_D['DIR_WAV'], '*.*'))
	d2 = glob.glob(os.path.join(PATH_D['DIR_BGM'], '*.*'))
	d3 = glob.glob(os.path.join(PATH_D['DIR_VOICE'], '*.*'))
	d4 = glob.glob(os.path.join(PATH_D['DIR_1'], '*.*'))

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:#garbroで取り出した音源のヘッダが仕様怪しいのでsoundfile通してwavへ変換 - マルチスレッドで高速化
		futures = []
		for i in (d1 + d2 + d3 + d4):
			futures.append(executor.submit(music_cnv_main, i))
		
		concurrent.futures.as_completed(futures)
		


def image_cnv(PATH_D):
	for p in glob.glob(os.path.join(PATH_D['DIR_GRPO'], '*.png')):
		n = (os.path.splitext(os.path.basename(p))[0])

		if (int(n) >= 9000) and (int(n) < 9100):
			result = (os.path.join(os.path.dirname(p), n + '_' + os.path.splitext(p)[1]))
			p2 = (os.path.join(os.path.dirname(p), str(int(n)+100)+os.path.splitext(p)[1]))#名前に+100
			
			im_p = Image.open(p)
			im_p2 = Image.open(p2)
			
			im = Image.new('RGBA', (im_p.width*3, im_p.height))
			im.paste(im_p, (0, 0))
			im.paste(im_p2, (im_p.width, 0))
			im.paste(im_p2, (im_p.width*2, 0))

			im.save(result)

	for p in glob.glob(os.path.join(PATH_D['DIR_GRPS'], '*.png')):
		n = (os.path.splitext(os.path.basename(p))[0])
		if str(n).lower() == 'confback':
			result = (os.path.join(os.path.dirname(p), n + '_' + os.path.splitext(p)[1]))
			im = Image.open(p)
			enhancer = ImageEnhance.Brightness(im)
			im = enhancer.enhance(0.2)
			im.save(result)


def text_cnv(PATH_D):
	# with open(PATH_D['DEFAULT_TXT']) as f:
	# 	txt = f.read()
	txt = default_txt()
	
	sp_reverse = 50
	effect_list = []
	effect_startnum = 10

	for p in glob.glob(os.path.join(PATH_D['DIR_SCR_DEC'], '*.txt')):
		line_mode = False
		
		with open(p, 'rb') as f:
			char_code = chardet.detect(f.read())['encoding']

		with open(p, encoding=char_code, errors='ignore') as f:

			name = os.path.splitext(os.path.basename(p))[0]
			txt += '\n;--------------- '+ name +' ---------------\n*'+ name.replace('.', '_') +'\n\n'

			for line in f:
				line_def = line
				line_hash = re.search(r'#([A-z0-9]+?)\n', line)
				line_snr = re.search(r'(\^g[0-9]{3})(.+?)\n', line)

				JUMP_var1 = re.search(r'\@([A-z0-9]+)', line)
				
				if re.search('^\n', line):#空行
					pass#そのまま放置

				elif line_hash:
					line = r';' + line

					if line_mode == 'scenario':
						line = '\\\n' + line
					
					line_mode = line_hash[1]
					
				elif JUMP_var1:
					line = '*JUMP_'+name.replace('.', '_')+'_'+JUMP_var1[1]+'\n'

					if line_mode == 'scenario':
						line = '\\\n' + line

					line_mode = False

				elif line_snr:
					line = 'name_img "gf'+line_snr[1][2:]+'"\n'+line_snr[2]+'\n'
					line_mode = 'scenario'

				else:#どれにも当てはまらない、よく分からない場合
					if line_mode == 'scenario':
						pass

					else:
						JUMP_var2 = re.search(r'\[([A-z0-9]+?)\]', line)

						if (line_mode == 'JUMP') and JUMP_var2:
							line = 'goto *JUMP_'+name.replace('.', '_')+'_'+JUMP_var2[1]+'\n'

						elif line_mode == 'MESSAGE':#メッセージ
							MESS_var1 = re.search(r'\[0, ([0-9]+?), 0, 0, -1, -1, (1|0)\]', line)

							if MESS_var1[1] == '0':
								line = ';voice ""\n'
							else:
								MESS_b = bool(int(MESS_var1[1]) > 10000)
								MESS = MESS_var1[1][1:] if MESS_b else MESS_var1[1]
								line = 'voice "'+MESS+'.wav",'+str(int(MESS_b))+'\n'

						elif line_mode == '66':#メッセージ2
							MESS_var2 = re.search(r'\[([0-9]+?), 0, 0, 0\]', line)

							if MESS_var2:
								MESS_b = bool(int(MESS_var2[1]) > 10000)
								MESS = MESS_var2[1][1:] if MESS_b else MESS_var2[1]
								line = 'voice "'+MESS+'.wav",'+str(int(MESS_b))+'\n'

						elif line_mode == '60':#BGM
							BGM_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'bgm "bgm_dec\\Track'+(BGM_var[1]).zfill(2)+'.wav"\n'

						elif line_mode == 'IMAGE_DEF':#スプライト
							DEF_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'tati '+str(sp_reverse-int(DEF_var[1]))+','+DEF_var[2]+','+DEF_var[3]+','+DEF_var[4]+'\n'

						elif line_mode == '36':#スプライト除去
							SP_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'vsp '+str(sp_reverse-int(SP_var[1]))+','+SP_var[2]+'\n'

						elif line_mode == 'PAUSE':#ウェイト
							PAUSE_var = re.search(r'\[([0-9]+?)\]', line)
							line = 'wait '+PAUSE_var[1]+'00\n'

						elif line_mode == '6144':#背景だよ 501が背景名/502がエフェクト/503で開始？
							BG_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)

							if BG_var[2] == '501':
								line = 'mov $51,"grpe\\'+(BG_var[3]).zfill(4)+'.png"\n'

							elif BG_var[2] == '502':
								ee, effect_list, effect_startnum = effect_edit('500', BG_var[3], effect_list, effect_startnum)
								line = 'mov %52,' + ee + ':bg_change\n'

						elif line_mode == '62':#効果音だよ
							SE_var = re.search(r'\[([0-9]+?)\]', line)
							line = 'dwave 1,"wav_dec\\'+(SE_var[1]).zfill(4)+'.wav"\n'

						elif line_mode == '61':#BGMのフェードアウト ホントはSEにもやったほうがいいけど面倒なので放置
							FADE_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'bgmfadeout_def '+(FADE_var[2])+'\n'

						elif line_mode == '24':# flush [x100ミリ秒,X]
							FL_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'flush '+(FL_var[1])+'00\n'

						elif line_mode == '23':# quake [x100ミリ秒,強さ(0有るので+1推奨),X,X]
							QU_var = re.search(r'\[([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							line = 'quake '+str((int(QU_var[2])+1)*2)+','+(QU_var[1])+'00\n'

						elif line_mode == '43':
							ES_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)

							if ES_var[1] != '0':#画像素材の関係で仕方なくコメントアウトしてます
								line = ';lsp 52,"grps\\es'+ES_var[1].zfill(3)+'.png",0,0:print 10\n'
							else:
								line = ';csp 52:print 10\n'

						elif line_mode == '64':
							line = 'csp 11:print 1\n'

						elif line_mode == 'IMAGE_GET':
							BG_var = re.search(r'\[([0-9]+?), ([0-9]+?)\]', line)
							line = 'bg "grpe\\'+BG_var[1].zfill(4)+'.png",10\n'

						elif line_mode == 'IMAGE_SET':
							line = 'csp_all\n'

						elif line_mode == '15':#gosub的な?
							BG_var = re.search(r'\[([0-9]+?), -1, ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?), ([0-9]+?)\]', line)
							if(int(BG_var[1]) > 1000):
								line = 'gosub *'+BG_var[1]+'_gsc\n'


						if line_def == line:
							line = r';' + line#エラー防止の為コメントアウト
						
						line_mode = False

				txt += line

			txt += '\nbgmstop:dwavestop 0:dwavestop 1:csp -1\nreturn\n'

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換

		if (int(e[1]) >= 24) or (int(e[1]) <= 11):#efXX.pngは11~24なのでそれ以外の指定はとりあえずフェードにしてごまかす
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

		else:
			add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"grps\\ef'+e[1]+'.png"\n'

	#-----ガ バ ガ バ 修 正-----
	# 第一章
	txt = txt.replace(r';モーガンの言', r'name_img "gf003":select "モーガンの言いなりにはならない！",*JUMP_2011_gsc_9,"いちかばちか、やってみる！",*JUMP_2011_gsc_11;')
	txt = txt.replace('\n*JUMP_2011_gsc_16', '\ngoto *GAMEOVER01\n*JUMP_2011_gsc_16')
	txt = txt.replace(r';青', r'name_img "gf003":select "黄色いマスコン",*JUMP_2011_gsc_16,"青いマスコン",*JUMP_2011_gsc_18,"緑のマスコン",*JUMP_2011_gsc_19;')
	txt = txt.replace(r';先端', r'name_img "gf003":select "先端",*JUMP_2011_gsc_25,"中央",*JUMP_2011_gsc_27,"根元",*JUMP_2011_gsc_28;')
	txt = txt.replace('\ntati 25,2001,0,0', '\ntati 11,2001,0,0')#これやんないと一部の雪が降る場面で唐突にモーガン出てくるの草
	txt = txt.replace(r';とにかく進', r'name_img "gf003":select "とにかく進む",*JUMP_2011_gsc_34,"進めるもんか",*JUMP_2011_gsc_36;')
	txt = txt.replace('\n*JUMP_2011_gsc_36', '\ngoto *GAMEOVER01\n*JUMP_2011_gsc_36')
	txt = txt.replace('tati 21,1946,0,0', '')
	txt = txt.replace('\nまた会える？', 'csp 21:print 1\nまた会える？')
	# 第二章
	txt = txt.replace('呟いたチ', 'csp 21:print 1\n呟いたチ')
	txt = txt.replace('\n謎めいた魔', '\ncsp_all\n謎めいた魔')
	txt = txt.replace('tati 19,2001,65186,0', 'tati 24,2001,65186,0')
	txt = txt.replace('で掴んだ。\n', 'で掴んだ。\\\nname_img "gf003":select "黄色いマスコンを、奥へ倒す",*JUMP_2037_gsc_3,"黄色いマスコンを、手前に引く",*JUMP_2037_gsc_5;')
	txt = txt.replace('\n*JUMP_2037_gsc_5', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_5')
	txt = txt.replace('ねえな？\n', 'ねえな？\\\nname_img "gf003":select "黄色いマスコンを、奥へ倒す",*JUMP_2037_gsc_8,"黄色いマスコンを、手前に引く",*JUMP_2037_gsc_10;')
	txt = txt.replace('\n*JUMP_2037_gsc_11', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_11')
	txt = txt.replace(';チョト・チェルパンに', 'name_img "gf003":select "チョト・チェルパンに同化する",*JUMP_2037_gsc_15,"チョグルに同化する",*JUMP_2037_gsc_17,"世界樹の根に同化する",*JUMP_2037_gsc_18;')
	txt = txt.replace('\n*JUMP_2037_gsc_17', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_17')
	txt = txt.replace('\n*JUMP_2037_gsc_19', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_19')
	txt = txt.replace(';チョグルを', 'name_img "gf003":select "チョグルを止める",*JUMP_2037_gsc_22,"チョグルに任せる",*JUMP_2037_gsc_24;')
	txt = txt.replace('\n*JUMP_2037_gsc_25', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_25')
	txt = txt.replace(';モ', 'name_img "gf003":select "モーガンに呼びかける",*JUMP_2037_gsc_28,"自分にできることをする",*JUMP_2037_gsc_30;')
	txt = txt.replace('\n*JUMP_2037_gsc_30', '\ngoto *GAMEOVER02\n*JUMP_2037_gsc_30')
	# 第三章
	txt = txt.replace(';白いマスコンの力を敵', 'name_img "gf003":select "白いマスコンの力を敵へ向ける",*JUMP_2060_gsc_3,"白いマスコンの力を自分に使う",*JUMP_2060_gsc_5;')
	txt = txt.replace('\n*JUMP_2060_gsc_5', '\ngoto *GAMEOVER03\n*JUMP_2060_gsc_5')
	txt = txt.replace(';ジェーンの心', 'name_img "gf003":select "ジェーンの心を読む",*JUMP_2060_gsc_8,"ジェーンの出方を考える",*JUMP_2060_gsc_10')
	txt = txt.replace('\n*JUMP_2060_gsc_10', '\ngoto *GAMEOVER03\n*JUMP_2060_gsc_10')
	# 第五章
	txt = txt.replace(';[15044, 999, 0, 0]', 'csp 10:print 1')
	# 第六章
	txt = txt.replace('tati 20,3152,0,0\n;#60', ';')
	txt = txt.replace('頬をくすぐり', 'tati 20,3152,0,0\n頬をくすぐり')
	txt = txt.replace('お幸せに！\n\\', 'お幸せに！\\\nname_img "gf003"\n')

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	open(PATH_D['ZERO_TXT'], 'w', errors='ignore').write(txt)
	

def file_check(PATH_D):
	c = True
	for p in [PATH_D['DIR_1'], PATH_D['DIR_BGM'], PATH_D['DIR_GRPE'], PATH_D['DIR_GRPO'], PATH_D['DIR_GRPO_BU'], PATH_D['DIR_GRPS'], PATH_D['DIR_SCR'], PATH_D['DIR_VOICE'], PATH_D['DIR_WAV'], PATH_D['EXE_GSC']]:
		if not os.path.exists(p):
			print(p+ ' is not found!')
			c = False
	
	return c


def text_dec_main(p, PATH_D, values_ex):
	if values_ex: from utils import subprocess_args
	n = (os.path.splitext(os.path.basename(p))[0])
	if int(n) >= 2000:
		if values_ex: sp.run([PATH_D['EXE_GSC'], '-m', 'decompile', '-i', p], shell=True, cwd=PATH_D['DIR_SCR'], **subprocess_args(True))
		else: sp.run([PATH_D['EXE_GSC'], '-m', 'decompile', '-i', p], shell=True, cwd=PATH_D['DIR_SCR'])
	return


def text_dec(PATH_D, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	os.makedirs(PATH_D['DIR_SCR_DEC'], exist_ok=True)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:#gscをtxtへデコード - マルチスレッドで高速化
		futures = []
		for p in glob.glob(os.path.join(PATH_D['DIR_SCR'], '*.gsc')):
			futures.append(executor.submit(text_dec_main, p, PATH_D, bool(values_ex)))
		
		concurrent.futures.as_completed(futures)
		
	for p in glob.glob(os.path.join(PATH_D['DIR_SCR'], '*.txt')):
		shutil.move(p, PATH_D['DIR_SCR_DEC'])


def junk_del(PATH_D):
	for d in [PATH_D['DIR_1'], PATH_D['DIR_BGM'], PATH_D['DIR_SCR'], PATH_D['DIR_SCR_DEC'], PATH_D['DIR_VOICE'], PATH_D['DIR_WAV']]:
		shutil.rmtree(d)
	

def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	same_hierarchy = str(pre_converted_dir)#(os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	#same_hierarchy = os.path.join(same_hierarchy,'SBridge')#debug

	PATH_D = {
		#grpo_exは不要
		'DIR_1'      :os.path.join(same_hierarchy,'1'),
		'DIR_BGM'    :os.path.join(same_hierarchy,'bgm'),
		'DIR_GRPE'   :os.path.join(same_hierarchy,'grpe'),
		'DIR_GRPO'   :os.path.join(same_hierarchy,'grpo'),
		'DIR_GRPO_BU':os.path.join(same_hierarchy,'grpo_bu'),
		'DIR_GRPS'   :os.path.join(same_hierarchy,'grps'),
		'DIR_SCR'    :os.path.join(same_hierarchy,'scr'),
		'DIR_VOICE'  :os.path.join(same_hierarchy,'voice'),
		'DIR_WAV'    :os.path.join(same_hierarchy,'wav'),

		'DIR_SCR_DEC':os.path.join(same_hierarchy,'scr_dec'),
		#'DEFAULT_TXT':os.path.join(same_hierarchy,'default.txt'),
		'ZERO_TXT'   :os.path.join(same_hierarchy,'0.txt')
	}


	if values:
		from requiredfile_locations import location
		PATH_D['EXE_GSC'] = str(location('gscScriptCompAndDecompiler-cli'))

	else:
		PATH_D['EXE_GSC'] = os.path.join(same_hierarchy,'gscScriptCompAndDecompiler.exe')

	if file_check(PATH_D):
		music_cnv(PATH_D, values_ex)
		image_cnv(PATH_D)
		text_dec(PATH_D, values_ex)
		text_cnv(PATH_D)
		junk_del(PATH_D)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()