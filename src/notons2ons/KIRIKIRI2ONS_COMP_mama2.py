#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import glob, os, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'コンプリーツ',
		'date': 20170721,
		'title': 'ママとの甘い性活II',
		'cli_arg': 'comp_mama2',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'program_name': ['Complets'],#一覧取得用
		'exe_name': ['MS2'],
		
		'version': [
			'ママとの甘い性活II FANZA DL版(cveaa_0038)',
		],

		'notes': [
			'オプション/CGモード未実装',
			'タイトル画面大幅簡略化',
			'ゲーム内選択肢も簡略化',
			'立ち絵は一切動きません',
			'画面下ボタン全て未実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xp3_name in ['bgm','core','data','grp','se','voice']:
			p = Path(input_dir / Path(xp3_name + '.xp3'))
			e = Path(pre_converted_dir / xp3_name)

			#なければ強制エラー
			if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))

			futures.append(executor.submit(extract_archive_garbro, p, e))
		
		concurrent.futures.as_completed(futures)

	return


#--------------------def--------------------
def default_txt():
	s = ''';$V2000G200S1280,720L10000
*define

caption "ママとの甘い性活II for ONScripter"
pretextgosub *name_text

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset
transmode alpha
globalon
rubyon
saveon
nsa
windowback
humanz 10
defsub bg			;erasetextwindow用bg命令乗っ取り

;---------- NSC2ONS4PSP強制変換機能ここから ----------
; 以下の文字列を認識すると、解像度に関わらず
; ONScripter_Multi_Converterの変換が可能になります
; PSP変換時でも座標ズレが発生しないようにしてください
; 
; <ONS_RESOLUTION_CHECK_DISABLED>
; 
;---------- NSC2ONS4PSP強制変換機能ここまで ----------

effect 2,10,100
effect 3,10,1000
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

;----------------------------------------
;***名前表示ウィンドウ - システムカスタマイズ***
*name_text
erasetextwindow 0

gettag $0,$1 ;[]の値（名前）を取得

if %199!=1 lsp 5,":s/28,28,0;#ffffff"+$0,50,470 ;名前の表示：文字幅28,高さ28,字間0
if %199==1 lsp 5,":s/15,15,0;#ffffff"+$0,50*480/960,470*480/960+3 ;名前の表示：文字幅30,高さ30,字間0
print 0
return
;----------------------------------------
*staff
	;エンディング(笑)
	bgm "bgm/BGM110.ogg"
	csp -1:vsp 12,0:print 2:bg "grp/parts/StaffRollBg1.png",3
	click
	_bg black,3
	bgmstop
	reset
;----------------------------------------
*start

;解像度が本来のものに一致しない場合PSP仕様へ
lsph 0,"grp/parts/logo.png"0,0
getspsize 0,%0,%1
if %0==1280 mov %199,0
if %0!=1280 mov %199,1

dwave 0,"voice/system/sys1a.ogg"
_bg "grp/parts/logo.png",3
click

_bg black,3
_bg "grp/parts/notice.png",3
click

*title

_bg black,3

dwave 0,"voice/system/sys1g.ogg"
bgm "bgm/BGM01.ogg"
_bg "grp/parts/TitleBg.png",3
lsp 24,"grp/parts/TitleSEL.png",0,0:print 2
click

if %199==1 lsph 9,"grp/parts/MesWinNML.png",0*480/960,410*480/960+3:print 0
if %199==1 lsph 11,"grp/parts/MesWinBg.png",0*480/960,410*480/960+3:print 0
if %199==1 setwindow 80*480/960,500*480/960+3,33,4,15,15,2,2,20,0,1,"grp/parts/MesWinScreen.png",0*480/960,410*480/960+3

if %199!=1 lsph 9,"grp/parts/MesWinNML.png",0,410:print 0
if %199!=1 lsph 11,"grp/parts/MesWinBg.png",0,410:print 0
if %199!=1 setwindow 80,500,33,4,30,30,2,2,20,0,1,"grp/parts/MesWinScreen.png",0,410

select
	"Ｎｅｗ　Ｇａｍｅ　　　はじめから",*startmode,
	"Ｌｏａｄ　Ｇａｍｅ　　　続きから",*loadmode,
	"Ｅｎｄ　Ｇａｍｅ　　　ゲーム終了",*endmode

goto *title
;----------------------------------------

*endmode
	csp 24:print 0
	_bg black,3
	end

*loadmode
	csp 24:print 0
	systemcall load
	bgmstop
	goto *title

*startmode
	vsp 9,1:vsp 11,1
	csp 24:print 0
	saveon
	bgmstop
	goto *Block1_1

;----------------------------------------
'''
	return s



def effect_edit(t,f,effect_list,effect_startnum):

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num),effect_list,effect_startnum

