#!/usr/bin/env python3
from pathlib import Path
import datetime, i18n, re

from conversion_video import convert_video
from conversion_image import convert_image
from conversion_music import convert_music
from conversion_other import convert_other
from utils import format_check


def create_cnvsetdict(values: dict, values_ex: dict, extracted_dir: Path):
	vid_movfmt_radio = values['vid_movfmt_radio']
	etc_filecomprenban_nsa = values['etc_filecomprenban_nsa']
	etc_filecompimg_nsa = values['etc_filecompimg_nsa']
	aud_bgmch_radio = values['aud_bgmch_radio']
	etc_filecompbgm_nsa = values['etc_filecompbgm_nsa']
	aud_sech_radio = values['aud_sech_radio']
	etc_filecompse_nsa = values['etc_filecompse_nsa']

	#とにかく仕分け作業はここでやる 変換は後で
	cnvset_dict = {}

	for f_path in extracted_dir.glob('**/*'):
		if f_path.is_file():#ファイル(=ディレクトリではない)なら処理
			fc = format_check(f_path)#まずフォーマットチェック
			f_path_re = f_path.relative_to(extracted_dir)

			#[動画]
			if (f_path_re in values_ex['vidlist']) or (fc in ['OGV', 'MP4', 'MPEG', 'AVI']):
				#用意するキー: fileformatのみ (同一タイトルだと全動画仕様統一 → なら変数取るのvaluesからでいいのでは、という)

				#シナリオ命令検知or拡張子で推測 ヘッダ検知できないので仕方なくこの状態
				cnvset_dict[f_path_re] = {'fileformat':'video'}

				#連番のときのみ設定先に
				if (vid_movfmt_radio == i18n.t('var.numbered_images')):
					if (etc_filecomprenban_nsa == 'arc.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc'
					elif (etc_filecomprenban_nsa == 'arc1.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc1'
					elif (etc_filecomprenban_nsa == 'arc2.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc2'
					elif (etc_filecomprenban_nsa == i18n.t('var.do_not_compress')):
						cnvset_dict[f_path_re]['comp'] = 'no_comp'
					else:
						raise ValueError(i18n.t('ui.Sequential_image_compression_not_selected'))

				#通常時は(再生できなくなるので)非圧縮
				else:
					cnvset_dict[f_path_re]['comp'] = 'no_comp'

			#[画像]
			elif fc in ['PNG', 'BMP', 'JPEG']:
				#用意するキー: fileformat/format/part(画像分割数)/trans(copy/alpha/leftup/rightup)

				# 「l」…(leftup) # 「r」…(rightup) # 「a」…(alpha) # 「m」…(mask) # 「c」…(copy)
				# maskは正規表現のタイミングでキー作るの失敗して実質transmodeデフォルト判定になるはず
				# "マスク画像がBMP"かつ"transmodeがleftup"の時に上手く変換できないと思われるが、
				# そもそもmask命令が滅多に使われない&使われてもマスク画像がBMPであることがあまりないはずなのでとりあえず無視(将来的には修正予定)

				cnvset_dict[f_path_re] = {'fileformat':'image'}

				if (values_ex['imgdict'].get(f_path_re) != None):
					d = values_ex['imgdict'][f_path_re]

					d_setwinpos = d.get('setwinpos')
					d_trans = d['trans'] if d.get('trans') else values_ex['imgtransmode']
					
					if d.get('part'):
						d_part = d['part']
					
					else:
						if values['img_multi_chk']: d_part = str(values['img_multi_num'])
						else: d_part = '1'
				
				else:
					d_setwinpos = False
					d_trans = values_ex['imgtransmode']
					if values['img_multi_chk']: d_part = str(values['img_multi_num'])
					else: d_part = '1'

				#アルファブレンドのためx2分割
				if (fc in ['JPEG', 'BMP']) and (d_trans == 'a'): d_part = str(int(d_part) * 2)

				#代入
				cnvset_dict[f_path_re]['setwinpos'] = d_setwinpos
				cnvset_dict[f_path_re]['trans'] = d_trans
				cnvset_dict[f_path_re]['part'] = d_part

				#copy/alphaのBMPの場合はJPEGに変換
				if (fc == 'BMP' and d_trans in ['c', 'a']):
					cnvset_dict[f_path_re]['format'] = 'JPEG'
				else:
					cnvset_dict[f_path_re]['format'] = fc

				if (etc_filecompimg_nsa == 'arc.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc'
				elif (etc_filecompimg_nsa == 'arc1.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc1'
				elif (etc_filecompimg_nsa == 'arc2.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc2'
				elif (etc_filecompimg_nsa == i18n.t('var.do_not_compress')):
					cnvset_dict[f_path_re]['comp'] = 'no_comp'
				else:
					raise ValueError(i18n.t('ui.Image_compression_not_selected'))

			#[音楽]
			elif fc in ['WAV', 'OGG', 'MP3']:
				#用意するキー: fileformat/format/kbps/hz/ch/cutoff/acodec

				#BGMかSEかの判断をここでやる
				cnvset_dict[f_path_re] = {'fileformat':'music'}
				
				if (f_path_re in values_ex['bgmlist']) or ('bgm' in str(f_path_re).lower()) or (re.fullmatch(r'cd[\/\\]track[0-9]{2}\.[A-z0-9]+', str(f_path_re).lower())):

					if (aud_bgmch_radio == i18n.t('var.stereo')):
						cnvset_dict[f_path_re]['ch'] = '2'
					elif (aud_bgmch_radio == i18n.t('var.mono')):
						cnvset_dict[f_path_re]['ch'] = '1'
					else:
						raise ValueError(i18n.t('ui.BGM_channel_not_selected'))

					match values['aud_bgmfmt_radio']:
						case 'WAV':
							cnvset_dict[f_path_re]['format'] = 'WAV'
							cnvset_dict[f_path_re]['hz'] = values['aud_wavbgm_hz']
							match values['aud_bgmcodec_radio']:
								case 'pcm_s16le': cnvset_dict[f_path_re]['acodec'] = 'pcm_s16le'
								case 'pcm_u8': cnvset_dict[f_path_re]['acodec'] = 'pcm_u8'
								case _: raise ValueError(i18n.t('ui.WAV_codec_not_selected'))

						case 'OGG':
							cnvset_dict[f_path_re]['format'] = 'OGG'
							cnvset_dict[f_path_re]['kbps'] = values['aud_oggbgm_kbps']
							cnvset_dict[f_path_re]['hz'] = values['aud_oggbgm_hz']

						case 'MP3':
							cnvset_dict[f_path_re]['format'] = 'MP3'
							cnvset_dict[f_path_re]['kbps'] = values['aud_mp3bgm_kbps']
							cnvset_dict[f_path_re]['hz'] = values['aud_mp3bgm_hz']
							cnvset_dict[f_path_re]['cutoff'] = values['aud_mp3bgm_cutoff']
						
						case _: raise ValueError(i18n.t('ui.BGM_format_not_selected'))
						
					if (etc_filecompbgm_nsa == 'arc.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc'
					elif (etc_filecompbgm_nsa == 'arc1.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc1'
					elif (etc_filecompbgm_nsa == 'arc2.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc2'
					elif (etc_filecompbgm_nsa == i18n.t('var.do_not_compress')):
						cnvset_dict[f_path_re]['comp'] = 'no_comp'
					else:
						raise ValueError(i18n.t('ui.BGM_compression_not_selected'))
				
				else:
					if (aud_sech_radio == i18n.t('var.stereo')):
						cnvset_dict[f_path_re]['ch'] = '2'
					elif (aud_sech_radio == i18n.t('var.mono')):
						cnvset_dict[f_path_re]['ch'] = '1'
					else:
						raise ValueError(i18n.t('ui.SE_channel_not_selected'))

					match values['aud_sefmt_radio']:
						case 'WAV':
							cnvset_dict[f_path_re]['format'] = 'WAV'
							cnvset_dict[f_path_re]['hz'] = values['aud_wavse_hz']
							match values['aud_secodec_radio']:
								case 'pcm_s16le': cnvset_dict[f_path_re]['acodec'] = 'pcm_s16le'
								case 'pcm_u8': cnvset_dict[f_path_re]['acodec'] = 'pcm_u8'
								case _: raise ValueError(i18n.t('ui.WAV_codec_not_selected'))

						case 'OGG':
							cnvset_dict[f_path_re]['format'] = 'OGG'
							cnvset_dict[f_path_re]['kbps'] = values['aud_oggse_kbps']
							cnvset_dict[f_path_re]['hz'] = values['aud_oggse_hz']

						case 'MP3':
							cnvset_dict[f_path_re]['format'] = 'MP3'
							cnvset_dict[f_path_re]['kbps'] = values['aud_mp3se_kbps']
							cnvset_dict[f_path_re]['hz'] = values['aud_mp3se_hz']
							cnvset_dict[f_path_re]['cutoff'] = values['aud_mp3se_cutoff']
						
						case _: raise ValueError(i18n.t('ui.SE_format_not_selected'))
					
					if (etc_filecompse_nsa == 'arc.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc'
					elif (etc_filecompse_nsa == 'arc1.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc1'
					elif (etc_filecompse_nsa == 'arc2.nsa'):
						cnvset_dict[f_path_re]['comp'] = 'arc2'
					elif (etc_filecompse_nsa == i18n.t('var.do_not_compress')):
						cnvset_dict[f_path_re]['comp'] = 'no_comp'
					else:
						raise ValueError(i18n.t('ui.SE_compression_not_selected'))
								
			#[他]
			else:
				#用意するキー: fileformatのみ
				cnvset_dict[f_path_re] = {'fileformat':'other'}

				#めんどいので画像と同じ扱い(将来的に修正予定)
				if (etc_filecompimg_nsa == 'arc.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc'
				elif (etc_filecompimg_nsa == 'arc1.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc1'
				elif (etc_filecompimg_nsa == 'arc2.nsa'):
					cnvset_dict[f_path_re]['comp'] = 'arc2'
				elif (etc_filecompimg_nsa == i18n.t('var.do_not_compress')):
					cnvset_dict[f_path_re]['comp'] = 'no_comp'
				else:
					raise ValueError(i18n.t('ui.Other_compression_not_selected'))

	return cnvset_dict


def tryconvert(values: dict, values_ex: dict, f_dict: dict, f_path_re: Path, converted_dir: Path):

	try:
		match f_dict['fileformat']:#ファイルフォーマットによる分岐
			case 'video': convert_video(values, values_ex, f_dict)
			case 'image': convert_image(values, values_ex, f_dict)
			case 'music': convert_music(f_dict)
			case 'other': convert_other(f_dict)
			case _: raise Exception('Unknown format. (messages from converter.)')#csvに書く用、多分出ない

	except Exception as e:
		dt_now = datetime.datetime.now()
		errmsg = f'{dt_now.strftime('%Y/%m/%d %H:%M:%S.%f')}\t{f_path_re}\t{e}\n'
		with open(Path(converted_dir / ('ERROR' + dt_now.strftime('%Y%m%d%H%M%S%f') + str(f_path_re.stem).upper()[:20]) ), 'w', encoding='utf-8') as s: s.write(errmsg)

	return