#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import subprocess as sp
import tempfile, shutil, glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'アパタイト',
		'date': 20210702,
		'title': '[アパタイト]祖母シリーズHD汎用 (2021〜2022)',
		'cli_arg': 'aptit_soboHD',
		'requiredsoft': ['Kikiriki'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'exe_name': ['ObaachanMamaHaSasetekuretayo', 'inrambaachan'],

		'version': [
			#字面終わってるので申し訳程度のutf-8エンコード
			str(b'\xe3\x81\x8a\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x80\x81\xe3\x83\x9e\xe3\x83\x9e\xe3\x81\xaf\xe3\x81\x95\xe3\x81\x9b\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x82\x88\xef\xbc\x9f \xe3\x80\x9c\xe6\x81\xaf\xe5\xad\x90\xe3\x81\xbf\xe3\x81\x9f\xe3\x81\x84\xe3\x81\xab\xe5\xa5\xaa\xe3\x82\x8f\xe3\x81\x9b\xe3\x81\xaa\xe3\x81\x84\xe3\x82\x8f\xef\xbc\x81\xe3\x80\x9c FANZA DL\xe7\x89\x88(aman_0514)'.decode('utf-8')),
			str(b'\xe8\xa1\xb0\xe3\x81\x88\xe7\x9f\xa5\xe3\x82\x89\xe3\x81\x9a\xe3\x81\xae\xe6\xb7\xab\xe4\xb9\xb1\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xef\xbc\x81 \xe3\x80\x9c\xe5\xad\xab\xe3\x81\xae\xe8\x82\x89\xe6\xa3\x92\xe3\x82\x82\xe3\x81\x84\xe3\x81\x9f\xe3\x81\xa0\xe3\x81\x8d\xe3\x81\xbe\xe3\x81\x99\xe2\x99\xaa\xe3\x80\x9c FANZA DL\xe7\x89\x88(aman_0637)'.decode('utf-8')),
		],

		'notes': [
			'好感度調整未実装(好感度分岐部分では全て選択肢が出ます)',
			'体験版の動作確認は取ってません(動かない可能性が高い)',
			'いくつかのウィンドウ表示が原作と異なります',
			'システム周りの効果音全般未実装',
			'バックグラウンドボイス未実装',
			'エンディング時の背景未実装',
			'クイックロード未実装',
			'オプション未実装',
			'バックログ未実装',
			'回想モード未実装'
		]
	}


