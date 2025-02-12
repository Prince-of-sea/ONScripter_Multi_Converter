from pathlib import Path
import math, re

from utils import openread0x84bitxor


def onsscript_decode(values: dict):
	input_dir = Path(values['input_dir'])

	#優先順位は00.txt > 0.txt > nscript.dat
	ztxt_path = Path(input_dir / '0.txt')
	zztxt_path = Path(input_dir / '00.txt')
	nsdat_path = Path(input_dir / 'nscript.dat')

	text = ''

	if zztxt_path.exists():
		for i in range(0, 100):
			zzrange_path = Path(input_dir / (str(i).zfill(2) + '.txt'))
			if zzrange_path.exists():				
				with open(zzrange_path, 'r', errors='ignore') as zzrangetext:
					text += zzrangetext.read()
					text += '\n\n;##\n;{} end\n;##\n\n'.format(str(zzrange_path.name))
	
	elif ztxt_path.exists():
		for i in range(0, 10):
			zrange_path = Path(input_dir / (str(i) + '.txt'))
			if zrange_path.exists():				
				with open(zrange_path, 'r', errors='ignore') as zrangetext:
					text += zrangetext.read()
					text += '\n\n;##\n;{} end\n;##\n\n'.format(str(zrange_path.name))

	elif nsdat_path.exists():
		text += openread0x84bitxor(nsdat_path)
	
	else:
		raise FileNotFoundError('00.txt/0.txt/nscript.datが見つかりません')

	return text


def onsscript_check_resolution(values: dict, values_ex: dict, ztxtscript: str, override_resolution: list):
	hardware = values['hardware']
	aspect_43only = values_ex['aspect_4:3only']

	#解像度表記抽出
	oldnsc_mode = (r';mode(320|400|800)')#ONS解像度旧表記
	newnsc_mode = (r'(\r|\n|\t|\s)*?;\$[Vv][0-9]{1,}[Gg]([0-9]{1,})[Ss]([0-9]{1,}),([0-9]{1,})[Ll][0-9]{1,}')#ONS解像度新表記
	oldnsc_search = re.search(oldnsc_mode, ztxtscript)
	newnsc_search = re.search(newnsc_mode, ztxtscript)

	#解像度表記を元に解像度を取得して変数に格納
	if oldnsc_search:
		script_resolution = (int(oldnsc_search.group(1)), int(int(oldnsc_search.group(1)) / 4 * 3))
	
	elif newnsc_search:
		script_resolution = (int(newnsc_search.group(3)), int(newnsc_search.group(4)))
	
	else:
		script_resolution = (640, 480)

	#PSPは解像度新表記が読めないので、強制的に旧表記に変換(ついでに非対応解像度時エラー)
	if (hardware == 'PSP') and (newnsc_search):
		script_w = script_resolution[0]
		script_h = script_resolution[1]

		#スクリプト横解像度が800や640に近いときに代替横解像度作成
		if   (script_w != 800) and (script_w > 790) and (script_w < 810): alternative_w = 800
		elif (script_w != 640) and (script_w > 630) and (script_w < 650): alternative_w = 640
		else: alternative_w = False

		#代替横解像度作成時
		if alternative_w:

			#代替縦 = 代替横 / 入力横 * 入力縦
			alternative_h = round(alternative_w / script_w * script_h)

			#出力縦 = 270固定(272だと左右若干見切れるor微妙に縦長くなるのでNG)
			output_h = 270

			#出力横 = 出力縦 * 代替横 / 代替縦
			output_w = round(output_h * alternative_w  / alternative_h)

			#出力横を2の倍数(切り捨て)に
			output_w = int(math.floor(output_w / 2) * 2)

			#出力横が480超えない(=画面比率が16:9より横長かったりしない)なら
			if (output_w <= 480):
				override_resolution = (output_w, output_h)

	if (aspect_43only) and (newnsc_search):
		#チェック&変換
		if (hardware == 'PSP') and (override_resolution):
			if   (alternative_w == 800): ztxtscript = re.sub(newnsc_mode, r';mode800,value\2', ztxtscript, 1)#ほぼ800変換時
			elif (alternative_w == 640): ztxtscript = re.sub(newnsc_mode, r';value\2', ztxtscript, 1)#ほぼ640変換時
			else: ztxtscript = re.sub(newnsc_mode, r';value\2', ztxtscript, 1)#解像度無視時

		elif (script_resolution[0] in [320, 400, 640, 800]) and (script_resolution[1] == script_resolution[0] / 4 * 3):
			if (script_resolution[0] == 640): ztxtscript = re.sub(newnsc_mode, r';value\2', ztxtscript, 1)#640x480
			else: ztxtscript = re.sub(newnsc_mode, r';mode\3,value\2', ztxtscript, 1)#通常時
		
		else: raise ValueError('非対応解像度のため、このソフトは変換できません')
	
	return script_resolution, override_resolution, ztxtscript


