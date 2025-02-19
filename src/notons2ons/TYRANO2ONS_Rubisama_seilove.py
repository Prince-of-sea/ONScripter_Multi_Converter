#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
from asarPy import extract_asar
import concurrent.futures
import subprocess, tempfile, chardet, shutil, glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'るび様を崇める会',
		'date': 20220715,
		'title': 'ご主人様、セイラに夢みたいないちゃラブご奉仕させていただけますか',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'ご主人様、セイラに夢みたいないちゃラブご奉仕させていただけますか DLsite DL版(RJ399143 - 2022/08/09)',
		],

		'notes': [
			'ゲーム進行時のUIはすべて未実装\nセーブ等は右クリックで行う仕様',
			'ゲーム終了時の操作が少々特殊\n(環境設定→終了する)',
			'タイトル画面のCGがランダムではなく固定',
			'キャラ移動/一部エフェクト/可変文字未実装',
			'コンフィグ/CG/回想未実装',
			'エンディング未実装',
			'その他細かいバグ有り(?)',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	input_dir = values['input_dir']

	p = Path(input_dir / Path('resources') / Path('app.asar'))

	#なければ強制エラー
	if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))
	
	with tempfile.TemporaryDirectory() as td:
		e = Path(td / Path('dst'))
		extract_asar(p, e)
		shutil.move(Path(e / Path('data')), pre_converted_dir)

	return


def default_txt():
	s = ''';$V2000G200S1280,720L10000
*define

caption "ご主人様、セイラに夢みたいないちゃラブご奉仕させていただけますか for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset
savenumber 11
transmode alpha
globalon
rubyon
nsa
humanz 10
windowback

;---------- NSC2ONS4PSP強制変換機能ここから ----------
; 以下の文字列を認識すると、解像度に関わらず
; ONScripter_Multi_Converterの変換が可能になります
; PSP変換時でも座標ズレが発生しないようにしてください
; 
; <ONS_RESOLUTION_CHECK_DISABLED>
; 
;---------- NSC2ONS4PSP強制変換機能ここまで ----------

pretextgosub *pretext_lb
defsub swind
defsub stopfadeout

effect 10,10,500

;<<-EFFECT->>

game
;----------------------------------------
*pretext_lb
	
	;ボイス周り
	if $11=="？？？"   itoa $170,%170:dwave 0,"data/sound/noname_1/SeiraVoice("+$170+").ogg":inc %170
	if $11=="seira"    itoa $170,%171:dwave 0,"data/sound/seira_1/SeiraVoice("+$170+").ogg" :inc %171
	if $11=="seira_m"  itoa $170,%172:dwave 0,"data/sound/seira_2/SeiraVoice("+$170+").ogg" :inc %172
	if $11=="mv"       itoa $170,%173:dwave 0,"data/sound/seira_1/SeiraVoice("+$170+").ogg" :inc %173
	
	if $11=="seira" mov $11,"セイラ"
	if $11=="seira_m" mov $11,"セイラ"
	if $11=="mv" mov $11,"セイラ"
	
	print 1
	if %199!=1 lsp 10,":s/26,26,0;#ffffff"+$11,150/%190  ,530/%190+%191	;名前の表示
	if %199==1 lsp 10,":s/14,14,0;#ffffff"+$11,150/%190-2,530/%190+%191	;名前の表示
return

*swind
	getparam %0
	if %199!=1 setwindow 140/%190,580/%190+%191,37,3,26,26,2,4,20,0,1,"data/image/frame_black.png",0,500/%190+%191
	if %199==1 setwindow 140/%190,580/%190+%191,37,3,14,14,0,1,20,0,1,"data/image/frame_black.png",0,500/%190+%191
return

*stopfadeout
	getparam %5
	bgmfadeout %5
	stop
	bgmfadeout 0
return
;----------------------------------------
;数字変数
;	
;文字変数
;	$11		名前
;	
;	
;スプライト番号
;	
;----------------------------------------
*start
mov %170,1		;noname_1 - ？？？
mov %171,1		;seira_1 - seira
mov %172,1		;seira_2 - seira_m
mov %173,1089	;seira_1 - mv

;解像度が本来のものに一致しない場合PSP仕様へ
lsph 0,"data/bgimage_/title_1.png"0,0
getspsize 0,%0,%1
if %0==1280 mov %199,0
if %0!=1280 mov %199,1

if %199==1 mov %190,2:mov %191,3
if %199!=1 mov %190,1:mov %191,0

;多分これで720pは誤魔化せる
;	普通の場合xy	:/%190
;	下辺合わせy		:/%190+%191

bgmvol 50		;BGM音量
voicevol 100	;ボイス音量
defsevol 30		;効果音音量
;mov %334,1		;クリア判定
;
;#			名前
;[l][r]		@
;[p]		\\

swind 26
;----------------------------------------
*title_menu
saveon

;<<-TITLE_BGM->>

bgm "data/bgm_/"+$66
bg "data/bgimage_/title_1.png",10
dwave 0,"data/sound/noname_1/SeiraVoice(4).ogg"

lsp 30, "data/image/title/button_start_hover.png"  ,788/%190,237/%190+%191
lsp 31, "data/image/title/button_load_hover.png"   ,798/%190,327/%190+%191
lsp 32, "data/image/title/button_cg_hover.png"     ,808/%190,417/%190+%191
lsp 33, "data/image/title/button_replay_hover.png" ,818/%190,507/%190+%191
lsp 34, "data/image/title/button_config_hover.png" ,828/%190,597/%190+%191
lsph 35,"data/image/title/button_start.png"        ,788/%190,237/%190+%191
lsph 36,"data/image/title/button_load.png"         ,798/%190,327/%190+%191
lsph 37,"data/image/title/button_cg.png"           ,808/%190,417/%190+%191
lsph 38,"data/image/title/button_replay.png"       ,818/%190,507/%190+%191
lsph 39,"data/image/title/button_config.png"       ,828/%190,597/%190+%191

lsp 40,"data/bgimage_/logo.png",630/%190,20/%190+%191

print 1
*title_loop
	bclear
	btrans
	
	exbtn_d     "C30C31C32C33C34P35P36P37P38P39"
	exbtn 30,30,"P30C31C32C33C34C35P36P37P38P39"
	exbtn 31,31,"C30P31C32C33C34P35C36P37P38P39"
	exbtn 32,32,"C30C31P32C33C34P35P36C37P38P39"
	exbtn 33,33,"C30C31C32P33C34P35P36P37C38P39"
	exbtn 34,34,"C30C31C32C33P34P35P36P37P38C39"
	
	print 1
	btnwait %20
	
	if %20==30 csp -1:stop:goto *scr_start
	if %20==31 csp -1:stop:bg black,10:systemcall load:bg black,10:goto *title_menu
	if %20==34 csp -1:stop:bg black,10:select "続ける",*tuduki,"終了する",*owari
	
goto *title_loop

*tuduki
reset
*owari
end
;----------------------------------------
'''
	return s