def extract_resource_main(Kikiriki_copy_Path, input_dir, xp3_name, pre_converted_dir):
	from utils import extract_archive_garbro, subprocess_args # type: ignore

	xp3_path = Path(input_dir / '{}.xp3'.format(xp3_name))
	xp3_outdir = Path(pre_converted_dir / xp3_name)
	
	#展開
	sp.run([Kikiriki_copy_Path, '-i', xp3_path, '-o', xp3_outdir], **subprocess_args())

	#(tlgをGARbroに変換させるため)zipに圧縮
	if xp3_name in ['data', 'evecg', 'syscg']:
		shutil.make_archive(xp3_outdir, format='zip', root_dir=xp3_outdir)
		shutil.rmtree(xp3_outdir)

		#GARbro展開変換
		xp3_outzip = Path(pre_converted_dir / '{}.zip'.format(xp3_name))
		extract_archive_garbro(xp3_outzip, xp3_outdir, 'png')
		xp3_outzip.unlink()
		
	return


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from requiredfile_locations import location # type: ignore
	from utils import extract_archive_garbro # type: ignore

	input_dir = values['input_dir']
	num_workers = values_ex['num_workers']

	#通常時
	if Path(input_dir / 'data.xp3').is_file():

		#kikirikiパス取得
		Kikiriki_Path = location('Kikiriki')
		madCHook_Path = Path( Kikiriki_Path.parent / 'madCHook.dll')
		tpm_Path = Path(input_dir / 'xp3dec.tpm')

		#展開ツール環境用一時ディレクトリ作成
		with tempfile.TemporaryDirectory() as temp_dir:
			temp_dir = Path(temp_dir)

			#コピー先パス
			Kikiriki_copy_Path = Path(temp_dir / 'kikiriki.exe')
			madCHook_copy_Path = Path(temp_dir / 'madCHook.dll')
			tpm_copy_Path = Path(temp_dir / 'xp3dec.tpm')

			#全部コピー
			shutil.copy(Kikiriki_Path, Kikiriki_copy_Path)
			shutil.copy(madCHook_Path, madCHook_copy_Path)
			shutil.copy(tpm_Path, tpm_copy_Path)

			#kikiriki全展開
			with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
				futures = []
				for xp3_name in ['bgm', 'cv', 'data', 'evecg', 'se', 'syscg']:
					if not Path(input_dir / '{}.xp3'.format(xp3_name)).is_file(): raise FileNotFoundError('{}.xp3が見つかりません'.format(str(xp3_name)))#チェック
					futures.append(executor.submit(extract_resource_main, Kikiriki_copy_Path, input_dir, xp3_name, pre_converted_dir))
				
				concurrent.futures.as_completed(futures)
	
	#xp3ないやつ(soboku用)
	else:
		datain_dir = Path(input_dir / 'data')
		dataout_dir = Path(pre_converted_dir / 'data')
		dataout_zip = Path(pre_converted_dir / 'data.zip')

		shutil.copytree(datain_dir, dataout_dir)
		shutil.make_archive(dataout_dir, format='zip', root_dir=dataout_dir)
		shutil.rmtree(dataout_dir)
		extract_archive_garbro(dataout_zip, dataout_dir, 'png')

		shutil.move( Path(dataout_dir / 'bgm'), pre_converted_dir)
		shutil.move( Path(dataout_dir / 'cv'), pre_converted_dir)
		shutil.move( Path(dataout_dir / 'se'), pre_converted_dir)
		shutil.move( Path(dataout_dir / 'evecg'), pre_converted_dir)
		shutil.move( Path(dataout_dir / 'syscg'), pre_converted_dir)

		dataout_zip.unlink()


	return


