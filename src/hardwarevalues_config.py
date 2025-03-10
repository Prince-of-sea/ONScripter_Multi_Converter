#!/usr/bin/env python3
import i18n


# 対応機種はここに書き足す
def gethardwarevalues_full():
	return {
		'PSP': {
			'values_ex': {
				'hardware_full': 'SONY PlayStation Portable',
				'support_charset': ('cp932', 'gbk'),
				'select_resolution': ((360, 270), (320, 240)),
				'disable_video': ('MP4'),
				'aspect_4:3only': True,
				'setwinimgbug': True,
				'configfile': 'ons.ini',
			},

			'values_default': {
				'preferred_resolution': i18n.t('var.high_resolution_priority'),
				'img_jpgquality_bar': 95, 'img_pngquantize_chk': True, 'img_pngquantize_num': '256',
				'img_bmptojpg_chk': True, 'img_multi_chk': True, 'img_multi_num': '2',

				'aud_bgmfmt_radio': 'OGG', 'aud_sefmt_radio': 'OGG',
				'aud_bgmch_radio': i18n.t('var.stereo'), 'aud_sech_radio': i18n.t('var.mono'),
				'aud_oggbgm_kbps': '96', 'aud_oggbgm_hz': '44100',
				'aud_oggse_kbps': '56', 'aud_oggse_hz': '22050',
				'aud_mp3bgm_kbps': '128', 'aud_mp3bgm_hz': '44100',
				'aud_mp3se_kbps': '96', 'aud_mp3se_hz': '22050',
				'aud_mp3bgm_cutoff': '13500', 'aud_mp3se_cutoff': '10500',
				'aud_wavbgm_hz': '44100', 'aud_wavse_hz': '22050',
				'aud_bgmcodec_radio': 'pcm_s16le', 'aud_secodec_radio': 'pcm_s16le',

				'vid_movfmt_radio': 'MJPEG',
				'vid_renbanfmt_radio': 'PNG', 'vid_renbanres_radio': '100%(1/1)',
				'vid_renbanpngquantize_chk': True, 'vid_renbanpngquantize_num': '256',
				'vid_renbanjpgquality_bar': 90,
				'vid_renbanaudset_radio': i18n.t('var.bgm_match'),
				'vid_mjpegquality_bar': 8,
				'vid_mp4quality_bar': 4, 'vid_mp4aud_kbps': '160', 'vid_mp4aud_hz': '44100',

				'etc_filecompimg_nsa': 'arc.nsa', 'etc_filecompbgm_nsa': 'arc1.nsa', 'etc_filecompse_nsa': 'arc2.nsa', 'etc_filecomprenban_nsa': 'arc2.nsa',
				'etc_fileexdll_chk': True, 'etc_fileexdb_chk': True,
				'etc_iniscreen': i18n.t('var.no_expansion'), 'etc_iniramfont_chk': True, 'etc_inicursor_chk': False,

				'etc_0txtnbz_radio': i18n.t('var.replace_all_nbz_to_wav'),
				'etc_0txtavitompegplay': i18n.t('var.use_function_override'),
				'etc_0txtnoscreenshot': i18n.t('var.use_function_override'),
				'etc_0txtmaxkaisoupage_chk': True,
				'etc_0txtmaxkaisoupage_num': '3',
				'etc_0txtoverwritesavenumber_chk': False,
				'etc_0txtoverwritesavenumber_num': '10',
				'etc_0txtsetwindowbigfont_chk': True,
				'etc_0txtskipokcancelbox_chk': True,
				'etc_0txtskipyesnobox_chk': True,
				'etc_0txtrndtornd2_chk': True,
				'etc_0txtdisabletextgosub_chk': False,
				'etc_0txtremovecommentout_chk': True,
			}
		},

		'PSVITA': {
			'values_ex': {
				'hardware_full': 'SONY PlayStation Vita',
				'support_charset': ('cp932', 'gbk'),
				'select_resolution': (),
				'disable_video': ('MJPEG', 'MP4'),
				'aspect_4:3only': False,
				'setwinimgbug': False,
				'configfile': 'sittings.txt',
			},

			'values_default': {
				'preferred_resolution': i18n.t('var.high_resolution_priority'),
				'img_jpgquality_bar': 95, 'img_pngquantize_chk': False, 'img_pngquantize_num': '256',
				'img_bmptojpg_chk': True, 'img_multi_chk': False, 'img_multi_num': '1',

				'aud_bgmfmt_radio': 'OGG', 'aud_sefmt_radio': 'WAV',
				'aud_bgmch_radio': i18n.t('var.stereo'), 'aud_sech_radio': i18n.t('var.mono'),
				'aud_oggbgm_kbps': '128', 'aud_oggbgm_hz': '44100',
				'aud_oggse_kbps': '64', 'aud_oggse_hz': '22050',
				'aud_mp3bgm_kbps': '160', 'aud_mp3bgm_hz': '44100',
				'aud_mp3se_kbps': '96', 'aud_mp3se_hz': '22050',
				'aud_mp3bgm_cutoff': '15000', 'aud_mp3se_cutoff': '12000',
				'aud_wavbgm_hz': '44100', 'aud_wavse_hz': '22050',
				'aud_bgmcodec_radio': 'pcm_s16le', 'aud_secodec_radio': 'pcm_s16le',

				'vid_movfmt_radio': i18n.t('var.numbered_images'),
				'vid_renbanfmt_radio': 'JPEG', 'vid_renbanres_radio': '66%(2/3)',
				'vid_renbanpngquantize_chk': True, 'vid_renbanpngquantize_num': '256',
				'vid_renbanjpgquality_bar': 90,
				'vid_renbanaudset_radio': i18n.t('var.se_voice_match'),
				'vid_mjpegquality_bar': 8,
				'vid_mp4quality_bar': 4, 'vid_mp4aud_kbps': '160', 'vid_mp4aud_hz': '44100',

				'etc_filecompimg_nsa': 'arc.nsa', 'etc_filecompbgm_nsa': 'arc.nsa', 'etc_filecompse_nsa': 'arc1.nsa', 'etc_filecomprenban_nsa': 'arc2.nsa',
				'etc_fileexdll_chk': True, 'etc_fileexdb_chk': True,
				'etc_iniscreen': i18n.t('var.no_expansion'), 'etc_iniramfont_chk': True, 'etc_inicursor_chk': False,

				'etc_0txtnbz_radio': i18n.t('var.replace_all_nbz_to_wav'),
				'etc_0txtavitompegplay': i18n.t('var.use_function_override'),
				'etc_0txtnoscreenshot': i18n.t('var.use_function_override'),
				'etc_0txtmaxkaisoupage_chk': True,
				'etc_0txtmaxkaisoupage_num': '10',
				'etc_0txtoverwritesavenumber_chk': False,
				'etc_0txtoverwritesavenumber_num': '10',
				'etc_0txtsetwindowbigfont_chk': False,
				'etc_0txtskipokcancelbox_chk': True,
				'etc_0txtskipyesnobox_chk': True,
				'etc_0txtrndtornd2_chk': False,
				'etc_0txtdisabletextgosub_chk': False,
				'etc_0txtremovecommentout_chk': True,
			}
		},

		'Brain': {
			'values_ex': {
				'hardware_full': 'SHARP Brain(Windows CE 6.0)',
				'support_charset': ('cp932'),
				'select_resolution': ((424, 318), (320, 240)),
				'disable_video': ('MJPEG', 'MP4'),
				'aspect_4:3only': True,
				'setwinimgbug': False,
				'configfile': '',
			},

			'values_default': {
				'preferred_resolution': i18n.t('var.high_resolution_priority'),
				'img_jpgquality_bar': 90, 'img_pngquantize_chk': True, 'img_pngquantize_num': '256',
				'img_bmptojpg_chk': True, 'img_multi_chk': True, 'img_multi_num': '2',

				'aud_bgmfmt_radio': 'MP3', 'aud_sefmt_radio': 'WAV',
				'aud_bgmch_radio': i18n.t('var.stereo'), 'aud_sech_radio': i18n.t('var.mono'),
				'aud_oggbgm_kbps': '56', 'aud_oggbgm_hz': '22050',
				'aud_oggse_kbps': '56', 'aud_oggse_hz': '22050',
				'aud_mp3bgm_kbps': '96', 'aud_mp3bgm_hz': '44100',
				'aud_mp3se_kbps': '56', 'aud_mp3se_hz': '22050',
				'aud_mp3bgm_cutoff': '13500', 'aud_mp3se_cutoff': '10500',
				'aud_wavbgm_hz': '22050', 'aud_wavse_hz': '22050',
				'aud_bgmcodec_radio': 'pcm_u8', 'aud_secodec_radio': 'pcm_u8',

				'vid_movfmt_radio': i18n.t('var.numbered_images'),
				'vid_renbanfmt_radio': 'JPEG', 'vid_renbanres_radio': '50%(1/2)',
				'vid_renbanpngquantize_chk': True, 'vid_renbanpngquantize_num': '256',
				'vid_renbanjpgquality_bar': 85,
				'vid_renbanaudset_radio': i18n.t('var.bgm_match'),
				'vid_mjpegquality_bar': 8,
				'vid_mp4quality_bar': 4, 'vid_mp4aud_kbps': '160', 'vid_mp4aud_hz': '44100',

				'etc_filecompimg_nsa': 'arc.nsa', 'etc_filecompbgm_nsa': i18n.t('var.do_not_compress'), 'etc_filecompse_nsa': 'arc.nsa', 'etc_filecomprenban_nsa': 'arc.nsa',
				'etc_fileexdll_chk': True, 'etc_fileexdb_chk': True,
				'etc_iniscreen': i18n.t('var.no_expansion'), 'etc_iniramfont_chk': True, 'etc_inicursor_chk': True,

				'etc_0txtnbz_radio': i18n.t('var.replace_all_nbz_to_wav'),
				'etc_0txtavitompegplay': i18n.t('var.use_function_override'),
				'etc_0txtnoscreenshot': i18n.t('var.use_function_override'),
				'etc_0txtmaxkaisoupage_chk': True,
				'etc_0txtmaxkaisoupage_num': '3',
				'etc_0txtoverwritesavenumber_chk': False,
				'etc_0txtoverwritesavenumber_num': '10',
				'etc_0txtsetwindowbigfont_chk': True,
				'etc_0txtskipokcancelbox_chk': True,
				'etc_0txtskipyesnobox_chk': True,
				'etc_0txtrndtornd2_chk': True,
				'etc_0txtdisabletextgosub_chk': False,
				'etc_0txtremovecommentout_chk': True,
			}
		},

		'Android': {
			'values_ex': {
				'hardware_full': 'Android OS',
				'support_charset': ('cp932', 'gbk', 'utf-8'),
				'select_resolution': (),
				'disable_video': ('MJPEG'),
				'aspect_4:3only': False,
				'setwinimgbug': False,
				'configfile': '',
			},

			'values_default': {
				'preferred_resolution': i18n.t('var.high_resolution_priority'),
				'img_jpgquality_bar': 95, 'img_pngquantize_chk': False, 'img_pngquantize_num': '256',
				'img_bmptojpg_chk': True, 'img_multi_chk': False, 'img_multi_num': '1',

				'aud_bgmfmt_radio': 'OGG', 'aud_sefmt_radio': 'OGG',
				'aud_bgmch_radio': i18n.t('var.stereo'), 'aud_sech_radio': i18n.t('var.stereo'),
				'aud_oggbgm_kbps': '192', 'aud_oggbgm_hz': '44100',
				'aud_oggse_kbps': '96', 'aud_oggse_hz': '44100',
				'aud_mp3bgm_kbps': '192', 'aud_mp3bgm_hz': '44100',
				'aud_mp3se_kbps': '128', 'aud_mp3se_hz': '44100',
				'aud_mp3bgm_cutoff': '18000', 'aud_mp3se_cutoff': '16500',
				'aud_wavbgm_hz': '44100', 'aud_wavse_hz': '44100',
				'aud_bgmcodec_radio': 'pcm_s16le', 'aud_secodec_radio': 'pcm_s16le',

				'vid_movfmt_radio': 'MP4',
				'vid_renbanfmt_radio': 'PNG', 'vid_renbanres_radio': '100%(1/1)',
				'vid_renbanpngquantize_chk': True, 'vid_renbanpngquantize_num': '256',
				'vid_renbanjpgquality_bar': 95,
				'vid_renbanaudset_radio': i18n.t('var.bgm_match'),
				'vid_mjpegquality_bar': 8,
				'vid_mp4quality_bar': 4, 'vid_mp4aud_kbps': '160', 'vid_mp4aud_hz': '44100',

				'etc_filecompimg_nsa': 'arc.nsa', 'etc_filecompbgm_nsa': 'arc1.nsa', 'etc_filecompse_nsa': 'arc2.nsa', 'etc_filecomprenban_nsa': 'arc2.nsa',
				'etc_fileexdll_chk': True, 'etc_fileexdb_chk': True,
				'etc_iniscreen': i18n.t('var.no_expansion'), 'etc_iniramfont_chk': True, 'etc_inicursor_chk': True,

				'etc_0txtnbz_radio': i18n.t('var.replace_all_nbz_to_wav'),
				'etc_0txtavitompegplay': i18n.t('var.use_function_override'),
				'etc_0txtnoscreenshot': i18n.t('var.use_function_override'),
				'etc_0txtmaxkaisoupage_chk': False,
				'etc_0txtmaxkaisoupage_num': '20',
				'etc_0txtoverwritesavenumber_chk': False,
				'etc_0txtoverwritesavenumber_num': '10',
				'etc_0txtsetwindowbigfont_chk': False,
				'etc_0txtskipokcancelbox_chk': False,
				'etc_0txtskipyesnobox_chk': False,
				'etc_0txtrndtornd2_chk': False,
				'etc_0txtdisabletextgosub_chk': False,
				'etc_0txtremovecommentout_chk': True,
			}
		},
	}


def gethardwarevalues(k: str, k2: str):
	return gethardwarevalues_full()[k][k2]