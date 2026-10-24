#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageEnhance
import concurrent.futures
import numpy as np
import struct, io, re, shutil, subprocess, os, sys, unicodedata


# 作品について
def title_info():
	return {
		'brand': 'Purple software',
		'date': 20030228,
		'title': '夏色小町',
		'cli_arg': 'purple_natsuiro',
		'requiredsoft': [],
		'is_4:3': True,
		'exe_name': ['ntk'],

		'version': [
			'夏色小町 パッケージ版',
		],

		'notes': [
			'ムービー(OP/ED/イベント)は未対応のためスキップ',
			'主人公の名前はデフォルト(中田 友也)で固定',
			'立ち絵の瞬き/口パク差分は未対応',
			'おまけはCG閲覧/音楽室のみ(イベント閲覧は未実装)',
			'UIは簡略化(セーブ/ロード等はONScripter標準)',
			'画面効果(フラッシュ等)は一部省略',
		]
	}


# --- アーカイブ(PK)読み込み ---

# 索引の暗号解除
def pk_decrypt(data, seed):
	n = len(data) // 4
	if n == 0: return bytes(data)

	words = np.frombuffer(bytes(data[:n * 4]), dtype='<u4').copy()
	ctls = []
	keys = []
	seed &= 0xFFFFFFFF

	for i in range(32):
		code = 0
		k = seed
		for j in range(16):
			code = (((k ^ (k >> 1)) << 15) | ((code & 0xFFFF) >> 1)) & 0xFFFFFFFF
			k >>= 2
		keys.append(seed)
		ctls.append(code & 0xFFFF)
		seed = ((seed << 1) | (seed >> 31)) & 0xFFFFFFFF

	for k in range(32):
		m1 = 0
		for j in range(16):
			if (ctls[k] >> j) & 1: m1 |= 1 << (2 * j)
		m3 = m1 * 3
		sub = words[k::32]
		sub = (sub & np.uint32(~m3 & 0xFFFFFFFF)) | ((sub & np.uint32(m1)) << np.uint32(1)) | ((sub >> np.uint32(1)) & np.uint32(m1))
		words[k::32] = sub ^ np.uint32(keys[k])

	return words.tobytes() + bytes(data[n * 4:])


# PK内のファイル一覧取得 -> [(名前, オフセット, サイズ)]
def pk_list(path: Path):
	with open(path, 'rb') as f:
		head = f.read(8)
		wide = head[3:4] == b'2'
		sz = 8 if wide else 4
		fmt = '<Q' if wide else '<I'
		total = f.seek(0, 2)
		pos = 4 + sz
		ents = []
		names = b''
		base = 0

		while pos < total:
			f.seek(pos)
			hd = f.read(4 + sz * 2)
			sid = hd[:4]
			ssz = struct.unpack_from(fmt, hd, 4)[0]
			hsz = struct.unpack_from(fmt, hd, 4 + sz)[0]

			if sid == b'cLST':
				_, count, key = struct.unpack('<III', f.read(12))
				f.seek(pos + hsz)
				clst = pk_decrypt(f.read(ssz - hsz), key)
				for i in range(count):
					o = i * sz * 3
					ents.append((
						struct.unpack_from(fmt, clst, o)[0],
						struct.unpack_from(fmt, clst, o + sz)[0],
						struct.unpack_from(fmt, clst, o + sz * 2)[0],
					))
			elif sid == b'cNAM':
				_, key = struct.unpack('<II', f.read(8))
				f.seek(pos + hsz)
				names = pk_decrypt(f.read(ssz - hsz), key)
			elif sid == b'cDAT':
				base = pos + hsz

			pos += ssz

	out = []
	for no, off, size in ents:
		out.append((names[no:names.index(b'\0', no)].decode('cp932'), base + off, size))
	return out


# PK内のファイル読み込み
def pk_read(path: Path, off: int, size: int):
	with open(path, 'rb') as f:
		f.seek(off)
		return f.read(size)


# --- 画像(SG)デコード ---