def default_txt():
	return ''';$V2000G200S1280,720L10000
*define

caption "<<-TITLE->> for ONScripter"
nsa

globalon
rubyon
transmode alpha
;<<-RMENU->>
effectcut
humanz 10
windowback
savenumber 10

defsub bgmstopfadeout
defsub sestopfadeout
defsub bg					;erasetextwindow用bg命令乗っ取り
defsub lsp_btn

;エフェクト定義 - 1
effect 11,10,500
effect 12,10,1500
effect 13,18,1500,"data\\rule\\rule28.png"
;<<-EFFECT->>

;<ONS_RESOLUTION_CHECK_DISABLED>
game
;----------------------------------------
*bg
erasetextwindow 1
getparam $90,%90

if $90=="white" _bg white,%90
if $90=="black" _bg black,%90

if $90!="white" if $90!="black" _bg $90,%90

return

;***名前表示***
*tp
erasetextwindow 0
if %11==0 mov %4,1
if %11==1 if $1!="" if $2=="" mov %4,1
if %11==1 if $1=="" if $2!="" mov %4,0

if %199==0 if %4==1 setwindow3 240,590,31,4,24,24,0,3,20,0,0,"syscg\\textwindow.png",0,0
if %199==0 if %4==0 setwindow3 240,265,31,4,24,24,0,3,20,0,0,#999999,40,40,1239,679

if %199==1 if %4==1 setwindow3 240/2,590/2,31,4,14,14,0,3,20,0,0,"syscg\\textwindow.png",0,0
if %199==1 if %4==0 setwindow3 240/2,265/2,31,4,14,14,0,3,20,0,0,#999999,0,0,1269,719

if %199==0 if $1!="" lsp 5,":s/24,24,0;#ffffff"+$1,240     ,565
if %199==1 if $1!="" lsp 5,":s/14,14,0;#ffffff"+$1,240/%190,565/%190+%191
if $1=="" csp 5
$0\\
mov $2,$1	;$2に$1を代入
mov $1,""	;$1を空に
return


;選択肢表示
*select_mode
erasetextwindow 1
vsp 11,0
mov %3,0:bclear
spbtn 28,8:spbtn 29,9
*sel_loop
skipoff
btnwait %3
if %3!=8 if %3!=9 vsp 11,1:goto *sel_loop
csp 28:csp 29
return


;***BGM再生、停止時のフェードイン/フェードアウト用*** - ttps://chappy.exblog.jp/5872275/
*bgmstopfadeout
getparam %0
bgmfadeout %0
stop
bgmfadeout 0
return


;***SE再生、停止時のフェードイン/フェードアウト用***
*sestopfadeout
getparam %0
for %2=100 to 0
	sevol %2
	wait %0/100
next
dwavestop 0
return


;***選択肢ボタン用lsp***
*lsp_btn
getparam %0,$0,%1,%2

lsp %0,$0,%1/%190,%2/%190+%191
return
;----------------------------------------
*start

;解像度が本来のものに一致しない場合PSP仕様へ
lsph 0,"syscg\\logo.png"0,0
getspsize 0,%0,%1
if %0==1280 mov %199,0:mov %190,1:mov %191,0
if %0!=1280 mov %199,1:mov %190,2:mov %191,3

;多分これで720pは誤魔化せる
;	普通の場合xy	:/%190
;	下辺合わせy		:/%190+%191

texton
saveon
bgmvol 30

;<<-MODE_SETTING->>

mov $2,"ダミーテキスト"
setcursor 0,":a/16,66,2;data\\system\\LineBreak_a.png",0,0
if %10==0 setcursor 1,":a/16,66,2;data\\system\\PageBreak_a.png",0,0

if %10==1 abssetcursor 1,":a/16,66,2;data\\system\\PageBreak_a.png",970/%190,680/%190+%191

;----------------------------------------
csp 5:_bg "syscg\\medi1.png",11
wait 2000

csp 5:_bg white,11
wait 1000

csp 5:_bg "syscg\\medi2.png",12
wait 3000

csp 5:_bg white,11
wait 1000

csp 5:_bg "syscg\\medi3.png",12
wait 3000

csp 5:_bg white,11
wait 1000

csp 5:_bg "syscg\\logo.png",13

dwave 1,$10
wait 4000

csp 5:_bg white,11
wait 1000

csp 5:_bg "syscg\\caution.png",12
wait 3000

;----------------------------------------
*title
	if %12==0 _bg "syscg\\title_bg.png",11
	if %12!=0 _bg "syscg\\trial_bg.png",11

	bgm $12
	dwave 1,$11

	lsp 21,":a/3,0,3;syscg\\title_btn_start.png"          ,885/%190,273/%190+%191
	lsp 22,":a/3,0,3;syscg\\title_btn_qload.png"          ,885/%190,338/%190+%191
	if %12=0 lsp 23,":a/3,0,3;syscg\\title_btn_load.png"  ,885/%190,403/%190+%191
	lsp 24,":a/3,0,3;syscg\\title_btn_config.png"         ,885/%190,468/%190+%191
	if %12=0 lsp 25,":a/3,0,3;syscg\\title_btn_omake.png" ,885/%190,533/%190+%191
	lsp 26,":a/3,0,3;syscg\\title_btn_exit.png"           ,885/%190,598/%190+%191

	print 1

*title_loop
	bclear

	spbtn 21,1
	spbtn 23,3
	spbtn 26,6

	btnwait %1
	print 1

	if %1=1 csp 21:csp 22:csp 23:csp 24:csp 25:csp 26:bgmstopfadeout 500:goto *scr_ks
	if %1=3 systemcall load:goto *title_loop
	if %1=6 end
goto *title_loop


;----------ここまでdefault.txt----------
'''


#--------------------def--------------------
def get_titleid(add0txt_title):

	if add0txt_title[:3]=='おばあ': title_id = 188
	elif add0txt_title[:2]=='衰え': title_id = 218
	else: title_id = 0

	return title_id


def quodel(s):
	s=str(s).replace('"', '')
	return s


def list2dict(l):
	#半角スペースで命令文を分割し、
	#それらを更に"="で分割("="の先がない場合はTrue)
	#そうしてできた二次元配列を辞書に変換しreturn

	#例:stage=暗転 hideall msgoff trans=normal time=1000
	#  →{'stage': '暗転', 'hideall': True, 'msgoff': True, 'trans': 'normal', 'time': '1000'}
	l2 = []
	for d in l[0][1].split():
		l2 += [d.split('=')] if re.search('=', d) else [[d,True]]

	return dict(l2)