def onsscript_check_image(ztxtscript: str):
	#画像表示命令抽出
	imgdict = {
		#カーソル類は最初から書いとく
		Path(r'cursor0.bmp'):{'trans': 'l', 'part': '3'},
		Path(r'cursor1.bmp'):{'trans': 'l', 'part': '3'},
		Path(r'doncur.bmp'):{'trans': 'l', 'part': '1'},
		Path(r'doffcur.bmp'):{'trans': 'l', 'part': '1'},
		Path(r'uoncur.bmp'):{'trans': 'l', 'part': '1'},
		Path(r'uoffcur.bmp'):{'trans': 'l', 'part': '1'},	
	}
	
	#[0]が命令文/[3]が(パスの入っている)変数名/[5]が透過形式/[6]が分割数/[8]が相対パス - [3]か[8]はどちらかのみ代入される
	immode_dict_tup  = re.findall(r'(ld)[\t\s]+([lcr])[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")[\t\s]*,[\t\s]*[0-9]+', ztxtscript)#ld
	immode_dict_tup += re.findall(r'((abs)?setcursor)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', ztxtscript)#setcursor系
	immode_dict_tup += re.findall(r'(lsp(h)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', ztxtscript)#lsp系
	immode_dict_tup += re.findall(r'(lsph?2(add|sub)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")(([\t\s]*,[\t\s]*((-?[0-9]{1,3})|(%.+?))){1,6})?', ztxtscript)#lsp2系

	#変数に画像表示命令用の文字列突っ込んである場合があるのでそれ抽出
	#[0]が命令文/[1]が変数名/[3]が透過形式/[4]が分割数/[6]が相対パス
	immode_var_tup = re.findall(r'(stralias|mov)[\t\s]*(\$?[A-Za-z0-9_]+?)[\t\s]*,[\t\s]*"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)"', ztxtscript)#パスの入ったmov及びstralias

	#[0]が相対パス
	immode_dict2_tup = re.findall(r'bg[\t\s]+"(.+?)"[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9]+)', ztxtscript)#背景

	# ここにsetwindow画像パス抽出正規表現セット - 未実装
	#[2]がx、[5]がy、[9]が透過方式、[10]が相対パス
	setwindow_re_tup = re.findall(r'setwindow3?\s+(\s*(([0-9]+)|%[A-z0-9$]+)\s*,)(\s*(([0-9]+)|%[A-z0-9$]+)\s*,)(\s*([0-9]+|%[A-z0-9$]+)\s*,){9}\s*"(:([alrc]);)?(.+?)"\s*,', ztxtscript)
	
	for l in immode_dict_tup:
		#抽出したタプルからパスを取得
		if ( bool(l[8]) and (not r'$' in l[8]) ): p = l[8]
		elif ( bool(l[3]) and (not r'$' in l[3]) ): p = l[3]
		else: p = ''

		if p:		
			imgdict[Path(p)] = {}#とりあえず辞書作成		
			if (l[5]): imgdict[Path(p)]['trans'] = l[5]#透過モード
			if (l[6]): imgdict[Path(p)]['part'] = l[6]#表示時画像分割数
			
	for l in immode_var_tup:
		#抽出したタプルからパスを取得
		if ( bool(l[6]) and (not r'$' in l[6]) ): p = l[6]
		else: p = ''

		if p:
			imgdict[Path(p)] = {}#とりあえず辞書作成		
			if (l[3]): imgdict[Path(p)]['trans'] = l[3]#透過モード
			if (l[4]): imgdict[Path(p)]['part'] = l[4]#表示時画像分割数
	
	for l in immode_dict2_tup:
		#抽出したタプルからパスを取得
		if l[0]: p = l[0]
		else: p = ''

		if p:
			imgdict[Path(p)] = {}#とりあえず辞書作成		
			imgdict[Path(p)]['trans'] = 'c'#透過モード
			imgdict[Path(p)]['part'] = '1'#表示時画像分割数

	for l in setwindow_re_tup:
		#抽出したタプルからパスを取得
		p = l[10] if bool(l[10]) else ''

		if p:
			winx = l[2] if bool(l[2]) else 0
			winy = l[5] if bool(l[5]) else 0

			imgdict[Path(p)] = {}#とりあえず辞書作成
			if (l[9]): imgdict[Path(p)]['trans'] = l[9]#透過モード
			imgdict[Path(p)]['setwinpos'] = (winx, winy)

	return imgdict