# SG -> PIL.Image, (x, y, canvas_w, canvas_h)
def sg_decode(b: bytes):
	h = b[8:8 + 0x24]
	hs = struct.unpack_from('<i', h, 8)[0]
	size = struct.unpack_from('<i', h, 0xC)[0]
	p = 8 + hs

	if h[:4] == b'cJPG':
		key = struct.unpack_from('<I', h, 0x20)[0]
		im = Image.open(io.BytesIO(pk_decrypt(b[p:p + size], key))).convert('RGB')
		return im, (struct.unpack_from('<h', h, 0x14)[0], struct.unpack_from('<h', h, 0x16)[0], im.width, im.height)

	mode = struct.unpack_from('<H', h, 0x10)[0]
	cw, ch_ = struct.unpack_from('<HH', h, 0x14)
	ox, oy = struct.unpack_from('<hh', h, 0x18)
	w, hh = struct.unpack_from('<HH', h, 0x1C)
	ch = struct.unpack_from('<H', h, 0x22)[0] // 8
	meta = (ox, oy, cw, ch_)

	if mode == 0:
		arr = np.frombuffer(b, np.uint8, w * hh * ch, p).reshape(hh, w, ch)

	elif mode == 1:
		arr = np.zeros((hh, w, ch), np.uint8)
		for y in range(hh):
			line = bytearray()
			for c in range(ch):
				x = 0
				while x < w:
					ctl = b[p]; p += 1
					cnt = ctl & 0x3F
					if ctl & 0x40:
						cnt = (cnt << 8) | b[p]; p += 1
					if ctl & 0x80:
						line += b[p:p + 1] * cnt; p += 1
					else:
						line += b[p:p + cnt]; p += cnt
					x += cnt
			arr[y] = np.frombuffer(bytes(line), np.uint8).reshape(ch, w).T

	elif mode == 3:
		idx = struct.unpack_from('<%di' % hh, b, p)
		base = p + 4 * hh
		arr = np.zeros((hh, w, ch), np.uint8)
		for y in range(hh):
			q = base + idx[y]
			x = 0
			row = bytearray()
			while x < w:
				ctl = b[q]; q += 1
				cnt = ctl & 0x3F
				if ctl & 0x40:
					cnt = (cnt << 8) | b[q]; q += 1
				x += cnt
				if ctl & 0x80:
					row += b[q:q + ch] * cnt; q += ch
				else:
					row += b[q:q + cnt * ch]; q += cnt * ch
			arr[y] = np.frombuffer(bytes(row), np.uint8).reshape(w, ch)

	else:
		pal = np.frombuffer(b, np.uint8, 1024, p).reshape(256, 4)[:, 2::-1]
		p += 1024
		idx = struct.unpack_from('<%di' % hh, b, p)
		base = p + 4 * hh
		end = len(b)

		if ch == 3:
			ind = np.zeros((hh, w), np.uint8)
			for y in range(hh):
				q = base + idx[y]
				x = 0
				row = bytearray()
				while x < w:
					ctl = b[q]; q += 1
					cnt = ctl >> 2
					if ctl & 2:
						cnt |= b[q] << 6; q += 1
					cnt = min(cnt, w - x)
					x += cnt
					if ctl & 1:
						row += b[q:q + 1] * cnt; q += 1
					else:
						row += b[q:q + cnt]; q += cnt
				ind[y] = np.frombuffer(bytes(row), np.uint8)
			arr = pal[ind]
			return Image.fromarray(np.ascontiguousarray(arr), 'RGB'), meta

		# 4bit alpha + 8bit palette index (LSB first bit stream)
		arr = np.zeros((hh, w, 4), np.uint8)
		pow12 = (1 << np.arange(12)).astype(np.uint32)
		for y in range(hh):
			s = base + idx[y]
			e = base + idx[y + 1] if y + 1 < hh else end
			rb = b[s:e] + b'\0\0\0\0'
			rint = int.from_bytes(rb, 'little')
			bits = None
			pos = 0
			x = 0
			while x < w:
				ctl = (rint >> pos) & 3
				pos += 2
				if ctl & 2:
					cnt = (rint >> pos) & 0x3FF; pos += 10
				else:
					cnt = (rint >> pos) & 3; pos += 2
				cnt = min(cnt, w - x)
				if ctl & 1:
					v = (rint >> pos) & 0xFFF; pos += 12
					a = v & 15
					arr[y, x:x + cnt, :3] = pal[v >> 4]
					arr[y, x:x + cnt, 3] = ((a << 4) | 15) if a else 0
				elif cnt:
					if bits is None: bits = np.unpackbits(np.frombuffer(rb, np.uint8), bitorder='little')
					v = bits[pos:pos + 12 * cnt].reshape(cnt, 12).astype(np.uint32) @ pow12
					pos += 12 * cnt
					a = (v & 15).astype(np.uint8)
					arr[y, x:x + cnt, :3] = pal[v >> 4]
					arr[y, x:x + cnt, 3] = np.where(a > 0, (a << 4) | 15, 0)
				x += cnt
		return Image.fromarray(arr, 'RGBA'), meta

	# BGR(A) -> RGB(A)
	arr = arr[:, :, [2, 1, 0] + ([3] if ch == 4 else [])]
	return Image.fromarray(np.ascontiguousarray(arr), 'RGBA' if ch == 4 else 'RGB'), meta


# 画像出力 (pad: 元のキャンバスサイズに配置 / jpg: 不透明画像をjpgで保存)
def sg_save(b: bytes, out: Path, pad: bool = False, jpg: bool = False):
	im, (ox, oy, cw, ch) = sg_decode(b)
	if pad and (im.width, im.height) != (cw, ch):
		canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
		canvas.paste(im.convert('RGBA'), (ox, oy))
		im = canvas
	if jpg:
		im.convert('RGB').save(out.with_suffix('.jpg'), 'JPEG', quality=90)
	else:
		im.save(out.with_suffix('.png'), 'PNG')
	return