#--------------------def--------------------
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
		['⁉',r'！？'], [',',r''],
	]

	for v in cnvl: txt = txt.replace(v[0], v[1])
	return txt


def krcmd2krdict(c):
	kr_dict = {}

	for p in re.findall(r'([A-z0-9-_]+?)=("(.*?)"|([^\t\s]+))', c):
		kr_dict[p[0]] = p[2] if p[2] else p[3]

	return kr_dict


def effect_edit(t,f, effect_startnum, effect_list):
	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num), effect_startnum, effect_list


def str2var(s2v_d, s2v_n, s,i):
	d=s2v_d.get(s)

	if d:
		sv=d
	else:
		s2v_d[s]=s2v_n[i]
		sv=s2v_n[i]
		s2v_n[i]+=1
	
	return s2v_d, s2v_n, str(sv)



def tati_create(same_hierarchy, fgimage_dir, storage, width, height, left, top):
	name = ('taticnv/' + storage + '_' + width + '_' + height + '_' + left + '_' + top + '.png')
	namepath = os.path.join(same_hierarchy,name)
	if not os.path.exists(namepath):
		os.makedirs(os.path.dirname(namepath), exist_ok=True)#フォルダなかったら作る

		im = Image.open(os.path.join(fgimage_dir,storage))
		im_r = im.resize((int(width), int(height)))

		im_new = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
		im_new.paste(im_r, (int(640-(int(width)/2)+int(left)), int(top)))
		im_new.save(namepath)

	return name