def effect_edit(t,f,effect_list):

	list_num=False
	for i, e in enumerate(effect_list,21):#一桁だとprint時番号が競合する可能性あり
		if (e[0] == t) and (e[1] == f):
			list_num = i

	if not list_num:
		effect_list.append([t,f])
		list_num = len(effect_list)+20

	return str(list_num),effect_list


def def_kakkoline(line, kakko_line, kakko_dict, sel_sparg, same_hierarchy, effect_list, sel_spnum):
	linedef = line

	if kakko_line[0][0] == 'jump':
		line='goto '+quodel(kakko_dict.get('target'))

	if kakko_line[0][0] == 'call':
		line='gosub *'+quodel(kakko_dict.get('storage')).replace('.ks', '_ks')

	elif kakko_line[0][0] == 'name':
		line='mov $1,'+kakko_dict.get('text')

	elif kakko_line[0][0] == 'wait':
		line='wait '+quodel(kakko_dict.get('time'))

	elif kakko_line[0][0] == 'bgm':
		line='bgm "bgm\\'+ quodel(kakko_dict.get('file')) +'.ogg"'

	elif kakko_line[0][0] == 'se':
		cv_path = os.path.join(same_hierarchy, 'cv', quodel(kakko_dict.get('file'))+'.ogg')
		se_path = os.path.join(same_hierarchy, 'se', quodel(kakko_dict.get('file'))+'.ogg')

		if os.path.isfile(cv_path):
			path_dir = 'cv'

		elif os.path.isfile(se_path):
			path_dir = 'se'
		
		else:
			path_dir = ''

		line='dwave 1,"'+path_dir+'\\'+quodel(kakko_dict.get('file'))+'.ogg"' if path_dir else ';dwave 1,"convert_error.ogg"'

	elif kakko_line[0][0] == 'voice':
		line='dwave 0,"cv\\'+quodel(kakko_dict.get('file'))+'.ogg"'

	elif kakko_line[0][0] == 'haikei':
		if kakko_dict.get('file') == '"black"' or kakko_dict.get('file') == '"white"':
			path_rel = f'"{quodel(kakko_dict.get('file'))}"'.lower()

		else:
			eve_path = os.path.join(same_hierarchy, 'evecg', quodel(kakko_dict.get('file'))+'.png')
			sys_path = os.path.join(same_hierarchy, 'syscg', quodel(kakko_dict.get('file'))+'.png')

			if os.path.isfile(eve_path):
				path_dir = 'evecg'

			elif os.path.isfile(sys_path):
				path_dir = 'syscg'
		
			path_rel = '"'+path_dir+'\\'+quodel(kakko_dict.get('file'))+'.png"'

		ef,effect_list = effect_edit(kakko_dict.get('time'), kakko_dict.get('fade'),effect_list)
		line = 'csp 5:bg '+path_rel+','+ef

	elif kakko_line[0][0] == 'char_c':
		line='lsp 11,"evecg\\'+quodel(kakko_dict.get('file'))+'.png",0,0'		

	elif kakko_line[0][0] == 'char_action':
		ef,effect_list = effect_edit(kakko_dict.get('time'), '"cross"',effect_list)#print命令はクロスフェードのため吉里吉里側"cross"命令に偽装
		line='print '+ef

	elif kakko_line[0][0] == 'crossfade':
		ef,effect_list = effect_edit(kakko_dict.get('time'), '"cross"',effect_list)#print命令はクロスフェードのため吉里吉里側"cross"命令に偽装
		line='print '+ef

	elif kakko_line[0][0] == 'stop_bgm':
		line='bgmstopfadeout '+(quodel(kakko_dict.get('fadeout')))

	elif kakko_line[0][0] == 'stop_se':
		line='sestopfadeout '+(quodel(kakko_dict.get('fadeout')))

	elif kakko_line[0][0] == 'exbutton':
		btn_x=(quodel(kakko_dict.get('x')))
		btn_y=(quodel(kakko_dict.get('y')))
		btn_file=(quodel(kakko_dict.get('file')))
		sel_sparg.append(re.findall(r'"ChJump\(\'\', \'\*([A-z0-9_]+)\'\)"', line)[0])
		line='lsp_btn '+str(sel_spnum)+',":a/3,0,3;syscg\\'+btn_file+'.png",'+btn_x+','+btn_y
		sel_spnum += 1

	#無変更時コメントアウト/変更時末尾に改行挿入
	line = r';' + line if linedef == line else line + '\n'
	return line, sel_sparg, effect_list, sel_spnum