# --- 音声(PX/cTRK)デコード ---

# cTRK -> (PCM(int16 little endian bytes), サンプリングレート, チャンネル数)
def trk_decode(b: bytes):
	o = 8 if b[:4] == b'fPX ' else 0
	h = b[o:o + 0x24]
	hl = struct.unpack_from('<I', h, 0xC)[0]
	dl = struct.unpack_from('<I', h, 4)[0] - hl
	ns = struct.unpack_from('<I', h, 0x10)[0]
	rate = struct.unpack_from('<I', h, 0x14)[0]
	ch = struct.unpack_from('<H', h, 0x1A)[0]
	typ = struct.unpack_from('<H', h, 0x1E)[0]
	data = b[o + hl:o + hl + dl]

	if typ == 0: return data, rate, ch

	nblk = (ns + 27) // 28
	raw = np.frombuffer(data, np.uint8)
	need = nblk * ch * 16
	if raw.size < need: raw = np.concatenate([raw, np.zeros(need - raw.size, np.uint8)])
	raw = raw[:need].reshape(nblk, ch, 16).astype(np.int64)

	first = raw[:, :, 0]
	shift = raw[:, :, 1] >> 4
	fs = raw[:, :, 1] & 15
	hd = first << ((fs & 7) + 1)
	hd = np.where(fs & 8, -hd, hd)

	nib = np.empty((nblk, ch, 28), np.int64)
	nib[:, :, 0::2] = raw[:, :, 2:] >> 4
	nib[:, :, 1::2] = raw[:, :, 2:] & 15
	mag = np.where(nib & 8, ((nib & 7) ^ 7) + 1, nib & 7) << shift[:, :, None]
	delta = np.where(nib & 8, -mag, mag)
	delta[:, :, 0] += hd

	out = np.empty((nblk * 28, ch), np.int64)
	for c in range(ch):
		seq = delta[:, c, :].reshape(-1)
		cs = np.cumsum(seq)
		if cs.size and (cs.min() < -32768 or cs.max() > 32767):
			cs = np.empty_like(seq)
			s = 0
			for i, d in enumerate(seq.tolist()):
				s = max(-32768, min(32767, s + d))
				cs[i] = s
		out[:, c] = cs
	return out[:ns].astype('<i2').tobytes(), rate, ch


