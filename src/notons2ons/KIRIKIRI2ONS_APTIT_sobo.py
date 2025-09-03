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
		'date': 20170310,
		'title': '祖母シリーズ汎用 (2017〜2020)',
		'cli_arg': 'aptit_sobo',
		'requiredsoft': ['Kikiriki'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'exe_name': ['soboku', 'bokusobo', 'mituana', 'gisobo', 'Anokoro', 'tsumanosobo', 'chouzyukuoyakodon', 'GreatGrandmother', 'mgnkykntrk', 'magokatsujukujo'],

		'version': [
			#字面終わってるので申し訳程度のutf-8エンコード
			str(b'\xe7\xa5\x96\xe6\xaf\x8d\xe3\x81\xa8\xe5\x83\x95\xef\xbd\x9e\xe3\x81\x8a\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x80\x81\xe3\x81\xaa\xe3\x81\xab\xe3\x81\x8b\xe3\x81\xa7\xe3\x81\xa1\xe3\x82\x83\xe3\x81\x86\xe3\x82\x88\xe3\x81\x89\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0127)'.decode('utf-8')),
			str(b'\xe3\x83\x9c\xe3\x82\xaf\xe3\x81\xae\xe7\xa5\x96\xe6\xaf\x8d\xef\xbd\x9e\xe3\x81\x8a\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x80\x81\xe6\xbf\xa1\xe3\x82\x8c\xe3\x81\xa6\xe3\x82\x8b\xe3\x82\x88\xef\xbc\x9f\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0141)'.decode('utf-8')),
			str(b'\xe7\xa5\x96\xe6\xaf\x8d\xe3\x81\xae\xe5\xaf\x86\xe7\xa9\xb4\xef\xbd\x9e\xe6\x84\x9b\xe3\x81\x99\xe3\x82\x8b\xe5\xad\xab\xe3\x81\xab\xe6\x80\xa7\xe3\x81\xae\xe6\x89\x8b\xe3\x81\xbb\xe3\x81\xa9\xe3\x81\x8d\xe3\x82\x92\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0167)'.decode('utf-8')),
			str(b'\xe7\xbe\xa9\xe7\xa5\x96\xe6\xaf\x8d\xe3\x80\x81\xe8\xaa\xbf\xe6\x95\x99\xe4\xb8\xad\xe3\x80\x82\xef\xbd\x9e\xe4\xbb\xb2\xe8\x89\xaf\xe3\x81\x97\xe3\x81\xae\xe7\xa7\x98\xe8\xa8\xa3\xe3\x81\xaf\xef\xbc\xb3\xef\xbc\xad\xe3\x81\xa7\xe3\x81\x99\xe3\x80\x82\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0172)'.decode('utf-8')),
			str(b'\xe3\x81\x82\xe3\x81\xae\xe9\xa0\x83\xe3\x80\x81\xe7\xa5\x96\xe6\xaf\x8d\xe3\x81\xaf\xe3\x82\xa8\xe3\x83\xad\xe3\x81\x8b\xe3\x81\xa3\xe3\x81\x9f\xef\xbd\x9e\xe6\x98\x94\xe3\x81\xab\xe6\x88\xbb\xe3\x81\xa3\xe3\x81\xa6\xe3\x80\x81\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x81\xab\xe3\x82\xa8\xe3\x83\x83\xe3\x83\x81\xe3\x81\xaa\xe3\x81\x8a\xe8\xbf\x94\xe3\x81\x97\xe3\x82\x92\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0186)'.decode('utf-8')),
			str(b'\xe5\xa6\xbb\xe3\x81\xae\xe7\xa5\x96\xe6\xaf\x8d\xe3\x81\xaf\xe3\x80\x81\xe3\x81\xbe\xe3\x81\xa0\xe3\x81\xbe\xe3\x81\xa0\xe7\x8f\xbe\xe5\xbd\xb9\xe8\xb6\x85\xe7\xbe\x8e\xe7\x86\x9f\xe5\xa5\xb3\xef\xbd\x9e\xe5\xad\xab\xe5\xa9\xbf\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x80\x81\xe5\xaf\x82\xe3\x81\x97\xe3\x81\x84\xe6\x99\x82\xe3\x81\xab\xe3\x81\xaf\xe3\x81\x84\xe3\x81\xa4\xe3\x81\xa7\xe3\x82\x82\xe3\x81\x84\xe3\x82\x89\xe3\x81\xa3\xe3\x81\x97\xe3\x82\x83\xe3\x81\x84\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0239)'.decode('utf-8')),
			str(b'\xe3\x81\xb0\xe3\x81\x81\xe3\x81\xb0\xe3\x81\xa8\xe3\x83\x9e\xe3\x83\x9e\xe3\x81\xa8\xe3\x81\xae\xe8\xb6\x85\xe7\x86\x9f\xe6\xaf\x8d\xe5\xa8\x98\xe4\xb8\xbc\xef\xbd\x9e\xef\xbc\x93\xe4\xb8\x96\xe4\xbb\xa3\xe3\x81\xa7\xe3\x81\xae\xe5\xae\xb6\xe5\xba\xad\xe5\x86\x85\xe3\x82\xa8\xe3\x83\x83\xe3\x83\x81\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0273)'.decode('utf-8')),
			str(b'\xe6\x9b\xbe\xe7\xa5\x96\xe6\xaf\x8d\xe3\x81\xae\xe3\x81\xb2\xe5\xad\xab\xe7\xad\x86\xe3\x81\x8a\xe3\x82\x8d\xe3\x81\x97\xef\xbd\x9e\xe3\x81\xb2\xe3\x81\x83\xe3\x81\xb0\xe3\x81\x82\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x80\x81\xe3\x82\x82\xe3\x81\xa3\xe3\x81\xa8\xe3\x81\x97\xe3\x81\x9f\xe3\x81\x84\xe3\x82\x88\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0308)'.decode('utf-8')),
			str(b'\xe5\xad\xab\xe3\x81\xae\xe5\xb7\xa8\xe6\xa0\xb9\xe3\x81\xae\xe8\x99\x9c\xe3\x81\xab\xe3\x81\xaa\xe3\x82\x8a\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f\xef\xbd\x9e\xe5\xae\xb6\xe6\x97\x8f\xe6\x97\x85\xe8\xa1\x8c\xe3\x81\xa7\xe3\x80\x81\xe3\x81\x8a\xe5\xa9\x86\xe3\x81\xa1\xe3\x82\x83\xe3\x82\x93\xe3\x81\x8c\xe7\xad\x86\xe3\x81\x8a\xe3\x82\x8d\xe3\x81\x97\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0377)'.decode('utf-8')),
			str(b'\xe3\x81\xbe\xe3\x81\x94\xe3\x81\x8b\xe3\x81\xa4\xef\xbd\x9e\xe5\x8f\xaf\xe6\x84\x9b\xe3\x81\x84\xe5\xad\xab\xe3\x81\xae\xe3\x81\x9f\xe3\x82\x81\xe3\x81\xaa\xe3\x82\x89\xe4\xb8\xad\xe5\x87\xba\xe3\x81\x97\xef\xbc\xaf\xef\xbc\xab\xe2\x80\xa6\xef\xbd\x9e FANZA DL\xe7\x89\x88(aman_0448)'.decode('utf-8')),
		],

		'notes': [
			'好感度調整未実装(好感度分岐部分では全て選択肢が出ます)',
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
	return ''';mode800
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
savenumber 18

defsub bgmstopfadeout
defsub sestopfadeout
defsub bg					;erasetextwindow用bg命令乗っ取り

;エフェクト定義 - 1
effect 11,10,500
effect 12,10,1500
effect 13,18,1500,"data\\rule\\rule28.png"
;<<-EFFECT->>


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

if %4==1 setwindow3 40,470,28,4,24,24,0,3,20,0,0,"syscg\\textwindow.png",0,390
if %4==0 setwindow3 80,230,27,4,24,24,0,3,20,0,0,#999999,0,0,799,599

if $1!="" lsp 5,":s/24,24,0;#ffffff"+$1,40,420
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


;----------------------------------------
*start
texton
saveon
bgmvol 30

;<<-MODE_SETTING->>

mov $2,"ダミーテキスト"
setcursor 0,":a/16,66,2;data\\system\\LineBreak_a.png",0,0
if %10==0 setcursor 1,":a/16,66,2;data\\system\\PageBreak_a.png",0,0
if %10==1 abssetcursor 1,":a/16,66,2;data\\system\\PageBreak_a.png",750,560

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

csp 5:_bg "syscg\\logo00.png",12
csp 5:_bg "syscg\\logo01.png",13

dwave 1,$10
wait 4000

csp 5:_bg white,11
wait 1000

csp 5:_bg "syscg\\caution001.png",12
wait 1000

csp 5:_bg "syscg\\caution002.png",12
wait 1000

csp 5:_bg "syscg\\caution003.png",12
wait 3000

;----------------------------------------
*title
	if %12==0 _bg "syscg\\title_bg.png",11
	if %12!=0 _bg "syscg\\trial_bg.png",11

	bgm $12
	dwave 1,$11

	lsp 21,":a/3,0,3;syscg\\title_btn_start.png" ,66 ,513
	lsp 22,":a/3,0,3;syscg\\title_btn_qload.png" ,170,513
	if %12=0 lsp 23,":a/3,0,3;syscg\\title_btn_load.png"  ,336,513
	lsp 24,":a/3,0,3;syscg\\title_btn_config.png",446,513
	if %12=0 lsp 25,":a/3,0,3;syscg\\title_btn_omake.png",576,513
	lsp 26,":a/3,0,3;syscg\\title_btn_exit.png" ,700,513

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

	if add0txt_title[:3]=='祖母と': title_id = 85
	elif add0txt_title[:3]=='ボクの': title_id = 95
	elif add0txt_title[:3]=='祖母の': title_id = 1102
	elif add0txt_title[:3]=='義祖母': title_id = 104
	elif add0txt_title[:4]=='あの頃、': title_id = 108
	elif add0txt_title[:3]=='妻の祖': title_id = 121
	elif add0txt_title[:2]=='ばぁ': title_id = 130
	elif add0txt_title[0]=='曾': title_id = 138
	elif add0txt_title[:2]=='孫の': title_id = 155
	elif add0txt_title[:2]=='まご': title_id = 173
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
		line='lsp '+str(sel_spnum)+',":a/3,0,3;syscg\\'+btn_file+'.png",'+btn_x+','+btn_y
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

	title_id = get_titleid(add0txt_title)
	if not title_id: Exception('非対応タイトルです')
	
	txt = default_txt()

	if title_id==85: utf16list = ['_first']
	else: utf16list = ['scr', '_first']

	for ks_path in glob.glob(os.path.join(scenario_dir, '*')):
		ks_name = os.path.splitext(os.path.basename(ks_path))[0]
		char_code = 'UTF-16' if (ks_name in utf16list) else 'SHIFT_JIS'

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
		case 85:
			txt = txt.replace(r'goto *40_021', r'select "ＥＮＤ１へ",*40_021,"ＥＮＤ２へ",*test'+'\n*test')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm26.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6600
			end_snd = 124

		case 95:
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm26.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6900
			end_snd = 136

		case 102:
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm26.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6800
			end_snd = 119

		case 104:
			txt = txt.replace(r'goto *30_000', r'select "ＥＮＤ１へ",*20_000,"ＥＮＤ２へ",*test'+'\n*test')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm26.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6800
			end_snd = 137

		case 108:
			txt = txt.replace(r';;;;;主人公：', 'mov %4,1\n;')
			txt = txt.replace(r'goto *20_000', r'select "ＥＮＤ１へ",*20_000,"ＥＮＤ２へ",*test'+'\n*test')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm01.ogg'
			nsc_num10 = 0
			nsc_num11 = 1

			end_pic = 6600
			end_snd = 103

		case 121:
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm01.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6600
			end_snd = 112

		case 130:
			txt = txt.replace(r'goto *07_000', r'select "ＥＮＤ１へ",*07_000,"ＥＮＤ２へ",*08_000,"ＥＮＤ３へ",*09_000,"ＥＮＤ４へ",*10_000')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall01.ogg'
			nsc_str11 = r'cv\titlecall01.ogg'
			nsc_str12 = r'bgm\bgm15.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6900
			end_snd = 116

		case 138:
			txt = txt.replace(r'goto *b05_000', r'select "ＧＯＯＤＥＮＤへ",*c05_000,"ＢＡＤＥＮＤへ",*b05_000')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall.ogg'
			nsc_str11 = r'cv\titlecall.ogg'
			nsc_str12 = r'bgm\bgm19.ogg'
			nsc_num10 = 0
			nsc_num11 = 1

			end_pic = 6600
			end_snd = 97

		case 155:
			txt = txt.replace(r'goto *c01_000', r'select "ＧＯＯＤＥＮＤへ",*c01_000,"ＢＡＤＥＮＤへ",*test'+'\n*test')#選択分岐処理実装面倒だったので
			nsc_str10 = r'cv\brandcall00.ogg'
			nsc_str11 = r'cv\titlecall00.ogg'
			nsc_str12 = r'bgm\bgm20.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6700
			end_snd = 84

		case 173:
			nsc_str10 = r'cv\brandcall00.ogg'
			nsc_str11 = r'cv\titlecall00.ogg'
			nsc_str12 = r'bgm\bgm20.ogg'
			nsc_num10 = 1
			nsc_num11 = 0

			end_pic = 6700
			end_snd = 106

	if txt:
		#設定反映
		txt = txt.replace('\n*Gamebad', '\n*Gamebad\ngoto *title')#終了後タイトルに戻る
		txt = txt.replace(r';<<-MODE_SETTING->>', r'mov %10,'+str(nsc_num10)+r':mov %11,'+str(nsc_num11)+r':mov %12,'+str(nsc_num12)+r':mov $10,"'+nsc_str10+r'":mov $11,"'+nsc_str11+r'":mov $12,"'+nsc_str12+r'"')

		if not nsc_num12:#製品版
			#エンディング - フレームレートはスペック次第
			txt = txt.replace(r'bgm "bgm\bgmed01.ogg"',
					 f'''
saveoff:csp 5
lsp 1,"syscg\\staff.png",0,600
dwave 2,"bgm\\bgmed01.ogg"
print 1
resettimer
*end_loop
gettimer %0
if %0>{end_snd}*1000 mov %0,{end_snd}*1000
amsp 1,0,0-({end_pic}*%0/({end_snd}*1000))
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
	
	#不要ファイル削除
	for suffix in ['.asd', '.ks', '.tjs']:
		for junk in Path(pre_converted_dir).glob('**/*'+suffix): junk.unlink()
	
	return


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()