def music_cnv_main(f):
		fogg = (f + ".ogg")
		try:
			subprocess.run(['ffmpeg', '-y', '-vn',
				'-i', f,
				#'-ab', '56k',
				'-ar', '44100',
				'-ac', '2',	fogg,
			], shell=True)
		except:
			pass
		else:
			os.remove(f)
			os.rename(fogg, f)


def music_cnv(sound_dir):
	pathlist = (glob.glob(os.path.join(sound_dir, '*.*')))
	pathlist += (glob.glob(os.path.join(sound_dir, 'noname_1', '*.*')))
	pathlist += (glob.glob(os.path.join(sound_dir, 'seira_1', '*.*')))
	pathlist += (glob.glob(os.path.join(sound_dir, 'seira_2', '*.*')))

	with concurrent.futures.ThreadPoolExecutor() as executor:#マルチスレッドで高速化
		futures = []
		for f in pathlist:
			futures.append(executor.submit(music_cnv_main, f))
		
		concurrent.futures.as_completed(futures)


def bgm_cnv_main(f, s2v_d, s2v_n, same_hierarchy, values):
	fn = os.path.basename(f).lower()
	s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, fn, 2)
	fwav = os.path.join(same_hierarchy, 'data', 'bgm_', str(sv) + ".wav")
	s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, fn, 2)
	fogg = os.path.join(same_hierarchy, 'data', 'bgm_', str(sv) + ".ogg")
	os.makedirs(os.path.dirname(fwav), exist_ok=True)#フォルダなかったら作る

	if values:
		from requiredfile_locations import location_env # type: ignore
		from utils import subprocess_args # type: ignore
		
		ffmpeg_Path = location_env('ffmpeg')

		try: subprocess.run([ffmpeg_Path, '-y', '-i', f, fwav, ], shell=True, **subprocess_args())
		except: pass
		try: subprocess.run([ffmpeg_Path, '-y', '-i', fwav, '-ar', '44100', '-ac', '2',	 fogg], shell=True, **subprocess_args())
		except: pass

	else:
		try: subprocess.run(['ffmpeg', '-y', '-i', f, fwav], shell=True)
		except: pass
		try: subprocess.run(['ffmpeg', '-y', '-i', fwav, '-ar', '44100', '-ac', '2', fogg], shell=True)
		except: pass

	os.remove(fwav)


def bgm_cnv(same_hierarchy, s2v_d, s2v_n, bgm_dir, values, values_ex):#一旦wavにしないと動かないのど う し て
	pathlist = (glob.glob(os.path.join(bgm_dir, '*.*')))
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:#マルチスレッドで高速化
		futures = []
		for f in pathlist:
			futures.append(executor.submit(bgm_cnv_main, f, s2v_d, s2v_n, same_hierarchy, bool(values)))
		
		concurrent.futures.as_completed(futures)
	return s2v_d, s2v_n
		