#--------------------event--------------------
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	same_hierarchy = str(pre_converted_dir)#(os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	scenario_dir = os.path.join(same_hierarchy,'data','scenario')
	first_ks = os.path.join(same_hierarchy,'data','script','first.ks')
	#char_dir = os.path.join(same_hierarchy,'char')

	sel_spnum = 28
	sel_sparg = []
	effect_list = []

	add0txt_effect = 'エフェクト定義 - 2\n'

	with open(first_ks, encoding='utf-16', errors='ignore') as f:
		txt_f = f.read()
		add0txt_title = re.search(r'\[title name="(.+?)(　Ver.\...)?"\]', txt_f).group(1)

		# 218が名前を日付のままにしてるのでゴリ押し修正
		if add0txt_title == '2022/05/17 01':
			add0txt_title = b'\xe8\xa1\xb0\xe3\x81\x88\xe7\x9f\xa5\xe3\x82\x89\xe3\x81\x9a\xe3\x81\xae\xe6\xb7\xab\xe4\xb9\xb1\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xef\xbc\x81\xef\xbd\x9e\xe5\xad\xab\xe3\x81\xae\xe8\x82\x89\xe6\xa3\x92\xe3\x82\x82\xe3\x81\x84\xe3\x81\x9f\xe3\x81\xa0\xe3\x81\x8d\xe3\x81\xbe\xe3\x81\x99\xe2\x99\xaa\xef\xbd\x9e'.decode('utf-8')

	title_id = get_titleid(add0txt_title)
	if not title_id: Exception('非対応タイトルです')
	
	txt = default_txt()

	for ks_path in sorted(glob.glob(os.path.join(scenario_dir, '*'))):
		ks_name = os.path.splitext(os.path.basename(ks_path))[0]
		char_code = 'UTF-16'

		with open(ks_path, encoding=char_code, errors='ignore') as f:
			#ks名をそのままonsのgoto先のラベルとして使い回す
			txt += '\n\n*' + ks_name + '_ks\n'

			for line in f:

				#最初にやっとくこと
				kakko_line = re.findall(r'\[(jump|call|name|wait|bgm|se|voice|haikei|char_c|char_action|crossfade|stop_bgm|stop_se|exbutton) (.+?)\]',line)#括弧行定義
				line = re.sub(r'\[ruby text="(.+?)" align="."\]\[ch text="(.+?)"\]', r'(\2/\1)', line)#ルビ置換

				if re.search('^\n', line):#空行
					#line = ''
					pass#そのまま放置

				elif re.search(';', line):#元々のメモ
					line = line.replace(';', ';;;;;')#分かりやすく

				elif re.search(r'\[tp\]', line):
					line = 'gosub *tp\n'

				elif re.search(r'\[hide_char\]', line):
					line = 'csp 11\n'

				elif re.search(r'\[stop_se\]', line):
					line = 'dwavestop 0\n'

				elif re.search(r'\[return\]', line):
					line = 'return\n'

				elif re.search(r'\[begin_link\]', line):#選択肢はじめ
					sel_spnum = 28
					sel_sparg = []
					line = r';' + line#エラー防止の為コメントアウト

				elif re.search(r'\[end_link\]', line):#選択肢おわり
					line = 'gosub *select_mode\n'
					for i,a in enumerate(sel_sparg,8):#28のボタン番号→8
						line += 'if %3='+str(i)+' goto *'+a+'\n'

				elif re.search(r'\*[A-z0-9_]+\|', line):
					line = line.replace('|', '')

				elif not re.search('[A-z]', line):#半角英字が存在しない(≒表示する文字)
					line = 'mov $0,"' + line.replace('\n', '"\n')#行末に

				elif kakko_line:#[]で呼び出し
					kakko_dict = list2dict(kakko_line)
					line, sel_sparg, effect_list, sel_spnum = def_kakkoline(line, kakko_line, kakko_dict, sel_sparg, same_hierarchy, effect_list, sel_spnum)

				else:#どれにも当てはまらない、よく分からない場合
					line = r';' + line#エラー防止の為コメントアウト

				txt += line

	for i,e in enumerate(effect_list,21):#エフェクト定義用の配列を命令文に&置換

		if e[1] == '"cross"':
			add0txt_effect +='effect '+str(i)+',10,'+quodel(e[0])+'\n'

		else:
			add0txt_effect +='effect '+str(i)+',18,'+quodel(e[0])+',"data\\rule\\rule'+quodel(e[1])+'.png"\n'

	txt = txt.replace(r'<<-TITLE->>', add0txt_title)
	txt = txt.replace(r'<<-EFFECT->>', add0txt_effect)

	#作品個別処理 - ホントはこの辺も自動取得～変換したいが技術力不足...
	# $10 ブランドコール(.\data\script\mode_title.ksに記載)
	# $11 タイトルコール(.\data\script\mode_title.ksに記載)
	# $12 タイトルBGM(.\data\config\title_cfg.ksに記載)
	# %10 カーソルは固定位置か否か(abssetcursor利用)
	# %11 無名時ウィンドウ変更が掛かるか否か
	# %12 体験版かどうか

	nsc_num12 = int('体験版' in add0txt_title)

	match title_id:
		case 188:
			txt = txt.replace(r'goto *99_001', r'select "ＥＮＤ１へ",*99_001,"ＥＮＤ２へ",*test'+'\n*test')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall00.ogg'
			nsc_str11 = r'cv\titlecall00.ogg'
			nsc_str12 = r'bgm\bgm25.ogg'
			nsc_num10 = 0
			nsc_num11 = 1

			end_pic = 6800 #PSP変換時調子悪いので+100
			end_snd = 85

		case 218:
			nsc_str10 = r'cv\brandcall00.ogg'
			nsc_str11 = r'cv\titlecall00.ogg'
			nsc_str12 = r'bgm\bgm11.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6700 #PSP変換時調子悪いので+100
			end_snd = 136

	if txt:
		#設定反映
		txt = txt.replace('\n*Gamebad', '\n*Gamebad\ngoto *title')#終了後タイトルに戻る
		txt = txt.replace(r';<<-MODE_SETTING->>', r'mov %10,'+str(nsc_num10)+r':mov %11,'+str(nsc_num11)+r':mov %12,'+str(nsc_num12)+r':mov $10,"'+nsc_str10+r'":mov $11,"'+nsc_str11+r'":mov $12,"'+nsc_str12+r'"')

		if not nsc_num12:#製品版
			#エンディング - フレームレートはスペック次第
			txt = txt.replace(r'bgm "bgm\bgmed01.ogg"',
					 f'''
saveoff:csp 5
lsp 1,"syscg\\staff.png",0,600/%190
dwave 2,"bgm\\bgmed01.ogg"
print 1
resettimer
*end_loop
gettimer %0
if %0>{end_snd}*1000 mov %0,{end_snd}*1000
amsp 1,0,0-(({end_pic}*%0/({end_snd}*1000))/%190)
print 1
if %0=={end_snd}*1000 goto *end_loop_end
goto *end_loop
*end_loop_end
dwavestop 2
click
saveon
csp 1:print 1
return
''')
			txt = txt.replace(r';<<-RMENU->>', r'rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset')
		else:#体験版
			txt = txt.replace(r';<<-RMENU->>', r'rmenu "スキップ",skip,"リセット",reset')

		open(os.path.join(same_hierarchy,'0.txt'), 'w', encoding='cp932', errors='ignore').write(txt)
	
	# 不要ファイル削除
	for suffix in ['.asd', '.ks', '.tjs']:
		for junk in Path(pre_converted_dir).glob('**/*'+suffix): junk.unlink()
	
	return


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()