def onsscript_check_bgm(ztxtscript: str):
	#bgm再生命令抽出
	bgmlist = []
	for a in re.findall(r'(bgm|mp3loop)[\t\s]+"(.+?)"', ztxtscript): bgmlist.append(Path(a[1]))#txt内の音源の相対パスを格納
	return set(bgmlist)


def onsscript_check_vid(ztxtscript: str):
	#動画再生命令抽出
	vidlist = []
	for a in re.findall(r'(mpegplay|avi)[\t\s]+"(.+?)"', ztxtscript): vidlist.append(Path(a[1]))#txt内の動画の相対パスを格納
	return set(vidlist)


def onsscript_check_txtmodify_adddefsub(ztxtscript: str, pre_txt: str, aft_txt: str):

	#game命令追加
	if re.search(r'[\n\t\s]*game[\t\s]*(;(.*?))?[\t\s]*\n', ztxtscript):
		ztxtscript = re.sub(r'[\n\t\s]*game[\t\s]*(;(.*?))?[\t\s]*\n',
					  '\n{p}\ngame\n{a}\n'.format(p = pre_txt, a = aft_txt), ztxtscript, 1)
	
	else:
		raise ValueError('game命令追加エラー')
	
	return ztxtscript


def onsscript_check_txtmodify(values: dict, values_ex: dict, ztxtscript: str, override_resolution: list):
	hardware = values['hardware']

	#アルファベット小文字変換
	alphabet_upper = ''.join([chr(i) for i in range(65, 91)])#AからZ
	alphabet_lower = ''.join([chr(i) for i in range(97, 123)])#aからz
	ztxtscript = ztxtscript.translate(str.maketrans(alphabet_upper, alphabet_lower))#大文字→小文字変換

	#ns2/ns3命令は全部nsaへ
	ztxtscript = re.sub(r'\n[\t\s]*ns[2|3][\t\s]*\n', r'\nnsa\n', ztxtscript)

	#numalias命令を追加
	numalias_list = [4080, 4081, 4082, 4083, 4084, 4085, 4086, 4087, 4088, 4089]#ここ将来的にはGUIで設定できるようにしたい
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias0,{l0}'.format(l0 = numalias_list[0]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias1,{l1}'.format(l1 = numalias_list[1]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias2,{l2}'.format(l2 = numalias_list[2]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias3,{l3}'.format(l3 = numalias_list[3]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias4,{l4}'.format(l4 = numalias_list[4]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias5,{l5}'.format(l5 = numalias_list[5]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias6,{l6}'.format(l6 = numalias_list[6]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias7,{l7}'.format(l7 = numalias_list[7]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias8,{l8}'.format(l8 = numalias_list[8]), '')
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'numalias multiconverteralias9,{l9}'.format(l9 = numalias_list[9]), '')
	
	#nbz変換設定
	match values['etc_0txtnbz_radio']:
		case '0.txtを".nbz"->".wav"で一括置換': ztxtscript = ztxtscript.replace('.nbz', '.wav')
		case '変換後のファイルを拡張子nbzとwavで両方用意しておく': pass
		case _: raise ValueError('「nbz変換設定」未選択エラー')
	
	#avi命令→mpegplay命令変換
	adddefsubavi = False
	match (values['etc_0txtavitompegplay']):
		#利用する(関数上書き)
		case '利用する(関数上書き)':
			ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub avi', '*avi\ngetparam $multiconverteralias0,%multiconverteralias0:mpegplay $multiconverteralias0,%multiconverteralias0:return')#avi命令をmpegplay命令に変換
			adddefsubavi = True

		#利用する(正規表現置換)
		case '利用する(正規表現置換)':
			ztxtscript = re.sub(r'([\n|\t| |:])avi[\t\s]+"(.+?)",[\t\s]*([0|1]|%[0-9]+)', r'\1mpegplay "\2",\3', ztxtscript)

		#利用しない
		case '利用しない': pass

		#未選択エラー
		case _: raise ValueError('「avi/mpegplay命令変換」未選択エラー')

	#動画連番画像利用時強制avi命令→mpegplay命令変換
	if (values['vid_movfmt_radio'] == '連番画像') and (not adddefsubavi):
		ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub avi', '*avi\ngetparam $multiconverteralias0,%multiconverteralias0:mpegplay $multiconverteralias0,%multiconverteralias0:return')#avi命令をmpegplay命令に変換
			
	#savescreenshot命令無効化
	match values['etc_0txtnoscreenshot']:
		#利用する(関数上書き)
		case '利用する(関数上書き)':
			ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub savescreenshot', '*savescreenshot\nreturn')#savescreenshot命令を無効化
			ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub savescreenshot2', '*savescreenshot2\nreturn')#savescreenshot2命令を無効化

		#利用する(正規表現置換)
		case '利用する(正規表現置換)':
			ztxtscript = re.sub(r'savescreenshot2?[\t\s]+"(.+?)"[\t\s]*([:|\n])', r'wait 0\2', ztxtscript)
	
		#利用しない
		case '利用しない': pass

		#未選択エラー
		case _: raise ValueError('「screenshot命令無効化」未選択エラー')
	
	#最大回想ページ数設定
	if values['etc_0txtmaxkaisoupage_chk']:
		mk = str(int(values['etc_0txtmaxkaisoupage_num']))
		ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'maxkaisoupage {mk}'.format(mk = mk), '')#本当はdefsub追加用の関数だが流用
	
	#setwindowのフォントサイズ変更(PSP解像度無視変換時は無効)
	if values['etc_0txtsetwindowbigfont_chk'] and (not override_resolution):

		#倍率計算
		fontper = values_ex['output_resolution'][1] / values_ex['script_resolution'][1]

		#倍率が1未満の時のみ処理
		if fontper < 1:

			#txt内のsetwindow命令を格納 - [0]命令文前部分/[2]横文字数/[3]縦文字数/[4]横文字サイズ/[5]縦文字サイズ/[6]横文字間隔/[7]縦文字間隔/[8]命令文後部分
			setwindow_re_fnttup = re.findall(r'(setwindow3? ([0-9]{1,},){2})([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),(([0-9]{1,},){3}(.+?)(,[0-9]{1,}){2,4})', ztxtscript)
	
			for v in set(setwindow_re_fnttup):

				txtmin = math.ceil(10 / fontper)
				nummin = min(int(v[4]), int(v[5]))

				#表示時10pxを下回りそうな場合 - ちなみに10pxはMSゴシックで漢字が潰れない最低サイズ
				if txtmin > nummin:

					#文字の縦横サイズが違う可能性を考え別に処理 - もちろん縦横比維持
					v4rp = str( int( txtmin * ( int(v[4]) / nummin ) ) )#横文字サイズ(拡大)
					v5rp = str( int( txtmin * ( int(v[5]) / nummin ) ) )#縦文字サイズ(拡大)
					v6rp = str( int( int(v[6]) * ( nummin / int(v4rp) ) ) )#横文字間隔(縮小)
					v7rp = str( int( int(v[7]) * ( nummin / int(v5rp) ) ) )#縦文字間隔(縮小)

					#横に表示できる最大文字数を(文字を大きくした分)減らす - 見切れるのを防ぐため縦はそのまま
					#v2rp = str( int( int(v[2]) * ( int(v[4]) + int(v[6]) ) / ( int(v4rp) + int(v6rp) ) ) )

					sw = (v[0] + v[2] +','+ v[3] +','+ v[4] +','+ v[5] +','+ v[6] +','+ v[7] +','+ v[8])
					sw_re = (v[0] + v[2] +','+ v[3] +','+ v4rp +','+ v5rp +','+ v6rp +','+ v7rp +','+ v[8])
				
					ztxtscript = ztxtscript.replace(sw, sw_re)

	#okcancelboxをmovで強制ok
	if values['etc_0txtskipokcancelbox_chk']:
		ztxtscript = re.sub(r'([\n|\t| |:])okcancelbox[\t\s]+%([A-z0-9_]+?),', r'\1mov %\2,1 ;', ztxtscript)
	
	#yesnoboxをmovで強制yes
	if values['etc_0txtskipyesnobox_chk']:
		ztxtscript = re.sub(r'([\n|\t| |:])yesnobox[\t\s]+%([A-z0-9_]+?),', r'\1mov %\2,1 ;', ztxtscript)

	#rnd2を自作命令multiconverterrnd2def(連番)に変換
	if values['etc_0txtrndtornd2_chk']:
		for i,r in enumerate( re.findall(r'(([\n|\t| |:])rnd2[\t\s]+(%[A-z0-9_]+)[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9_]+)[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9_]+))', ztxtscript) ):
			ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub multiconverterrnd2def{i}'.format(i = i), '*multiconverterrnd2def{i}\nrnd {r2},{r4}+1-{r3}:add {r2},{r3}:return'.format(i = i, r2 = r[2], r3 = r[3], r4 = r[4]))
			ztxtscript = re.sub(r[0], '{r1}multiconverterrnd2def{i}'.format(r1=r[1], i = i), ztxtscript, 1)
	
	#連番画像利用時mpegplay命令
	if (values['vid_movfmt_radio'] == '連番画像'):
		#参考: https://web.archive.org/web/20110308215321fw_/http://blog.livedoor.jp/tormtorm/archives/51356258.html

		if hardware == 'PSVITA':
			bltx1 = math.ceil(540 / values_ex['output_resolution'][1] * values_ex['output_resolution'][0])
			blty1 = 544

		else:
			bltx1 = values_ex['script_resolution'][0]
			blty1 = values_ex['script_resolution'][1]
		
		bltx2 = math.ceil(bltx1 * values_ex['renbanresper'])
		blty2 = math.ceil(blty1 * values_ex['renbanresper'])

		ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub mpegplay', '''*mpegplay
saveoff
mov %multiconverteralias0,%0 :mov %multiconverteralias1,%1 :mov %multiconverteralias2,%2 :mov %multiconverteralias3,%3 :mov %multiconverteralias4,%4 
mov %multiconverteralias5,%5 :mov %multiconverteralias6,%6 :mov %multiconverteralias7,%7 :mov %multiconverteralias8,%8 :mov %multiconverteralias9,%9 
mov $multiconverteralias0,$10:mov $multiconverteralias1,$11:mov $multiconverteralias2,$12:mov $multiconverteralias3,$13:mov $multiconverteralias4,$14:mov $multiconverteralias5,$15
getparam $13,%9:fileexist %0,$13+"/00000.jpg"
if %0==1 mov $14,".jpg"
if %0!=1 mov $14,".png"
mov $11,$13:add $11,"/":mov %6,5:mov $15,""
for %4=7 to 1 step -1:itoa $10,%4:for %5=0 to 9
itoa $12,%5:fileexist %7,$11+"keta"+$10+"_"+$12
if %7==1 add $15,$12:break
next:next:atoi %2,$15:for %4=1 to %6:mov $%4,"":next
*count
dec %6:for %4=1 to %6:add $%4,"0":next
if %6!=1 goto *count
mov %0,5000
*movie_count1
itoa $12,%0:len %3,$12:fileexist %4,$11+$%3+$12+$14
if %4==1 add %0,5000:goto *movie_count1
mov %1,0
*movie_count2
mov %8,(%1+%0)/2:itoa $12,%8:len %3,$12:fileexist %4,$11+$%3+$12+$14:mov %%4,%8+1*%4-1*(1-%4)
if %1!=%0 goto *movie_count2
if %9==1 lr_trap *movie_end
bgmonce $11+"audio.mus":resettimer
*movie_loop
gettimer %1
if %2<=%1 goto *movie_end
itoa $12,%0*%1/%2
if $12==$10 waittimer 0:goto *movie_loop
mov $10,$12:len %3,$12:btndef $11+$%3+$12+$14:blt 0,0,{bltx1},{blty1},0,0,{bltx2},{blty2}:goto *movie_loop
*movie_end
lr_trap off:ofscpy:bg black,1:stop
mov %0 ,%multiconverteralias0:mov %1 ,%multiconverteralias1:mov %2 ,%multiconverteralias2:mov %3 ,%multiconverteralias3:mov %4 ,%multiconverteralias4
mov %5 ,%multiconverteralias5:mov %6 ,%multiconverteralias6:mov %7 ,%multiconverteralias7:mov %8 ,%multiconverteralias8:mov %9 ,%multiconverteralias9
mov $10,$multiconverteralias0:mov $11,$multiconverteralias1:mov $12,$multiconverteralias2:mov $13,$multiconverteralias3:mov $14,$multiconverteralias4:mov $15,$multiconverteralias5
saveon:return'''.format(bltx1 = bltx1, blty1 = blty1, bltx2 = bltx2, blty2 = blty2))

	#nsa命令追記
	ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'nsa', '')

	return ztxtscript


def set_output_resolution(values: dict, values_ex: dict, override_resolution: list):
	preferred_resolution = values['preferred_resolution']
	select_resolution = values_ex['select_resolution']
	script_resolution = values_ex['script_resolution']

	#最終解像度取得
	if select_resolution:
		if override_resolution: output_resolution = override_resolution#解像度無視変換時

		else:
			if (preferred_resolution == '高解像度優先'): output_resolution = select_resolution[0]
			else: output_resolution = select_resolution[1]

		#その他
	else: output_resolution = script_resolution

	return output_resolution


def onsscript_check(values: dict, values_ex: dict):
	hardware = values['hardware']

	#0.txtのテキスト取得
	ztxtscript = values_ex['0txtscript']

	#*defineがない時
	if not re.search(r'\*define', ztxtscript): raise ValueError('0.txtの復号化に失敗しました')

	#変換済み簡易チェック
	if re.search(r'Converted by "ONScripter Multi Converter', ztxtscript): raise ValueError('既に変換済みです')
	
	#PSP用解像度無視変換フラグ
	if (hardware == 'PSP') and (r'<ONS_RESOLUTION_CHECK_DISABLED>' in ztxtscript): override_resolution = (480, 272)
	else: override_resolution = ()

	#解像度無視変換時setwindow画像描画バグ対策無効化(そのままだと解像度取得ミスって見切れる)
	if override_resolution: values_ex['setwinimgbug'] = False

	#解像度表記抽出&新表記が読めないPSP用変換
	values_ex['script_resolution'], override_resolution, ztxtscript = onsscript_check_resolution(values, values_ex, ztxtscript, override_resolution)

	#元作品解像度が存在しない場合(=別エンジンONSコンバータを事前に使用していない時)0.txtから抽出した解像度をvalues_exに格納
	if not values_ex.get('input_resolution'): values_ex['input_resolution'] = values_ex['script_resolution']

	#最終解像度取得
	values_ex['output_resolution'] = set_output_resolution(values, values_ex, override_resolution)
	
	#画像表示命令抽出
	values_ex['imgdict'] = onsscript_check_image(ztxtscript)

	#bgm再生命令抽出
	values_ex['bgmlist'] = onsscript_check_bgm(ztxtscript)

	#動画再生命令抽出
	values_ex['vidlist'] = onsscript_check_vid(ztxtscript)

	#savedir抽出
	try: values_ex['savedir_path'] = (re.search(r'\n[\t| ]*savedir[\t| ]+"(.+?)"', ztxtscript))[1]
	except: values_ex['savedir_path'] = False

	#画像が初期設定でどのような透過指定で扱われるかを代入
	try: values_ex['imgtransmode'] = (re.search(r'\n[\t| ]*transmode[\t| ]+(leftup|copy|alpha)', ztxtscript))[1][0]#transmode命令があればそれ(の最初の文字)を採用
	except: values_ex['imgtransmode'] = 'a'#見つからないなら初期値leftup…のはずだがlだとタグ付けミスった時盛大に破綻するので仕方なくalpha

	#0.txt関連はここで編集
	ztxtscript = onsscript_check_txtmodify(values, values_ex, ztxtscript, override_resolution)

	#最終的にvalues_exに格納
	values_ex['0txtscript'] = ztxtscript

	return values_ex