# PCM -> ogg
def pcm_to_ogg(ffmpeg: str, pcm: bytes, rate: int, ch: int, out: Path, quality: int):
	subprocess.run(
		[ffmpeg, '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(rate), '-ac', str(ch), '-i', 'pipe:0', '-c:a', 'libvorbis', '-q:a', str(quality), str(out)],
		input=pcm, check=True
	)
	return


# 音声1ファイル変換
def px_to_ogg(ffmpeg: str, b: bytes, out: Path, quality: int):
	pcm, rate, ch = trk_decode(b)
	pcm_to_ogg(ffmpeg, pcm, rate, ch, out, quality)
	return


# --- リソース展開 ---

# ファイル名の正規化 (小文字化/記号除去)
def fname(n: str):
	return unicodedata.normalize('NFKC', Path(n).stem).lower().replace('@', 'x')


# 並列実行(例外はまとめて再送出)
def run_parallel(tasks: list, num_workers: int):
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = [executor.submit(*t) for t in tasks]
		for fu in concurrent.futures.as_completed(futures): fu.result()
	return


# UI用画像の切り出し
def make_ui(input_dir: Path, ui_dir: Path):
	grp = input_dir / 'misc' / 'grp.pk'
	ents = {Path(n).stem.upper(): (o, s) for n, o, s in pk_list(grp)}

	def load(name):
		return sg_decode(pk_read(grp, *ents[name]))

	# タイトル
	im, _ = load('TITLE_BASE')
	im.save(ui_dir / 't.jpg', 'JPEG', quality=92)
	im, _ = load('TITLE_BUTTON')
	for sec, pre in enumerate(['m', 'o', 'g']):
		for i in range(4):
			im.crop((0, sec * 192 + i * 48, 320, sec * 192 + i * 48 + 48)).convert('RGB').save(ui_dir / f'{pre}{i}.jpg', 'JPEG', quality=92)

	# メッセージウィンドウ/待機カーソル
	sg_save(pk_read(grp, *ents['BASE']), ui_dir / 'w')
	load('WAITCURSOR')[0].crop((0, 0, 1200, 20)).save(ui_dir / 'k.png', 'PNG')

	# 音楽室
	im, _ = load('MUSIC_ALL')
	im.crop((0, 0, 640, 480)).convert('RGB').save(ui_dir / 'mu.jpg', 'JPEG', quality=92)
	hov = im.crop((0, 480, 640, 960)).convert('RGB')
	for k in range(11):
		for col, x in enumerate([48, 336]):
			hov.crop((x, 112 + 24 * k, x + 256, 128 + 24 * k)).save(ui_dir / f'mh{k + 11 * col + 1}.png', 'PNG')
	hov.crop((259, 417, 381, 453)).save(ui_dir / 'mh0.png', 'PNG')

	# コンフィグ用背景(タイトル背景からロゴと文字を消して暗くしたもの)
	base, _ = load('TITLE_BASE')
	base = base.convert('RGB')
	base.paste(base.crop((300, 20, 530, 150)), (20, 30))
	base.paste(base.crop((20, 260, 320, 470)).transpose(Image.FLIP_LEFT_RIGHT), (330, 260))
	ImageEnhance.Brightness(base).enhance(0.45).save(ui_dir / 'cf.jpg', 'JPEG', quality=92)
	return


# リソース自動展開 (マルチコンバータ組み込み時にのみ利用)
def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	num_workers = values_ex.get('num_workers') or os.cpu_count() or 4
	input_dir = Path(values['input_dir'])
	pre_converted_dir = Path(pre_converted_dir)

	ffmpeg = shutil.which('ffmpeg')
	if not ffmpeg: raise FileNotFoundError('ffmpegが見つかりません(音声変換に必要です)')

	dirs = {k: Path(pre_converted_dir / k) for k in ['b', 'c', 'm', 's', 'v', 'u', 'n']}
	for p in dirs.values(): p.mkdir(parents=True, exist_ok=True)

	tasks = []

	# 画像
	for pk_name, key, pad, jpg in [('bg', 'b', False, True), ('chr', 'c', True, False)]:
		pk_path = input_dir / 'misc' / f'{pk_name}.pk'
		for n, o, s in pk_list(pk_path):
			tasks.append((lambda pk_path, o, s, out, pad, jpg: sg_save(pk_read(pk_path, o, s), out, pad, jpg), pk_path, o, s, dirs[key] / fname(n), pad, jpg))

	# BGM
	for p in sorted((input_dir / 'music').glob('*.px')):
		tasks.append((lambda p, out: px_to_ogg(ffmpeg, p.read_bytes(), out, 4), p, dirs['m'] / f'{p.stem}.ogg'))

	# SE
	se_pk = input_dir / 'misc' / 'se.pk'
	for n, o, s in pk_list(se_pk):
		tasks.append((lambda o, s, out: px_to_ogg(ffmpeg, pk_read(se_pk, o, s), out, 4), o, s, dirs['s'] / f'{fname(n)}.ogg'))

	# シナリオ(NTK)
	sce_pk = input_dir / 'misc' / 'script.pk'
	for n, o, s in pk_list(sce_pk):
		tasks.append((lambda o, s, out: (open(out, "wb").write(pk_read(sce_pk, o, s))), o, s, dirs['n'] / f'{fname(n)}.NTK'))

	# ボイス
	vo_pk = input_dir / 'voice' / 'voice.pk'
	for n, o, s in pk_list(vo_pk):
		tasks.append((lambda o, s, out: px_to_ogg(ffmpeg, pk_read(vo_pk, o, s), out, 1), o, s, dirs['v'] / f'{fname(n)}.ogg'))

	tasks.append((make_ui, input_dir, dirs['u']))
	run_parallel(tasks, num_workers)
	return


# --- シナリオ(NTK)解析 ---

# 暗号化された各チャンクを復号して取り出す
def ntk_parse(b: bytes):
	p = 8
	res = {}
	while p < len(b):
		cid = b[p:p + 4]
		size, hs = struct.unpack_from('<II', b, p + 4)
		hd = b[p + 12:p + hs]
		body = b[p + hs:p + size]
		if cid == b'cCOD':
			n, key = struct.unpack_from('<II', hd, 0)
			res['cod'] = pk_decrypt(body, key)[:n - 28]
		else:
			res[cid.decode()] = pk_decrypt(body, struct.unpack('<I', hd)[0])
		p += size
	return res


# コード列をレコード(オフセット, 命令, 引数u32のリスト)に分解
def ntk_records(code: bytes):
	p = 0
	out = []
	while p + 4 <= len(code):
		op, ln = struct.unpack_from('<HH', code, p)
		args = struct.unpack_from('<%dI' % ((ln - 4) // 4), code, p + 4)
		out.append((p, op, args, code[p + 4:p + ln]))
		p += ln
	return out


# 文字列取得
def ntk_str(buf: bytes, off: int):
	if off == 0xffffffff: return ''
	return buf[off:buf.index(b'\0', off)].decode('cp932')


# 本文の置換(主人公名など)
def fix_text(s: str):
	return s.replace('\uf8f30', '中田').replace('\uf8f31', '友也')


# 変数名 -> ONS変数
def var_name(raw: bytes):
	kind = raw[:3].decode('latin1')
	n = raw[3]
	if kind == 'FLG' and n <= 69: return f'%{110 + n}'
	if kind == 'HSC' and n <= 9: return f'%{180 + n}'
	if kind == 'STA' and n <= 9: return f'%{190 + n}'
	raise ValueError(f'未対応の変数です: {kind}{n}')


# 命令の比較種別
def cmp_op(t: int):
	return ['==', '!=', '>', '<', '>=', '<='][t]


# 連続する選択肢レコードを1つのメニュー(0x109)にまとめる
def ntk_merge(recs: list):
	merged = []
	i = 0
	while i < len(recs):
		p, op, a, raw = recs[i]
		if op != 0x09:
			merged.append(recs[i])
			i += 1
			continue
		j = i
		while j < len(recs) and recs[j][1] == 0x09: j += 1
		nxt = recs[j][0]
		if j - i == 1: pairs = [(a[2], a[3]), (a[4], a[5])]
		else: pairs = [(g[2][2], g[2][3]) for g in recs[i:j]]
		merged.append((p, 0x109, [(t, nxt if tg == 0xffffffff else tg) for t, tg in pairs], raw))
		i = j
	return merged


# 1シナリオ分をONSスクリプトの行リストへ変換
def convert_one(stem: str, b: bytes, voice_set: set):
	r = ntk_parse(b)
	tex, fnm = r['cTEX'], r['cFNM']
	recs = ntk_merge(ntk_records(r['cod']))

	# ジャンプ先ラベルを先に収集
	targets = set()
	for p, op, a, raw in recs:
		if op == 0x0a and a[0] >> 24 != 0xff: targets.add(a[0])
		elif op == 0x0d and a[3] >> 24 != 0xff: targets.add(a[3])
		elif op == 0x109:
			for t, tg in a:
				if tg >> 24 != 0xff: targets.add(tg)

	def label(t):
		if t >> 24 == 0xff: return f'*{fname(ntk_str(fnm, t & 0xffffff))}'
		return f'*{stem}_{t:x}'

	lines = [f'*{stem}']
	dead = False
	jump_to = label

	for p, op, a, raw in recs:
		if p in targets:
			lines.append(label(p))
			dead = False
		if dead: continue

		match op:
			case 0x01:
				lines.append(fix_text(ntk_str(tex, a[1])) + '\\')

			case 0x02:
				name = fix_text(ntk_str(tex, a[1]))
				text = fix_text(ntk_str(tex, a[2]))
				voice = fname(ntk_str(fnm, a[3]))
				if voice not in voice_set: voice = ''
				lines.append(f'd"{name}","{voice}"')
				lines.append(('「' if text.endswith('」') else '') + text + '\\')

			case 0x03:
				lines.append(f'm"{fname(ntk_str(fnm, a[1]))}"')

			case 0x04:
				lines.append('m""')

			case 0x05:
				lines.append(f'dwave 1,"s/{fname(ntk_str(fnm, a[0]))}.ogg"')

			case 0x06 | 0x15:
				n = fname(ntk_str(fnm, a[0]))
				lines.append(f'b"{n}",{12 if n in ("black", "white") else 10}')

			case 0x3b:
				lines.append('c' + ','.join(f'"{fname(ntk_str(fnm, x))}"' if x != 0xffffffff else '""' for x in a))

			case 0x109:
				opts = [f'"{fix_text(ntk_str(tex, t))}",{jump_to(tg)}' for t, tg in a]
				lines.append('select ' + ','.join(opts))
				dead = True

			case 0x0a:
				lines.append(f'goto {jump_to(a[0])}')
				dead = True

			case 0x0d:
				v = raw[:4]
				val = int(struct.unpack('<f', struct.pack('<I', a[2]))[0])
				if v[:3] == b'FLG' and v[3] == 254:
					# 回想モード用の変数(常に0)なので静的に解決
					ok = eval(f'0 {cmp_op(a[1])} {val}')
					if ok:
						lines.append(f'goto {jump_to(a[3])}')
						dead = True
				else:
					lines.append(f'if {var_name(v)}{cmp_op(a[1])}{val} goto {jump_to(a[3])}')

			case 0x14:
				val = int(struct.unpack('<f', struct.pack('<I', a[2]))[0])
				v = raw[:4]
				if v[:3] in (b'FLG', b'HSC', b'STA'):
					lines.append(f'{"add" if a[1] == 5 else "mov"} {var_name(v)},{val}')

			case 0x10:
				lines.append(f'wait {int(struct.unpack("<f", struct.pack("<I", a[0]))[0]) * 2}')

			case 0x4d:
				lines.append('f')

			case _:
				pass

	return lines


# 全シナリオ変換
def convert_scripts(sen_dir: Path, voice_set: set):
	txt = ''
	for p in sorted(sen_dir.glob('*.NTK')):
		stem = p.stem.lower()
		if stem == 'start': continue
		lines = convert_one(stem, p.read_bytes(), voice_set)
		if stem == 'ending': lines = [lines[0], 'm""', 'b"black",12', 'wait 1500', 'reset']
		txt += '\n'.join(lines) + '\n'
	return txt


# シナリオが開始から最後まで繋がっているか、フラグの値を追いながら簡易チェック
def check_flow(sen_dir: Path):
	scripts = {}
	for p in sorted(sen_dir.glob('*.NTK')):
		r = ntk_parse(p.read_bytes())
		recs = ntk_merge(ntk_records(r['cod']))
		scripts[fname(p.stem)] = (recs, {rec[0]: i for i, rec in enumerate(recs)}, r['cFNM'])

	# 1シナリオ内を全分岐たどり、出口(次のシナリオ, フラグ)の集合を返す
	def run(stem, flags):
		recs, index, fnm = scripts[stem]
		exits = set()
		seen = set()
		todo = [(0, flags)]

		def go(t, fl):
			if t >> 24 == 0xff:
				nxt = fname(ntk_str(fnm, t & 0xffffff))
				if nxt != 'start' and nxt not in scripts: raise ValueError(f'{stem}の飛び先{nxt}が存在しません')
				exits.add((nxt, fl))
			else:
				todo.append((index[t], fl))

		while todo:
			i, fl = todo.pop()
			if (i, fl) in seen: continue
			seen.add((i, fl))
			if i >= len(recs): raise ValueError(f'{stem}が飛び先なしで終わっています(フラグ: {dict(fl)})')
			p, op, a, raw = recs[i]
			d = dict(fl)
			key = raw[:4]
			match op:
				case 0x0a:
					go(a[0], fl)
				case 0x109:
					for t, tg in a: go(tg, fl)
				case 0x0d:
					val = int(struct.unpack('<f', struct.pack('<I', a[2]))[0])
					cur = 0 if key == b'FLG\xfe' else d.get(key, 0)
					if eval(f'{cur} {cmp_op(a[1])} {val}'): go(a[3], fl)
					else: todo.append((i + 1, fl))
				case 0x14:
					val = int(struct.unpack('<f', struct.pack('<I', a[2]))[0])
					d[key] = d.get(key, 0) + val if a[1] == 5 else val
					todo.append((i + 1, tuple(sorted(d.items()))))
				case _:
					todo.append((i + 1, fl))
		return exits

	entries = {('na01a0', ())}
	todo = [('na01a0', ())]
	edges = {}
	while todo:
		e = todo.pop()
		if e[0] in ('ending', 'start'): continue
		edges[e] = run(*e)
		for x in edges[e]:
			if x not in entries:
				entries.add(x)
				todo.append(x)

	# 全状態からエンディングへ到達できるか
	ok = {e for e in entries if e[0] == 'ending'}
	changed = True
	while changed:
		changed = False
		for e, xs in edges.items():
			if e not in ok and any(x in ok for x in xs):
				ok.add(e)
				changed = True
	bad = [e for e in entries if e not in ok]
	if not any(e[0] == 'ending' for e in entries): raise ValueError('開始からエンディングまで到達できません')
	if bad: raise ValueError(f'エンディングへ到達できない状態があります: {bad[:3]}')
	return


# 0.txt内のラベル参照がすべて定義済みか確認
def check_labels(txt: str):
	defined = set(re.findall(r'^\*([0-9A-Za-z_]+)', txt, re.M))
	used = set(re.findall(r'(?:goto|gosub|,)\s*\*([0-9A-Za-z_]+)', txt))
	missing = sorted(used - defined)
	if missing: raise ValueError(f'未定義のラベルがあります: {missing[:10]}')
	return


# ステータス変数の初期化命令(新規ゲーム開始時)
def clear_vars():
	nums = list(range(110, 170)) + list(range(180, 200))
	return '\n'.join(':'.join(f'mov %{n},0' for n in nums[i:i + 10]) for i in range(0, len(nums), 10))


# 0.txtにはじめから書いておくもの
def default_txt(txt: str, cg_names: list):

	# 音楽室
	mu_spr = ''.join(f'lsph {100 + k},"u/mh{k}.png",{[48, 336][(k - 1) // 11]}/%100,{112 + 24 * ((k - 1) % 11)}/%100\n' for k in range(1, 23))
	mu_spr += 'lsph 100,"u/mh0.png",259/%100,417/%100\n'
	mu_btn = 'exbtn_d "' + ''.join(f'C{100 + k}' for k in range(23)) + '"\n'
	for k in range(23):
		mu_btn += f'exbtn {100 + k},{100 + k},"' + ''.join(f'{"P" if j == k else "C"}{100 + j}' for j in range(23)) + '"\n'

	# CG閲覧
	cg_if = '\n'.join(f'\tif %1=={i} mov $1,"{n}"' for i, n in enumerate(cg_names))

	return f'''*define

caption "夏色小町 for ONScripter"

rmenu "セーブ",save,"ロード",load,"ログ",lookback,"スキップ",skip,"タイトルへ戻る",reset
savename "セーブ","ロード","データ"
savenumber 15
menusetwindow 22,22,0,8,0,1,#445588
selectcolor #ffffff,#aaddff
transmode alpha
globalon
rubyon
saveon
windowback
humanz 10

numalias aud_bgm,1400
numalias aud_se,1401
numalias aud_vo,1402

effect 10,10,400
effect 11,10,150
effect 12,10,700

pretextgosub *pt

defsub d
defsub b
defsub c
defsub m
defsub f
game
;----------------------------------------
*d
	getparam $10,$11
return
;----------------------------------------
*b
	getparam $0,%0
	vsp 1,0:csp 20:csp 21:csp 22:mov $41,"":mov $42,"":mov $43,""
	lsp 30,":c;b/"+$0+".jpg",0,0:print %0
return
;----------------------------------------
*c
	getparam $0,$1,$2
	if $0!=$41 mov $41,$0:csp 20:if $0!="" lsp 20,"c/"+$0+".png",-128/%100,0
	if $1!=$42 mov $42,$1:csp 21:if $1!="" lsp 21,"c/"+$1+".png",0,0
	if $2!=$43 mov $43,$2:csp 22:if $2!="" lsp 22,"c/"+$2+".png",128/%100,0
	print 11
return
;----------------------------------------
*m
	getparam $0
	if $0=="" bgmstop:mov $44,"":return
	if $0!=$44 bgm "m/"+$0+".ogg":mov $44,$0
return
;----------------------------------------
*f
	lsp 2,":c;b/white.jpg",0,0:print 11:csp 2:print 11
return
;----------------------------------------
*pt
	dwavestop 0
	if $10=="" vsp 1,0
	if $10!="" lsp 1,":s/22,22,0;#ffffff"+$10,88/%100,346/%100
	if $11!="" dwave 0,"v/"+$11+".ogg"
	mov $10,"":mov $11,""
	saveon
return
;----------------------------------------
*start
	mov %100,2
	lsp 30,":c;u/t.jpg",0,0
	getspsize 30,%99,%98
	if %99==640 mov %100,1
	csp 30
	mov $44,""
	fileexist %90,"gloval.sav"
	if %90==0 if %aud_bgm==0 if %aud_se==0 if %aud_vo==0 mov %aud_bgm,100:mov %aud_se,100:mov %aud_vo,100
	bgmvol %aud_bgm
	sevol %aud_se
	voicevol %aud_vo

	setwindow 88/%100,372/%100,21,3,22/%100,22/%100,0,8/%100,20,0,1,"u/w.png",21/%100,336/%100
	abssetcursor 1,":a/60,30,2;u/k.png",524/%100,442/%100
;----------------------------------------
*title
	csp -1:mov $41,"":mov $42,"":mov $43,""
	lsp 200,":c;u/t.jpg",0,0
	lsph 41,":c;u/m0.jpg",320/%100,272/%100
	lsph 42,":c;u/m1.jpg",320/%100,320/%100
	lsph 43,":c;u/m2.jpg",320/%100,368/%100
	lsph 44,":c;u/m3.jpg",320/%100,416/%100
	lsp 45,":s/22,22,0;#335599コンフィグ",24/%100,440/%100
	spbtn 45,45
	m"01"
	print 10
*tl
	bclear
	exbtn_d "C41C42C43C44"
	exbtn 41,41,"P41C42C43C44"
	exbtn 42,42,"C41P42C43C44"
	exbtn 43,43,"C41C42P43C44"
	exbtn 44,44,"C41C42C43P44"
	spbtn 45,45
	btnwait %20
	if %20==41 goto *ng
	if %20==42 systemcall load
	if %20==43 goto *omake
	if %20==44 bgmstop:csp -1:print 12:end
	if %20==45 goto *cfg
goto *tl
;----------------------------------------
*ng
	bgmstop:mov $44,""
	csp -1:print 12
{clear_vars()}
	goto *na01a0
;----------------------------------------
*omake
	csp -1
	lsp 200,":c;u/t.jpg",0,0
	lsp 51,":c;u/o0.jpg",320/%100,272/%100
	lsp 52,":c;u/o1.jpg",320/%100,320/%100
	lsp 53,":c;u/o2.jpg",320/%100,368/%100
	lsp 54,":c;u/o3.jpg",320/%100,416/%100
	lsph 61,":c;u/g0.jpg",320/%100,272/%100
	lsph 62,":c;u/g1.jpg",320/%100,320/%100
	lsph 63,":c;u/g2.jpg",320/%100,368/%100
	lsph 64,":c;u/g3.jpg",320/%100,416/%100
	vsp 45,0
	print 1
*ol
	bclear
	exbtn_d "C61C62C63C64"
	exbtn 61,61,"P61C62C63C64"
	exbtn 62,62,"C61P62C63C64"
	exbtn 63,63,"C61C62P63C64"
	exbtn 64,64,"C61C62C63P64"
	btnwait %20
	if %20==61 goto *cgv
	if %20==63 goto *mus
	if %20==64 goto *title
goto *ol
;----------------------------------------
*cgv
	csp -1:mov %1,0
*cgl
{cg_if}
	lsp 30,":c;b/"+$1+".jpg",0,0:print 10
	bclear
	spbtn 30,1
	btnwait %2
	if %2==-1 goto *omake
	add %1,1
	if %1=={len(cg_names)} mov %1,0
goto *cgl
;----------------------------------------
*mus
	csp -1
	lsp 200,":c;u/mu.jpg",0,0
{mu_spr}	print 1
*ml
	bclear
{mu_btn}	btnwait %20
	if %20==100 bgmstop:mov $44,"":goto *omake
	mov %21,0
	if %20>100 if %20<=122 mov %21,1
	if %21==1 sub %20,100:itoa $5,%20
	if %21==1 if %20<10 mov $5,"0"+$5
	if %21==1 bgm "m/"+$5+".ogg":mov $44,$5
goto *ml
;----------------------------------------
*cfg
	csp -1
	lsp 200,":c;u/cf.jpg",0,0
	print 1
*cl
	itoa2 $41,%aud_bgm
	itoa2 $42,%aud_se
	itoa2 $43,%aud_vo
	lsp 130,":s/24,24,0;#ffffffコンフィグ",40/%100,40/%100
	lsp 131,":s/22,22,0;#ffffffＢＧＭ",40/%100,120/%100
	lsp 132,":s/22,22,0;#ffffff＜",200/%100,120/%100
	lsp 133,":s/22,22,0;#ffffff＞",360/%100,120/%100
	lsp 134,":s/22,22,0;#ffffff"+$41,420/%100,120/%100
	lsp 135,":s/22,22,0;#ffffffＳＥ",40/%100,200/%100
	lsp 136,":s/22,22,0;#ffffff＜",200/%100,200/%100
	lsp 137,":s/22,22,0;#ffffff＞",360/%100,200/%100
	lsp 138,":s/22,22,0;#ffffff"+$42,420/%100,200/%100
	lsp 139,":s/22,22,0;#ffffffボイス",40/%100,280/%100
	lsp 140,":s/22,22,0;#ffffff＜",200/%100,280/%100
	lsp 141,":s/22,22,0;#ffffff＞",360/%100,280/%100
	lsp 142,":s/22,22,0;#ffffff"+$43,420/%100,280/%100
	lsp 143,":s/22,22,0;#ffffffもどる",400/%100,400/%100
	print 1
	bclear
	spbtn 132,132
	spbtn 133,133
	spbtn 136,136
	spbtn 137,137
	spbtn 140,140
	spbtn 141,141
	spbtn 143,143
	btnwait %20
	if %20==132 if %aud_bgm!=0 sub %aud_bgm,10
	if %20==133 if %aud_bgm!=100 add %aud_bgm,10
	if %20==136 if %aud_se!=0 sub %aud_se,10
	if %20==137 if %aud_se!=100 add %aud_se,10
	if %20==140 if %aud_vo!=0 sub %aud_vo,10
	if %20==141 if %aud_vo!=100 add %aud_vo,10
	bgmvol %aud_bgm
	sevol %aud_se
	voicevol %aud_vo
	if %20==143 goto *title
goto *cl
;----------------------------------------
{txt}
'''


# メイン処理関数 ※pre_converted_dir→今までのコンバータのsame_hierarchy
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	pre_converted_dir = Path(pre_converted_dir)

	# マルチコンバータ利用時/入力指定時は自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	# シナリオ変換
	voice_set = {p.stem for p in (pre_converted_dir / 'v').glob('*.ogg')}
	sen_dir = Path(pre_converted_dir) / 'n'
	txt = convert_scripts(sen_dir, voice_set)
	check_flow(sen_dir)

	# CG閲覧用リスト
	cg_names = sorted(p.stem for p in (pre_converted_dir / 'b').glob('*.jpg') if re.fullmatch(r'(mk|mo|ng|ss|sz)_[0-9a-z_]+', p.stem) and not (p.stem[:2] == 'ng' and p.stem.endswith('x')) and not p.stem.endswith('pt'))

	# 0.txt書込み
	txt = default_txt(txt, cg_names)
	check_labels(txt)
	with open(pre_converted_dir / '0.txt', 'w', encoding='cp932') as f: f.write(txt)

	return


# 単体動作: python Ariga2ONS.py <input_dir> <pre_converted_dir>
if __name__ == "__main__":
	main({'input_dir': Path(sys.argv[1])}, {}, Path(sys.argv[2]))
