from PIL import Image
from io import BytesIO
import mozjpeg_lossless_optimization as mozj
import imagequant as iq
import zopfli as zf
import numpy as np
import base64, shutil, math

from b64_data import get_cur_dict


def convert_image(values: dict, values_ex: dict, f_dict: dict):
	img_pngquantize_chk = bool(values['img_pngquantize_chk'])
	img_pngquantize_num = int(values['img_pngquantize_num'])
	img_jpgquality_bar = int(values['img_jpgquality_bar'])
	output_resolution = values_ex['output_resolution']
	input_resolution = values_ex['input_resolution']
	setwinimgbug = values_ex['setwinimgbug']
	setwinpos = f_dict.get('setwinpos')
	extractedpath = f_dict['extractedpath']
	convertedpath = f_dict['convertedpath']
	d_format = f_dict['format'] #最終出力フォーマット
	d_trans = f_dict['trans'] #表示モード(c/a/l/r)
	d_part = int(f_dict['part']) #表示時分割数

	#縦横倍率をtapleで保持
	scale = (
		(output_resolution[0] / input_resolution[0]),
		(output_resolution[1] / input_resolution[1])
	)

	# 画像を開く
	input_img = Image.open(extractedpath)

	#αチャンネル付き&非RGBAな画像をRGBAへ変換
	if ('transparency' in input_img.info): input_img = input_img.convert('RGBA')
	
	#その他RGBじゃない画像をRGB形式に(但しRGBAはそのまま)
	elif (not (input_img.mode in ['RGB', 'RGBA'])): input_img = input_img.convert('RGB')

	#変換後サイズを指定
	output_width = math.ceil(input_img.width * scale[0] / d_part) * d_part#横
	output_height = math.ceil(input_img.height * scale[1])#縦

	#ここでそもそも縮小が必要かどうかで分岐 - if文で囲っておき、不要の場合保存フェーズへ飛ばす
	if scale != (1, 1):
		#transがl、bmpかpng、解像度が既定値の場合 - カーソル比較モード
		if (d_trans == 'l') and (d_format in ['BMP', 'PNG']) and (input_img.size in [(72, 24), (24, 24)]):
			output_img_b64 = ''

			#画素比較のためnumpyへ変換
			input_img_np = np.array(input_img.convert('RGB'))

			#カーソルの入った辞書を取ってくる
			cur_dict = get_cur_dict()

			#for文で標準画像とそれぞれ比較
			for name, b64file in cur_dict['default'].items():
				default_img = Image.open(BytesIO(base64.b64decode(b64file)))
				default_img_np = np.array(default_img.convert('RGB'))

				#カーソルが公式の画像と同一の時
				if np.array_equal(input_img_np, default_img_np):

					#縮小率50%で区切って大小どっちか取ってくる
					if (scale[0] < 0.5): output_img_b64 = cur_dict['small'][name]
					else: output_img_b64 = cur_dict['big'][name]

			#b64が代入できた(≒カーソルが合致した)場合
			if output_img_b64:

				#書き込んで
				with open(convertedpath, 'wb') as f: f.write(base64.b64decode(output_img_b64))

				#もう終了でいいや
				return
			
		#透明判定px抽出→代入
		match d_trans:
			case 'l': trans_px = input_img.getpixel((0, 0))
			case 'r': trans_px = input_img.getpixel((input_img.width - 1, 0))
			case _: 
				if   (input_img.mode == 'RGB') : trans_px = (0, 0, 0)
				elif (input_img.mode == 'RGBA'): trans_px = (0, 0, 0, 0)
				else: raise ValueError('RGBでもRGBAでもありません 変換ミスでは?')

		
		#通常処理(カーソル比較モード抜けた後)
		output_img = Image.new(input_img.mode, (output_width, output_height), trans_px)

		#分割する横幅を指定
		crop_width = int(input_img.width / d_part)
		output_crop_width = math.ceil(output_width / d_part)
		
		for di in range(d_part):#枚数分繰り返す
			cropped_img = input_img.crop((crop_width * di, 0, crop_width * (di + 1), input_img.height))#画像切り出し

			#lかrで呼び出し & BMPかJPG & 元の高さが32px以下 & 横が縦で割り切れる → カーソル切り出し処理 (この辺割と雰囲気で決めてる)
			if (d_trans in ['l', 'r']) and (d_format in ['BMP', 'PNG']) and (input_img.height <= 32) and ((cropped_img.width / cropped_img.height) == int(cropped_img.width / cropped_img.height)):

				#numpy変換
				cropped_img_np = np.array(cropped_img.convert('RGB'))
				msk_img_np = np.array(cropped_img.convert('RGB'))
				cropped_img_np.flags.writeable = True
				msk_img_np.flags.writeable = True

				#念の為numpyから縦横取り直し - Imageのw/hから取るとたまに何故かindex範囲外指定エラー出てたので
				cropped_img_height = cropped_img_np.shape[0]
				cropped_img_width = cropped_img_np.shape[1]

				#透過部分灰色化&マスク作成
				for i in range(cropped_img_width):
					for j in range(cropped_img_height):

						#透過判定元代入
						if (d_trans == 'l'): a_px = 0, 0
						elif (d_trans == 'r'): a_px = cropped_img.width - 1, 0

						if  (i, j) == (a_px):#背景色設定元
							msk_img_np[i, j] = np.array([0, 0, 0])

						elif np.all(cropped_img_np[i, j] == cropped_img_np[a_px]):#背景色と一致	
							cropped_img_np[i, j] = np.array([128, 128, 128])#灰色に
							msk_img_np[i, j] = np.array([0, 0, 0])

						else:#背景色不一致
							msk_img_np[i, j] = np.array([255, 255, 255])

				#最後に背景色設定元を変更
				cropped_img_np[a_px] = np.array([128, 128, 128])

				#numpy書き戻し
				cropped_img = Image.fromarray(np.uint8(cropped_img_np))
				msk_img = Image.fromarray(np.uint8(msk_img_np))

				#リサイズ
				cropped_img = cropped_img.resize((output_crop_width - 1, output_height - 1), Image.Resampling.LANCZOS)
				msk_img = msk_img.resize((output_crop_width - 1, output_height - 1), Image.Resampling.NEAREST)

				#msk L変換
				msk_img = msk_img.convert('L')

				#塗りつぶし背景作成
				fill_img = Image.new('RGB', (output_crop_width, output_height), trans_px)

				#マスク切り出し
				cropped_img = Image.composite(cropped_img, fill_img, msk_img)
				output_img.paste(cropped_img, (output_crop_width * di, 1))#結合用画像へ貼り付け

			else:
				cropped_img = cropped_img.resize((output_crop_width, output_height), Image.Resampling.LANCZOS)#縮小
				output_img.paste(cropped_img, (output_crop_width * di, 0))#結合用画像へ貼り付け
		
		#setwindow命令で表示した画像(透過PNGのみ?)の右と下に描画不具合が出るやつを修正
		if (setwinimgbug) and (setwinpos) and (output_img.mode == 'RGBA'):
			
			#右&下を透明で埋めたあとの解像度 - 念の為+1
			output_fix_width = math.ceil((input_resolution[0] - int(setwinpos[0])) * scale[0]) + 1
			output_fix_height = math.ceil((input_resolution[1] - int(setwinpos[1])) * scale[1]) + 1

			print(output_fix_width, output_fix_height)

			output_fix_img = Image.new('RGBA', (output_fix_width, output_fix_height), (0, 0, 0, 0))
			output_fix_img.paste(output_img, (0, 0))

			output_img = output_fix_img

	#縮小しないならoutがそのままin使いまわし
	else: output_img = input_img

	#保存 - format参照
	match d_format:
		# BMP 素直に保存です
		case 'BMP':
			output_img.save(convertedpath, format='BMP')

		# JPEG BytesIO/mozjpeg経由保存 ('img_jpgquality_bar'参照)
		case 'JPEG':
			io_img = BytesIO()
			output_img.save(io_img, format='JPEG', quality=img_jpgquality_bar)
			io_img.seek(0)
			with open(convertedpath, 'wb') as c: c.write(mozj.optimize(io_img.read()))

		# PNG 
		case 'PNG':
			#imagequant/BytesIO/ZopfliPNG経由保存
			if img_pngquantize_chk: quant_img = iq.quantize_pil_image(output_img, dithering_level=1.0, max_colors=img_pngquantize_num, min_quality=0, max_quality=100)
			else: quant_img = output_img
			io_img = BytesIO()
			quant_img.save(io_img, format='PNG')
			io_img.seek(0)
			with open(convertedpath, 'wb') as c: c.write(zf.ZopfliPNG().optimize(io_img.read()))

		case _: raise ValueError('画像保存フォーマット未選択エラー(たぶんこれ出ないと思うんだけど)')

	#元nbz用コビー
	if (f_dict['nbz']) and (convertedpath.suffix != '.nbz'): shutil.copy(convertedpath, convertedpath.with_suffix('.nbz'))
	return