def str2var(s,i,str2var_dict,str2var_num):
	d=str2var_dict.get(s)

	if d:
		s2=d
	else:
		str2var_dict[s]=str2var_num[i]
		s2=str2var_num[i]
		str2var_num[i]+=1
	
	return s2,str2var_dict,str2var_num


def stand_name(aaa):
	aaa = aaa.replace('うっとり','uttori')
	aaa = aaa.replace('エプロン','apron')
	aaa = aaa.replace('ネグリジェ','negligee')
	aaa = aaa.replace('下着','shitagi')
	aaa = aaa.replace('不機嫌','hukigen')
	aaa = aaa.replace('喜び','yorokobi')
	aaa = aaa.replace('困る','komaru')
	aaa = aaa.replace('嬉しい','uresii')
	aaa = aaa.replace('小夜','sayo')
	aaa = aaa.replace('怒り','ikari')
	aaa = aaa.replace('悩む','nayamu')
	aaa = aaa.replace('悲しい','kanasii')
	aaa = aaa.replace('普通','hutsuu')
	aaa = aaa.replace('私服','shihuku')
	aaa = aaa.replace('服','huku')
	aaa = aaa.replace('裸','hadaka')
	aaa = aaa.replace('輝','hikaru')
	aaa = aaa.replace('近','chikai')
	aaa = aaa.replace('遠','tooi')
	aaa = aaa.replace('香織','kaori')

	return aaa

def gebg_name(bbb):
	bbb = bbb.replace('リビング','living')
	bbb = bbb.replace('主人公部屋','shuzinkou_room')
	bbb = bbb.replace('催眠教室','saimin')
	bbb = bbb.replace('夕','yuu')
	bbb = bbb.replace('夜','yoru')
	bbb = bbb.replace('寝室','shinsitsu')
	bbb = bbb.replace('昼','hiru')
	bbb = bbb.replace('空','sora')
	bbb = bbb.replace('自宅外観','zitaku')
	bbb = bbb.replace('風呂','huro')
	bbb = bbb.replace('本屋','honya')

	return bbb