#--------------------0.txt作成--------------------
def text_cnv(s2v_d, s2v_n, same_hierarchy, bgimage_dir, fgimage_dir):
	effect_startnum=10
	effect_list=[]

	tati_now = {}
	txt = default_txt()

	pathlist = glob.glob(os.path.join(same_hierarchy,'data','scenario', 'scene_all_v110.ks'))#listにする意味(めんどくさくてコピペしてきた)

	for snr_path in pathlist:
		
		with open(snr_path, 'rb') as f:
			char_code = chardet.detect(f.read())['encoding']

		with open(snr_path, encoding=char_code, errors='ignore') as f:
			#memo
			txt += '\n;--------------- '+ os.path.splitext(os.path.basename(snr_path))[0] +' ---------------\nend\n\n'
			txt = txt.replace('//', ';;;')

			for line in f:
				#最初にやっとくこと
				name_line = re.search(r'#(.*?)\n', line)
				mes_lr_line = re.search(r'(.*?)\[l\]\[r\]\n', line)
				mes_p_line = re.search(r'(.*?)\[p\]\n', line)
				kakko_line = re.search(r'\[(.+?)\]\n', line)

				if re.match('\n', line):#改行は無視
					pass

				elif re.match(r';', line):#元々コメントアウトのやつ目立たせる
					line = r';;;;' + line

				elif name_line:#名前
					line = r'mov $11,"' + name_line[1] + '"\n'

				elif mes_lr_line:#文章＠
					line = message_replace(mes_lr_line[1]) + '@\n'

				elif mes_p_line:#文章￥
					line = message_replace(mes_p_line[1]) + '\\\n'

				elif kakko_line:#[]内
					d = krcmd2krdict('kr_cmd=' + kakko_line[1])
					kr_cmd = d['kr_cmd']

					if kr_cmd == 'bg':
						d_method_ = d.get('method') if d.get('method') else 'crossfade'
						d_time_ = d.get('time') if d.get('time') else '500'
						if d['storage']=='真っ黒.png':
							s, effect_startnum, effect_list = effect_edit(d_time_, d_method_, effect_startnum, effect_list)
							line = 'vsp 10,0:bg black,' + s + '\n'
						else:
							s, effect_startnum, effect_list = effect_edit(d_time_, d_method_, effect_startnum, effect_list)
							line = 'vsp 10,0:bg "data\\bgimage_\\' + d['storage'] + '",' + s + '\n'

					elif kr_cmd == 'cg':
						s, effect_startnum, effect_list = effect_edit('500', 'crossfade', effect_startnum, effect_list)
						line = 'vsp 10,0:bg "data\\bgimage_\\' + d['storage'] + '",' + s + '\n'

					elif kr_cmd == 'chara_new':
						
						if not tati_now.get(d['name']):
							tati_now[d['name']] = {}

						tati_now[d['name']]['storage'] = d['storage']
						tati_now[d['name']]['width'] = d['width']
						tati_now[d['name']]['height'] = d['height']
						tati_now[d['name']]['left'] = d['left']
						tati_now[d['name']]['top'] = d['top']

						s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
						line = 'lsph ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d['storage'], d['width'], d['height'], d['left'], d['top']) + '",0,0\n'

					elif kr_cmd == 'chara_move':
						d2 = {}
						for a in ['storage', 'width', 'height', 'left', 'top']:
							if d.get(a):					
								tati_now[d['name']][a] = d[a]
								d2[a] = d[a]
							else:
								d2[a] = tati_now[d['name']][a]

						s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
						line = 'lsph ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d2['storage'], d2['width'], d2['height'], d2['left'], d2['top']) + '",0,0\n'

					elif kr_cmd == 'chara_show':
						d2 = {}
						for a in ['storage', 'width', 'height', 'left', 'top']:
							if d.get(a):					
								tati_now[d['name']][a] = d[a]
								d2[a] = d[a]
							else:
								d2[a] = tati_now[d['name']][a]
						
						time = d.get('time') if d.get('time') else False
						if time:
							s, effect_startnum, effect_list = effect_edit(time, 'crossfade', effect_startnum, effect_list)
							s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
							line = 'lsp ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d2['storage'], d2['width'], d2['height'], d2['left'], d2['top']) + '",0,0:print ' + s + '\n'
						else:
							s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
							line = 'lsph ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d2['storage'], d2['width'], d2['height'], d2['left'], d2['top']) + '",0,0:print 1\n'

					elif kr_cmd == 'chara_mod':
						d2 = {}
						for a in ['storage', 'width', 'height', 'left', 'top']:
							if d.get(a):					
								tati_now[d['name']][a] = d[a]
								d2[a] = d[a]
							else:
								d2[a] = tati_now[d['name']][a]
						
						time = d.get('time') if d.get('time') else False
						if time:
							s, effect_startnum, effect_list = effect_edit(time, 'crossfade', effect_startnum, effect_list)
							s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
							line = 'lsp ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d2['storage'], d2['width'], d2['height'], d2['left'], d2['top']) + '",0,0:print ' + s + '\n'
						else:
							s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
							line = 'lsph ' + str(sv) + ',"' + tati_create(same_hierarchy, fgimage_dir, d2['storage'], d2['width'], d2['height'], d2['left'], d2['top']) + '",0,0:print 1\n'

					elif kr_cmd == 'chara_hide':
						time = d.get('time') if d.get('time') else '10'
						s, effect_startnum, effect_list = effect_edit(time, 'crossfade', effect_startnum, effect_list)
						s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, d['name'], 1)
						line = 'vsp ' + str(sv) + ',0' + s + '\n'

					elif kr_cmd == 'playse':
						line = 'dwave 0,"data/sound/' + d['storage'] + '"\n'

					elif kr_cmd == 'playbgm':
						s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, str(d['storage']).lower(), 2)
						line = 'bgm "data/bgm_/' + str(sv) + '.ogg"\n'

					elif kr_cmd == 'stopbgm':
						line = 'stop\n'

					elif kr_cmd == 'fadeoutbgm':
						line = 'stopfadeout\n'

					elif kr_cmd == 'stopse':
						line = 'dwavestop\n'


					else:
						line = r';' + line#エラー防止の為コメントアウト
						#print(d)


				else:#どれにも当てはまらない、よく分からない場合
					line = r';' + line#エラー防止の為コメントアウト
					#print(line[:-1])


				txt += line

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換
		add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	s2v_d, s2v_n, sv = str2var(s2v_d, s2v_n, 'ふさわしきメイドであるために（タイトル画面Ver.）.mp3'.lower(), 2)
	fusa = str(sv)
	txt = txt.replace(r';<<-TITLE_BGM->>', r'mov $66,"'+fusa+r'.ogg"')

	txt = txt.replace(r';*gameend', r'mov %334,1:reset')
	txt = txt.replace(r'ゲーム本編', '\n*scr_start\n')

	#ガバガバ修正
	txt = txt.replace(r'lsp 20,"taticnv/chara/seira/裸_腕広げ_すまし.png_1416_2000_0_-10.png",0,0:print 14', '')
	txt = txt.replace(r'lsph 23,"taticnv/chara/seira/mainvisual.jpg_1280_1810_0_-400.png",0,0', r'lsp 23,"taticnv/chara/seira/mainvisual.jpg_1280_1810_0_-400.png",0,0:print 15')

	open(os.path.join(same_hierarchy,'0.txt'), 'w', encoding='cp932', errors='ignore').write(txt)


	#画像加工(別にdef取れよって感じだけど)
	for img_path in glob.glob(os.path.join(bgimage_dir, '*.*')):
		os.makedirs(os.path.dirname(img_path.replace('bgimage', 'bgimage_')), exist_ok=True)#フォルダなかったら作る
		if not os.path.basename(img_path).lower()=='logo.png':
			img = Image.open(img_path)
			width, height = img.size

			width_r = 1280
			height_r = height*width_r/width

			img_resize = img.resize((int(width_r), int(height_r)), Image.Resampling.LANCZOS)
			img_resize.save(img_path.replace('bgimage', 'bgimage_'), quality=95)

		else:
			shutil.copyfile(img_path, img_path.replace('bgimage', 'bgimage_'))

	return s2v_d, s2v_n


def junk_del(same_hierarchy, bgimage_dir, bgm_dir):
	shutil.rmtree(os.path.join(bgimage_dir))
	shutil.rmtree(bgm_dir)
	shutil.rmtree(os.path.join(same_hierarchy,'data','scenario'))
	shutil.rmtree(os.path.join(same_hierarchy,'data','system'))
	shutil.rmtree(os.path.join(same_hierarchy,'data','video'))



def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):
	
	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	same_hierarchy = str(pre_converted_dir)#(os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入

	bgimage_dir = os.path.join(same_hierarchy,'data','bgimage')
	fgimage_dir = os.path.join(same_hierarchy,'data','fgimage')
	bgm_dir = os.path.join(same_hierarchy,'data','bgm')
	sound_dir = os.path.join(same_hierarchy,'data','sound')

	s2v_d={}
	s2v_n=[20, 20, 1000]#名前sp,

	s2v_d, s2v_n = text_cnv(s2v_d, s2v_n, same_hierarchy, bgimage_dir, fgimage_dir)
	s2v_d, s2v_n = bgm_cnv(same_hierarchy, s2v_d, s2v_n, bgm_dir, values, values_ex)
	if not values: music_cnv(sound_dir)
	junk_del(same_hierarchy, bgimage_dir, bgm_dir)

	#不要ファイル削除
	for suffix in ['.html','.css', '.ks', '.js']:
		for junk in Path(pre_converted_dir).glob('**/*'+suffix): junk.unlink()


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()