def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	same_hierarchy = str(pre_converted_dir)
	#same_hierarchy = os.path.join(same_hierarchy,'ext')#debug

	scenario_dir = os.path.join(same_hierarchy,'data','snr')
	se_dir = os.path.join(same_hierarchy,'se')

	stand_dir = os.path.join(same_hierarchy,'grp','stand')
	#other_dir = os.path.join(same_hierarchy,'grp','other')
	#parts_dir = os.path.join(same_hierarchy,'grp','parts')
	gebg_dir = os.path.join(same_hierarchy,'grp','gebg')
	#evcg_dir = os.path.join(same_hierarchy,'grp','evcg')

	effect_startnum=10
	effect_list=[]

	str2var_dict={}
	str2var_num=[50, 50, 1000]

	sel_dict={}

	#--------------------ファイル整理--------------------

	#音源リネーム
	for p in  glob.glob(os.path.join(se_dir, '*')) :
		p_num,str2var_dict,str2var_num = str2var((os.path.splitext(os.path.basename(p))[0]).lower(),1,str2var_dict,str2var_num)
		p2 = os.path.join(os.path.dirname(p), str(p_num)+os.path.splitext(p)[1])

		os.rename(p, p2)

	for p in  glob.glob(os.path.join(gebg_dir, '*')) :
		p_ren = gebg_name((os.path.splitext(os.path.basename(p))[0]).lower())
		p2 = os.path.join(os.path.dirname(p), str(p_ren)+os.path.splitext(p)[1])

		os.rename(p, p2)

	for p in  glob.glob(os.path.join(stand_dir, '*')) :
		p_ren = stand_name((os.path.splitext(os.path.basename(p))[0]).lower())
		p2 = os.path.join(os.path.dirname(p), str(p_ren)+os.path.splitext(p)[1])

		os.rename(p, p2)

	#--------------------0.txt作成--------------------
	txt = default_txt()

	pathlist = sorted(glob.glob(os.path.join(scenario_dir, 'general', '*.snr')))
	pathlist.extend(glob.glob(os.path.join(scenario_dir, '*.snr')))

	for snr_path in pathlist:

		with open(snr_path, encoding='SHIFT_JIS', errors='ignore') as f:
			#memo
			txt += '\n;--------------- '+ os.path.splitext(os.path.basename(snr_path))[0] +' ---------------\nend\n\n'
			txt = txt.replace('//', ';;;')

			for line in f:
				#最初にやっとくこと
				Block_line = re.match(r'\[(.+?)\]',line)
				jump_line = re.match(r'シナリオジャンプ\("([\-A-z0-9]+?)"\)',line)
				trans_line = re.match(r'トランジション\(([0-9]+?)\)',line)
				chrmsg_line = re.match(r'【(.+?)】(\((.+?)\))?(.+?)\n',line)
				BGM_line = re.match(r'音楽再生\("([\-A-z0-9]+?)"\)',line)
				set_line = re.match(r'(f\.[A-z]{2}[0-9]+) ?= ?"(.+)?";', line)
				sel_line = re.match(r'選択肢実行\(([0-9]+), ([0-9]+)\)', line)
				selset_line = re.match(r'選択肢登録\(([0-9]+), "(.+?)", "(.+?)"\)', line)
				tati_line = re.match(r'前景\(f\.(.+?), f\.(.+?)\+"(.+?)"\)', line)
				haikei_line = re.match(r'背景\("(.+?)"\)', line)
				seplay_line = re.match(r'(LOOP)?効果音再生\(([0-9]), "(.+?)"\)', line)

				if re.search('^\n', line):#空行
					#line = ''#行削除
					pass#そのまま放置

				elif re.match(r'\*', line):#nsc側でラベルと勘違いするの対策
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'　', line):
					line = line.replace('\n','') + '\\\n'

				elif re.match(r'リターン', line):
					line = 'return\n'

				elif re.match(r'ファンクションコール\(".+?キャラOUT"\)', line):
					line = 'vsp 12,0:print 2\n'

				elif selset_line:
					s,str2var_dict,str2var_num = str2var(selset_line[2].lower(),2,str2var_dict,str2var_num)
					sel_dict[selset_line[1]]= [selset_line[3],'*STR_'+str(s)]
					line = ';処理済\t;;'+line

				elif sel_line:
					sel = 'select '
					sd1 = sel_dict[ sel_line[1] ]
					sd2 = sel_dict[ sel_line[2] ]
					sel += '"'+sd1[0]+'",'+sd1[1]+',"'+sd2[0]+'",'+sd2[1]+'"\n'
					line = sel

				elif set_line:
					if re.match(r'CC0[0-9]', (set_line[1][2:]) ) and set_line[2]:
						s,str2var_dict,str2var_num = str2var(set_line[1][2:].lower(),0,str2var_dict,str2var_num)
						line='mov $'+str(s)+',"'+stand_name(set_line[2])+'"\n'

				elif tati_line:
					s,str2var_dict,str2var_num = str2var(tati_line[2].lower(),0,str2var_dict,str2var_num)
					line='lsp 12,"grp\\stand\\"+$'+str(s)+'+"'+stand_name(tati_line[3])+'.png",0,0:print 2\n'

				elif seplay_line:
					s,str2var_dict,str2var_num = str2var(seplay_line[3].lower(),1,str2var_dict,str2var_num)
					line = ('dwave '+seplay_line[2]+',"se\\'+str(s)+'.ogg"\n')

				elif Block_line:
					if re.match(r'\[([\-A-z0-9]+?)\]',line):
						line = '*'+str(Block_line[1]).replace('-','_') + '\n'
					else:
						s,str2var_dict,str2var_num = str2var(Block_line[1].lower(),2,str2var_dict,str2var_num)
						line = '*STR_'+str(s) + '\t;;'+Block_line[1]+'\n'


				elif jump_line:
					line = 'goto *'+str(jump_line[1]).replace('-','_') + '\n'

				elif trans_line:
					e,effect_list,effect_startnum = effect_edit(trans_line[1], 'fade',effect_list,effect_startnum)
					line = 'print '+ e + '\n'

				elif chrmsg_line:
					line = r'['+chrmsg_line[1]+r']'+chrmsg_line[4] + '\\\n'

					if (chrmsg_line[3]):
						line ='dwave 10,"voice\\'+chrmsg_line[3]+'.ogg"\n'+line

				elif haikei_line:#memo:その後のprint不要
					if haikei_line[1] =='BLACK':
						line='vsp 12,0:print 2:bg "black",3\n'
					elif re.match(r'EV',haikei_line[1]):
						line='vsp 12,0:print 2:bg "grp\\evcg\\'+haikei_line[1]+'.png",3\n'
					else:
						line='vsp 12,0:print 2:bg "grp\\gebg\\'+gebg_name(haikei_line[1])+'.png",3\n'

				elif BGM_line:
					line = 'bgm "bgm\\'+str(BGM_line[1])+ '.ogg"\n'


				else:#どれにも当てはまらない、よく分からない場合
					line = r';' + line#エラー防止の為コメントアウト
					#print(line)


				txt += line

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換

		if e[1] == 'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

		#else:#今作フェードしか無いからこっち使わないんだよね
			#add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"rule\\'+e[1]+'.png"\n'

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	open(os.path.join(same_hierarchy,'0.txt'), 'w', encoding='cp932', errors='ignore').write(txt)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()