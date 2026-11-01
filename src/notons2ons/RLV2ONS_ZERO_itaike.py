#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import concurrent.futures
import numpy as np
import soundfile as sf
import os, re, shutil, struct, unicodedata


# 作品について
def title_info():
	return {
		'brand': 'ZERO',
		'date': 20031024,
		'title': 'いたいけな彼女 ～いじめられっ子物語～',
		'cli_arg': 'zero_itaike',
		'requiredsoft': [],
		'is_4:3': True,
		'exe_name': ['REALLIVE'],

		'version': [
			'いたいけな彼女 パッケージ版',
			'いじめられっ子物語 ～いたいけな彼女～ DLsite DL版',
		],

		'notes': [
			'画面遷移は全てフェードで代用',
			'画面特殊効果は簡略化',
			'セーブ、ロード、設定画面は簡略化',
			'CG/音楽/回想モードは未実装',
			'選択肢はメッセージウィンドウ内に表示',
		]
	}


# ----------------------------------------------------------------------------
# 入力フォルダの解決(パッケージ版/DL版でフォルダ名・大文字小文字が異なる)
# ----------------------------------------------------------------------------

# 大文字小文字を区別せずにパスを辿る
def ci_path(base, *names):
	p = Path(base)
	for n in names:
		hit = p / n
		if not hit.exists() and p.is_dir():
			hit = next((c for c in p.iterdir() if c.name.lower() == n.lower()), hit)
		p = hit
	return p


# SEEN.TXTとGAMEEXE.INIがあるフォルダ(ゲームデータの根)を探す
def find_game_root(input_dir, depth=3):
	def is_root(p):
		return ci_path(p, 'SEEN.TXT').is_file() and ci_path(p, 'GAMEEXE.INI').is_file()

	def walk(p, d):
		if is_root(p):
			return [p]
		if d == 0:
			return []
		r = []
		for c in sorted(p.iterdir()):
			if c.is_dir():
				r += walk(c, d - 1)
		return r

	found = walk(Path(input_dir), depth)
	if len(found) != 1:
		raise RuntimeError(
			'ゲームデータ(SEEN.TXTとGAMEEXE.INIがあるフォルダ)を1つに特定できません\n'
			+ '\n'.join(f'  {p}' for p in found)
		)
	return found[0]


# ----------------------------------------------------------------------------
# RealLive(SEEN.TXT)解析
# ----------------------------------------------------------------------------

# RealLive第一段階XOR鍵
def rl_xor_key():
	return bytes([
		0x8b, 0xe5, 0x5d, 0xc3, 0xa1, 0xe0, 0x30, 0x44, 0x00, 0x85, 0xc0, 0x74, 0x09, 0x5f, 0x5e, 0x33, 0xc0, 0x5b, 0x8b, 0xe5, 0x5d, 0xc3, 0x8b, 0x45,
		0x0c, 0x85, 0xc0, 0x75, 0x14, 0x8b, 0x55, 0xec, 0x83, 0xc2, 0x20, 0x52, 0x6a, 0x00, 0xe8, 0xf5, 0x28, 0x01, 0x00, 0x83, 0xc4, 0x08, 0x89, 0x45,
		0x0c, 0x8b, 0x45, 0xe4, 0x6a, 0x00, 0x6a, 0x00, 0x50, 0x53, 0xff, 0x15, 0x34, 0xb1, 0x43, 0x00, 0x8b, 0x45, 0x10, 0x85, 0xc0, 0x74, 0x05, 0x8b,
		0x4d, 0xec, 0x89, 0x08, 0x8a, 0x45, 0xf0, 0x84, 0xc0, 0x75, 0x78, 0xa1, 0xe0, 0x30, 0x44, 0x00, 0x8b, 0x7d, 0xe8, 0x8b, 0x75, 0x0c, 0x85, 0xc0,
		0x75, 0x44, 0x8b, 0x1d, 0xd0, 0xb0, 0x43, 0x00, 0x85, 0xff, 0x76, 0x37, 0x81, 0xff, 0x00, 0x00, 0x04, 0x00, 0x6a, 0x00, 0x76, 0x43, 0x8b, 0x45,
		0xf8, 0x8d, 0x55, 0xfc, 0x52, 0x68, 0x00, 0x00, 0x04, 0x00, 0x56, 0x50, 0xff, 0x15, 0x2c, 0xb1, 0x43, 0x00, 0x6a, 0x05, 0xff, 0xd3, 0xa1, 0xe0,
		0x30, 0x44, 0x00, 0x81, 0xef, 0x00, 0x00, 0x04, 0x00, 0x81, 0xc6, 0x00, 0x00, 0x04, 0x00, 0x85, 0xc0, 0x74, 0xc5, 0x8b, 0x5d, 0xf8, 0x53, 0xe8,
		0xf4, 0xfb, 0xff, 0xff, 0x8b, 0x45, 0x0c, 0x83, 0xc4, 0x04, 0x5f, 0x5e, 0x5b, 0x8b, 0xe5, 0x5d, 0xc3, 0x8b, 0x55, 0xf8, 0x8d, 0x4d, 0xfc, 0x51,
		0x57, 0x56, 0x52, 0xff, 0x15, 0x2c, 0xb1, 0x43, 0x00, 0xeb, 0xd8, 0x8b, 0x45, 0xe8, 0x83, 0xc0, 0x20, 0x50, 0x6a, 0x00, 0xe8, 0x47, 0x28, 0x01,
		0x00, 0x8b, 0x7d, 0xe8, 0x89, 0x45, 0xf4, 0x8b, 0xf0, 0xa1, 0xe0, 0x30, 0x44, 0x00, 0x83, 0xc4, 0x08, 0x85, 0xc0, 0x75, 0x56, 0x8b, 0x1d, 0xd0,
		0xb0, 0x43, 0x00, 0x85, 0xff, 0x76, 0x49, 0x81, 0xff, 0x00, 0x00, 0x04, 0x00, 0x6a, 0x00, 0x76,
	])


# LZ展開(スクリプト用)
def rl_decompress(src, dlen):
	xk = rl_xor_key()
	out = bytearray()
	p = 8
	mask = 8
	flag = src[p] ^ xk[mask & 255]
	p += 1
	mask += 1
	bit = 1
	n = len(src)
	while p < n and len(out) < dlen:
		if bit == 256:
			bit = 1
			flag = src[p] ^ xk[mask & 255]
			p += 1
			mask += 1
		if flag & bit:
			out.append(src[p] ^ xk[mask & 255])
			p += 1
			mask += 1
		else:
			c = src[p] ^ xk[mask & 255]
			p += 1
			mask += 1
			c += (src[p] ^ xk[mask & 255]) << 8
			p += 1
			mask += 1
			rep = len(out) - ((c >> 4) - 1) - 1
			cnt = (c & 15) + 2
			for _ in range(cnt):
				out.append(out[rep])
				rep += 1
		bit <<= 1
	return bytes(out)


# SEEN.TXTからシーン番号→生データの辞書を作成
def rl_load_seen(path):
	d = Path(path).read_bytes()
	sc = {}
	for i in range(10000):
		o, l = struct.unpack_from('<ii', d, i * 8)
		if o:
			sc[i] = d[o:o + l]
	return sc


# シーン1本を展開してバイトコード要素列にする
def rl_parse_scene(data):
	kid_off, kid_n = struct.unpack_from('<ii', data, 8)
	kid = [struct.unpack_from('<i', data, kid_off + i * 4)[0] for i in range(kid_n)]
	boff, dlen, clen = struct.unpack_from('<iii', data, 0x20)
	code = rl_decompress(data[boff:boff + clen], dlen)
	return rl_parse_code(code, kid)


class RLPos:
	def __init__(self, b, i=0):
		self.b = b
		self.i = i


def rl_is_lead(c):
	return 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xef


def rl_e_token(p):
	b = p.b
	c = b[p.i]
	if c == 0xff:
		v = struct.unpack_from('<i', b, p.i + 1)[0]
		p.i += 5
		return ('int', v)
	if c == 0xc8:
		p.i += 1
		return ('store',)
	if b[p.i + 1] == 0x5b:
		p.i += 2
		loc = rl_e_expr(p)
		if b[p.i] != 0x5d:
			raise ValueError('不正なメモリ参照')
		p.i += 1
		return ('mem', c, loc)
	raise ValueError('不正な式トークン')


def rl_e_term(p):
	b = p.b
	c = b[p.i]
	if c == 0x24:
		p.i += 1
		return rl_e_token(p)
	if c == 0x5c and b[p.i + 1] == 0:
		p.i += 2
		return rl_e_term(p)
	if c == 0x5c and b[p.i + 1] == 1:
		p.i += 2
		return ('neg', rl_e_term(p))
	if c == 0x28:
		p.i += 1
		r = rl_e_expr(p)
		if b[p.i] != 0x29:
			raise ValueError('不正な括弧')
		p.i += 1
		return r
	raise ValueError('不正な式項')


def rl_e_arith_hi(p, tok):
	b = p.b
	while b[p.i] == 0x5c and 2 <= b[p.i + 1] <= 9:
		op = b[p.i + 1]
		p.i += 2
		tok = ('bin', op, tok, rl_e_term(p))
	return tok


def rl_e_arith(p):
	b = p.b
	tok = rl_e_arith_hi(p, rl_e_term(p))
	while b[p.i] == 0x5c and b[p.i + 1] in (0, 1):
		op = b[p.i + 1]
		p.i += 2
		tok = ('bin', op, tok, rl_e_arith_hi(p, rl_e_term(p)))
	return tok


def rl_e_cond(p):
	b = p.b
	tok = rl_e_arith(p)
	while b[p.i] == 0x5c and 0x28 <= b[p.i + 1] <= 0x2d:
		op = b[p.i + 1]
		p.i += 2
		tok = ('bin', op, tok, rl_e_arith(p))
	return tok


def rl_e_expr(p):
	b = p.b
	tok = rl_e_cond(p)
	while b[p.i] == 0x5c and b[p.i + 1] == 0x3c:
		p.i += 2
		tok = ('bin', 0x3c, tok, rl_e_cond(p))
	while b[p.i] == 0x5c and b[p.i + 1] == 0x3d:
		p.i += 2
		rhs = rl_e_cond(p)
		while b[p.i] == 0x5c and b[p.i + 1] == 0x3c:
			p.i += 2
			rhs = ('bin', 0x3c, rhs, rl_e_cond(p))
		tok = ('bin', 0x3d, tok, rhs)
	return tok


def rl_e_assign(p):
	it = rl_e_term(p)
	op = p.b[p.i + 1]
	p.i += 2
	et = rl_e_expr(p)
	if not 0x14 <= op <= 0x24:
		raise ValueError('不正な代入演算子')
	return ('bin', op, it, et)


def rl_string_len(b, i):
	quoted = False
	s = i
	e = i
	while True:
		if quoted:
			q = b[e] == 0x22 and (e == s or b[e - 1] != 0x5c)
			quoted = not q
			if not quoted and b[e - 1] != 0x5c:
				e += 1
				break
		else:
			quoted = b[e] == 0x22 and (e == s or b[e - 1] != 0x5c)
			if b[e:e + 9] == b'###PRINT(':
				e += 9
				p = RLPos(b, e)
				rl_e_expr(p)
				e = p.i + 1
				continue
			c = b[e]
			if not (rl_is_lead(c) or 0x61 <= c <= 0x7a or 0x41 <= c <= 0x5a or 0x30 <= c <= 0x39 or c in (0x20, 0x3f, 0x5f, 0x22, 0x5c)):
				break
		if rl_is_lead(b[e]):
			e += 2
		else:
			e += 1
	return e - i


def rl_e_string(p):
	b = p.b
	n = rl_string_len(b, p.i)
	raw = b[p.i:p.i + n]
	if raw[:1] == b'"':
		raw = raw[1:-1]
	p.i += n
	return ('str', raw.replace(b'\\"', b'"'))


def rl_e_data(p):
	b = p.b
	c = b[p.i]
	if c == 0x2c:
		p.i += 1
		return rl_e_data(p)
	if c == 0x0a:
		p.i += 3
		return rl_e_data(p)
	if rl_is_lead(c) or 0x41 <= c <= 0x5a or 0x30 <= c <= 0x39 or c in (0x20, 0x3f, 0x5f, 0x22) or b[p.i:p.i + 9] == b'###PRINT(':
		return rl_e_string(p)
	if c == 0x61:
		e = p.i + 1
		tag = b[e]
		e += 1
		if b[e] == 0x61:
			e += 1
			tag = (b[e] << 16) | tag
			e += 1
		pieces = []
		q = RLPos(b, e)
		if b[e] != 0x28:
			pieces.append(rl_e_data(q))
			p.i = q.i
			return ('special', tag, pieces)
		q.i += 1
		while b[q.i] != 0x29:
			pieces.append(rl_e_data(q))
		q.i += 1
		p.i = q.i
		return ('special', tag, pieces)
	if c == 0x28:
		q = RLPos(b, p.i + 1)
		pieces = []
		while b[q.i] != 0x29:
			pieces.append(rl_e_data(q))
		q.i += 1
		if b[q.i] == 0x5c:
			rl_e_expr(q)
		p.i = q.i
		return ('complex', pieces)
	return rl_e_expr(p)


def rl_params(b, i):
	params = []
	if b[i] != 0x28:
		return params, i
	p = RLPos(b, i + 1)
	while b[p.i] != 0x29:
		params.append(rl_e_data(p))
	p.i += 1
	return params, p.i


def rl_parse_code(code, kid):
	els = []
	pos = 0
	n = len(code)
	marker = 0x40
	while pos < n:
		c = code[pos]
		off = pos
		if c == 0x21:
			marker = 0x21
		if c == 0 or c == 0x2c:
			els.append((off, 'comma', None))
			pos += 1
			continue
		if c == 0x0a:
			els.append((off, 'line', struct.unpack_from('<H', code, pos + 1)[0]))
			pos += 3
		elif c == 0x40 or c == 0x21:
			v = struct.unpack_from('<H', code, pos + 1)[0]
			k = kid[v]
			els.append((off, 'entry', k - 1000000) if k >= 1000000 else (off, 'kidoku', v))
			pos += 3
		elif c == 0x24:
			p = RLPos(code, pos)
			els.append((off, 'expr', rl_e_assign(p)))
			pos = p.i
		elif c == 0x23:
			e, pos = rl_parse_cmd(code, pos)
			els.append((off,) + e)
		else:
			e = pos
			quoted = False
			while e < n:
				if quoted:
					quoted = code[e] != 0x22
					if code[e] == 0x5c and code[e + 1] == 0x22:
						e += 1
				else:
					if code[e] == 0x2c:
						e += 1
					quoted = code[e] == 0x22
					if code[e] in (0, 0x23, 0x24, 0x0a, 0x40) or code[e] == marker:
						break
				e += 2 if rl_is_lead(code[e]) else 1
			els.append((off, 'text', code[pos:e]))
			pos = e
	return els


def rl_parse_cmd(code, pos):
	mt, mod = code[pos + 1], code[pos + 2]
	opc = code[pos + 3] | (code[pos + 4] << 8)
	argc = code[pos + 5] | (code[pos + 6] << 8)
	ov = code[pos + 7]
	key = (mt, mod, opc, ov)
	k32 = (mt << 24) | (mod << 16) | (code[pos + 4] << 8) | code[pos + 3]
	i = pos + 8
	if k32 in (0x00010000, 0x00010005, 0x00050001, 0x00050005, 0x00060001, 0x00060005):
		return ('goto', key, struct.unpack_from('<i', code, i)[0]), i + 4
	if k32 in (0x00010001, 0x00010002, 0x00010006, 0x00010007, 0x00050002, 0x00050006, 0x00050007, 0x00060000, 0x00060002, 0x00060006, 0x00060007):
		p = RLPos(code, i + 1)
		ex = rl_e_expr(p)
		return ('gotoif', key, ex, struct.unpack_from('<i', code, p.i + 1)[0]), p.i + 5
	if k32 in (0x00010003, 0x00010008, 0x00050003, 0x00050008, 0x00060003, 0x00060008):
		p = RLPos(code, i)
		ex = rl_e_expr(p)
		p.i += 1
		ts = []
		for _ in range(argc):
			ts.append(struct.unpack_from('<i', code, p.i)[0])
			p.i += 4
		return ('goto_on', key, ex, ts), p.i + 1
	if k32 in (0x00010004, 0x00010009, 0x00050004, 0x00050009, 0x00060004, 0x00060009):
		p = RLPos(code, i)
		ex = rl_e_expr(p)
		p.i += 1
		cases = []
		for _ in range(argc):
			if code[p.i + 1] == 0x29:
				ce = None
				p.i += 2
			else:
				p.i += 1
				ce = rl_e_expr(p)
				p.i += 1
			cases.append((ce, struct.unpack_from('<i', code, p.i)[0]))
			p.i += 4
		return ('goto_case', key, ex, cases), p.i + 1
	if k32 in (0x00010010, 0x00060010):
		params, j = rl_params(code, i)
		return ('gosub_with', key, params, struct.unpack_from('<i', code, j)[0]), j + 4
	if k32 in (0x00020000, 0x00020001, 0x00020002, 0x00020003, 0x00020010):
		return rl_parse_select(code, pos, key, argc)
	params, j = rl_params(code, i)
	return ('cmd', key, params), j


def rl_parse_select(code, pos, key, argc):
	i = pos + 8
	win = None
	if code[i] == 0x28:
		p = RLPos(code, i + 1)
		win = rl_e_expr(p)
		i = p.i + 1
	i += 1
	if code[i] == 0x0a:
		i += 3
	opts = []
	for _ in range(argc):
		while code[i] == 0x2c:
			i += 1
		conds = []
		if code[i] == 0x28:
			i += 1
			while code[i] != 0x29:
				cond = None
				if code[i] == 0x28:
					p = RLPos(code, i)
					cond = rl_e_expr(p)
					i = p.i
				seek = code[i] not in (0x32, 0x33)
				eff = chr(code[i])
				i += 1
				arg = None
				if seek and code[i] != 0x29 and not 0x30 <= code[i] <= 0x39:
					p = RLPos(code, i)
					arg = rl_e_expr(p)
					i = p.i
				conds.append((cond, eff, arg))
			i += 1
		n = rl_string_len(code, i)
		opts.append((conds, code[i:i + n]))
		i += n + 3
	while code[i] == 0x0a:
		i += 3
	return ('select', key, win, opts), i + 1


# ----------------------------------------------------------------------------
# PDT(画像)展開
# ----------------------------------------------------------------------------

def pdt_lz(src, p, pend, count, kind, idx_table=None):
	unit = 4 if kind == 'pdt10' else 1
	end = count * unit
	out = bytearray()
	while len(out) < end and p < pend:
		flag = src[p]
		p += 1
		for _ in range(8):
			if len(out) >= end or p >= pend:
				break
			if flag & 0x80:
				if kind == 'pdt10':
					out += src[p:p + 3]
					out.append(0)
					p += 3
				else:
					out.append(src[p])
					p += 1
			else:
				if kind == 'pdt10':
					d = src[p] | (src[p + 1] << 8)
					p += 2
					size = (d & 15) + 1
					dist = (d >> 4) + 1
				elif kind == 'pdt11':
					d = src[p]
					p += 1
					size = (d >> 4) + 2
					dist = idx_table[d & 15]
				else:
					d = src[p] | (src[p + 1] << 8)
					p += 2
					size = (d & 255) + 2
					dist = (d >> 8) + 1
				bs = dist * unit
				nb = size * unit
				st = len(out) - bs
				if bs >= nb:
					out += out[st:st + nb]
				else:
					for k in range(nb):
						out.append(out[st + k])
			flag = (flag << 1) & 0xff
	return out


# PDT10/PDT11をRGBA画像にする
def pdt_decode(data):
	w, h = struct.unpack_from('<ii', data, 0x0c)
	mask_pt = struct.unpack_from('<i', data, 0x1c)[0]
	n = w * h
	end = mask_pt or len(data)
	if data[:5] == b'PDT10':
		buf = bytes(pdt_lz(data, 0x20, end, n, 'pdt10')[:n * 4])
	else:
		idx_table = [struct.unpack_from('<i', data, 0x420 + i * 4)[0] for i in range(16)]
		idx = pdt_lz(data, 0x460, end, n, 'pdt11', idx_table)
		pal = [data[0x20 + i * 4:0x20 + i * 4 + 3] + b'\x00' for i in range(256)]
		buf = b''.join(pal[b] for b in idx[:n])
	im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
	if mask_pt:
		m = pdt_lz(data, mask_pt, len(data), n, 'mask')
		im.putalpha(Image.frombuffer('L', (w, h), bytes(m[:n]), 'raw', 'L', 0, 1))
	else:
		im.putalpha(255)
	return im


# ----------------------------------------------------------------------------
# NWA/NWK(音声)展開
# ----------------------------------------------------------------------------

def nwa_header(buf, off):
	ch, bps, freq, comp, rl, blocks, datasize, compsize, samples, blocksize, restsize = struct.unpack_from('<hhiiiiiiiii', buf, off)
	return {'ch': ch, 'bps': bps, 'freq': freq, 'comp': comp, 'rl': rl, 'blocks': blocks, 'datasize': datasize, 'compsize': compsize, 'blocksize': blocksize, 'off': off}


# 全ブロックを一括で(ブロック方向にベクトル化して)展開
def nwa_decode_blocks(D, bases, ch, comp, rl, blocksize):
	nb = len(bases)
	cur = [np.zeros(nb, dtype=np.int32), np.zeros(nb, dtype=np.int32)]
	for c in range(ch):
		v = (D[bases + 2 * c] | (D[bases + 2 * c + 1] << 8)).astype(np.int32)
		cur[c] = np.where(v >= 32768, v - 65536, v)
	bp = (bases + 2 * ch) * 8
	run = np.zeros(nb, dtype=np.int32)
	out = np.empty((nb, blocksize), dtype=np.int16)
	if comp >= 3:
		b1, s1, b7, s7 = comp + 3, 1, 8, 9
	else:
		b1, s1, b7, s7 = 5 - comp, 2 + comp, 8 - comp, 9 + comp
	m1, top1, mk1 = (1 << (b1 - 1)) - 1, 1 << (b1 - 1), (1 << b1) - 1
	m7, top7, mk7 = (1 << (b7 - 1)) - 1, 1 << (b7 - 1), (1 << b7) - 1
	for s in range(blocksize):
		fl = (s & 1) if ch == 2 else 0
		need = run == 0
		i0 = bp >> 3
		w = (D[i0] | (D[i0 + 1] << 8) | (D[i0 + 2] << 16)) >> (bp & 7)
		t = w & 7
		b = (w >> 3) & mk1
		mag = (b & m1) << (s1 + t)
		d_n = np.where((b & top1) != 0, -mag, mag)
		isn = need & (t >= 1) & (t <= 6)
		bb = (w >> 4) & mk7
		mag7 = (bb & m7) << s7
		d_7 = np.where((bb & top7) != 0, -mag7, mag7)
		is7 = need & (t == 7)
		z7 = is7 & (((w >> 3) & 1) == 1)
		d7 = is7 & (((w >> 3) & 1) == 0)
		is0 = need & (t == 0)
		nc = cur[fl] + np.where(isn, d_n, 0) + np.where(d7, d_7, 0)
		nc = np.where(z7, 0, nc)
		adv = np.where(isn, 3 + b1, 0) + np.where(z7, 4, 0) + np.where(d7, 4 + b7, 0) + np.where(is0, 3, 0)
		if rl:
			bp2 = bp + 3
			j0 = bp2 >> 3
			w2 = (D[j0] | (D[j0 + 1] << 8) | (D[j0 + 2] << 16)) >> (bp2 & 7)
			r1 = w2 & 1
			r2 = (w2 >> 1) & 3
			r3 = (w2 >> 3) & 255
			rv = np.where(r1 == 0, 0, np.where(r2 == 3, r3, r2))
			rb = np.where(r1 == 0, 1, np.where(r2 == 3, 11, 3))
			adv = adv + np.where(is0, rb, 0)
			run = np.where(is0, rv, np.where(need, run, run - 1))
		bp = bp + adv
		cur[fl] = nc
		out[:, s] = nc.astype(np.int16)
	return out


# NWA(複数エントリ可)を展開してPCM(int16, インタリーブ)のリストを返す
def nwa_decode_entries(buf, offsets):
	D = np.zeros(len(buf) + 8192, dtype=np.int32)
	D[:len(buf)] = np.frombuffer(buf, dtype=np.uint8)
	heads = [nwa_header(buf, o) for o in offsets]
	result = [None] * len(heads)
	groups = {}
	for k, h in enumerate(heads):
		if h['comp'] == -1:
			result[k] = (h['ch'], h['freq'], np.frombuffer(buf, dtype='<i2', count=h['datasize'] // 2, offset=h['off'] + 0x2c).copy())
		else:
			groups.setdefault((h['ch'], h['comp'], h['rl'], h['blocksize']), []).append(k)
	for (ch, comp, rl, bsz), ks in groups.items():
		bases = []
		spans = []
		for k in ks:
			h = heads[k]
			offs = np.frombuffer(buf, dtype='<i4', count=h['blocks'], offset=h['off'] + 0x2c).astype(np.int64) + h['off']
			spans.append((len(bases), len(bases) + h['blocks']))
			bases.extend(offs.tolist())
		bases = np.array(bases, dtype=np.int64)
		out = np.concatenate([nwa_decode_blocks(D, bases[i:i + 60000], ch, comp, rl, bsz) for i in range(0, len(bases), 60000)])
		for k, (a, b) in zip(ks, spans):
			h = heads[k]
			result[k] = (ch, h['freq'], out[a:b].reshape(-1)[:h['datasize'] // 2])
	return result


# OGGで保存(大きい配列でクラッシュするため分割書き込み)
def write_ogg(path, ch, freq, pcm):
	pcm = pcm.reshape(-1, ch)
	with sf.SoundFile(str(path), 'w', samplerate=freq, channels=ch, format='OGG', subtype='VORBIS') as f:
		for i in range(0, len(pcm), 65536):
			f.write(pcm[i:i + 65536])


# ----------------------------------------------------------------------------
# シナリオ変換
# ----------------------------------------------------------------------------

# 使用するRealLiveの命令(モジュール種別,モジュール,オペコード)の名前
def rl_ops():
	return {
		(1, 20, 0): 'bgmLoop', (1, 20, 2): 'bgmPlay', (1, 20, 5): 'bgmStop', (1, 20, 105): 'bgmFadeOut',
		(1, 33, 73): 'grpOpenBg', (1, 33, 75): 'grpMulti', (1, 33, 32): 'shake', (1, 33, 406): 'pan',
		(0, 1, 11): 'jump', (0, 1, 12): 'farcall', (0, 1, 13): 'rtl',
		(1, 23, 0): 'koePlay', (1, 23, 5): 'koeStop',
		(1, 26, 20): 'movPlay', (1, 26, 5): 'movStop',
		(0, 3, 17): 'pause', (0, 3, 151): 'msgHide',
		(1, 21, 0): 'wavPlay', (1, 21, 2): 'wavLoop', (1, 21, 5): 'wavStop', (1, 21, 20): 'wavStopAll', (1, 21, 105): 'wavFadeOut',
		(1, 30, 0): 'stackClear', (1, 4, 100): 'wait', (1, 4, 101): 'waitC',
		(1, 4, 1200): 'end', (1, 4, 1201): 'menuReturn', (1, 4, 300): 'ignore', (1, 4, 1211): 'ignore', (1, 4, 1212): 'ignore',
		(1, 4, 110): 'ignore', (1, 4, 112): 'ignore', (1, 4, 320): 'ignore',
	}


# ゲーム開始シーンから辿れるシーンを全て展開
def story_scan(scenes, start_scene):
	parsed = {}
	todo = [start_scene]
	ops = rl_ops()
	while todo:
		n = todo.pop()
		if n in parsed:
			continue
		parsed[n] = rl_parse_scene(scenes[n])
		for e in parsed[n]:
			if e[1] == 'cmd' and ops.get(e[2][:3]) in ('jump', 'farcall'):
				todo.append(e[3][0][1])
	return parsed


# 全角化(ONScripterで特殊文字になる半角文字を避ける)
def to_zen(s):
	r = []
	for ch in s:
		o = ord(ch)
		if ch == ' ':
			r.append('\u3000')
		elif 0x21 <= o <= 0x7e:
			r.append(chr(o + 0xfee0) if ch != '\\' else '\uffe5')
		elif 0xff61 <= o <= 0xff9f:
			r.append(unicodedata.normalize('NFKC', ch))
		else:
			r.append(ch)
	s = ''.join(r)
	return s.encode('cp932', errors='replace').decode('cp932')


# 使用画像・音声の名前を集める
def collect_resources(parsed):
	ops = rl_ops()
	res = {'bg': set(), 'layer': set(), 'bgm': set(), 'se': set(), 'koe': set(), 'mov': set()}
	for els in parsed.values():
		for e in els:
			if e[1] != 'cmd':
				continue
			name = ops.get(e[2][:3])
			a = e[3]
			if name == 'grpOpenBg':
				res['bg'].add(a[0][1].decode('cp932').lower())
			elif name == 'grpMulti':
				res['bg'].add(a[0][1].decode('cp932').lower())
				for x in a[2:]:
					if x[0] != 'special' or x[1] != 1:
						raise RuntimeError('未対応のgrpMulti形式です')
					res['layer'].add((x[2][0][1].decode('cp932').lower(), x[2][1][1]))
			elif name in ('bgmLoop', 'bgmPlay'):
				res['bgm'].add(a[0][1].decode('cp932').lower())
			elif name in ('wavPlay', 'wavLoop'):
				res['se'].add(a[0][1].decode('cp932').lower())
			elif name == 'koePlay':
				res['koe'].add(a[0][1])
			elif name == 'movPlay':
				res['mov'].add(a[0][1].decode('cp932').lower())
	return res


# GAMEEXE.INIの#SEL設定を取得
def read_sel(input_dir):
	sel = {}
	for line in ci_path(input_dir, 'GAMEEXE.INI').read_text(encoding='cp932').splitlines():
		m = re.match(r'#SEL\.(\d+)\s*=\s*(.+)', line.strip())
		if m:
			sel[int(m.group(1))] = [int(x) for x in m.group(2).replace(' ', '').split(',') if x != '']
	return sel


# 重ね合わせ画像をSEL設定に従って切り出し、画面内に収まる(画像,座標)にする
def layer_crop(im, sel):
	x1, y1, x2, y2, dx, dy = sel[:6]
	w, h = im.size
	sx0, sy0, sx1, sy1 = max(x1, 0), max(y1, 0), min(x2 + 1, w), min(y2 + 1, h)
	ox, oy = dx + sx0 - x1, dy + sy0 - y1
	cl, ct = max(0, -ox), max(0, -oy)
	cr, cb = min(sx1 - sx0, 640 - ox), min(sy1 - sy0, 480 - oy)
	if cr <= cl or cb <= ct:
		return None, 0, 0
	im = im.crop((sx0 + cl, sy0 + ct, sx0 + cr, sy0 + cb))
	bb = im.getchannel('A').getbbox()
	if bb is None:
		return None, 0, 0
	return im.crop(bb), ox + cl + bb[0], oy + ct + bb[1]


# 画像変換(重ね合わせ画像・背景・システム画像)
def image_processing(input_dir, pre_converted_dir, res, sel, num_workers):
	img_dir = Path(pre_converted_dir, 'image')
	img_dir.mkdir(exist_ok=True)
	pdt_dir = ci_path(input_dir, 'PDT')

	def load(name):
		return pdt_decode(ci_path(pdt_dir, name + '.pdt').read_bytes())

	def do_bg(name):
		im = load(name)
		fn = name + '.png'
		im.convert('RGB').save(Path(img_dir, fn), compress_level=1)
		return name, fn

	def do_layer(key):
		name, sid = key
		im = load(name)
		crop, x, y = layer_crop(im, sel[sid])
		if crop is None:
			return key, None
		fn = f'{name}_{sid}.png'
		crop.save(Path(img_dir, fn), compress_level=3)
		return key, (fn, x, y)

	bg_files = {}
	layer_files = {}
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = [executor.submit(do_bg, n) for n in sorted(res['bg'] | {'z_titl1', 'z_tai01a', 'z_tai02a'})]
		futures += [executor.submit(do_layer, k) for k in sorted(res['layer'])]
		for f in concurrent.futures.as_completed(futures):
			a, b = f.result()
			if isinstance(a, tuple):
				layer_files[a] = b
			else:
				bg_files[a] = b
	system_images(pdt_dir, img_dir)
	return bg_files, layer_files


# システム画像(メッセージウィンドウ・名前枠・タイトルボタン・カーソル等)を作成
def system_images(pdt_dir, img_dir):
	def load(name):
		return pdt_decode(ci_path(pdt_dir, name + '.pdt').read_bytes())

	# メッセージウィンドウ: 半透明の塗り+枠
	frame, mask = load('howd'), load('howd2')
	fill = Image.new('RGBA', mask.size, (28, 24, 50, 0))
	fill.putalpha(mask.getchannel('A').point(lambda v: v * 92 // 255))
	win = Image.new('RGBA', mask.size, (0, 0, 0, 0))
	win.alpha_composite(fill)
	win.alpha_composite(frame)
	pad = Image.new('RGBA', (win.width * 3 // 2, win.height * 3 // 2), (0, 0, 0, 0))
	pad.paste(win, (0, 0))
	pad.save(Path(img_dir, 'win.png'))

	# 名前枠: 文字数に応じて中央部分を引き伸ばす
	nb = load('howb')
	nb.save(Path(img_dir, 'howb.png'))
	for n in range(5, 9):
		w = 24 * n + 16
		im = Image.new('RGBA', (w, nb.height), (0, 0, 0, 0))
		im.paste(nb.crop((0, 0, 48, nb.height)), (0, 0))
		im.paste(nb.crop((48, 0, 64, nb.height)).resize((w - 96, nb.height)), (48, 0))
		im.paste(nb.crop((64, 0, 112, nb.height)), (w - 48, 0))
		im.save(Path(img_dir, f'howb{n}.png'))

	# タイトルボタン(通常/選択の2コマ)
	t1, t2 = load('z_titl1'), load('z_titl2')
	for i in range(4):
		box = (230, 135 + 53 * i, 410, 188 + 53 * i)
		im = Image.new('RGBA', (360, 53))
		im.paste(t1.crop(box), (0, 0))
		im.paste(t2.crop(box), (180, 0))
		im.save(Path(img_dir, f'tb{i + 1}.png'))

	# クリック待ちカーソル
	load('_kcur01').save(Path(img_dir, 'kcur.png'))

	# ログ画面の矢印
	for i, (up, on) in enumerate([(True, False), (True, True), (False, False), (False, True)]):
		im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
		d = ImageDraw.Draw(im)
		col = (255, 255, 160, 255) if on else (200, 200, 200, 255)
		d.polygon([(16, 6), (28, 26), (4, 26)] if up else [(4, 6), (28, 6), (16, 26)], fill=col)
		im.save(Path(img_dir, f'lb{i}.png'))


# 効果音・BGM・ボイスの変換
def audio_processing(input_dir, pre_converted_dir, res, num_workers):
	jobs = []
	bgm_dir = Path(pre_converted_dir, 'bgm')
	se_dir = Path(pre_converted_dir, 'se')
	vo_dir = Path(pre_converted_dir, 'v')
	for d in (bgm_dir, se_dir, vo_dir):
		d.mkdir(exist_ok=True)
	bgm_ok = set()
	se_ok = set()
	koe_ok = set()

	def do_nwa(src, dst):
		buf = src.read_bytes()
		ch, freq, pcm = nwa_decode_entries(buf, [0])[0]
		write_ogg(dst, ch, freq, pcm)

	def do_nwk(path, entries):
		buf = path.read_bytes()
		n = struct.unpack_from('<i', buf, 0)[0]
		table = {}
		for i in range(n):
			length, offset, koe_num = struct.unpack_from('<iii', buf, 4 + i * 12)
			table[koe_num] = offset
		want = [k for k in entries if k in table]
		for i in range(0, len(want), 400):
			part = want[i:i + 400]
			for k, (ch, freq, pcm) in zip(part, nwa_decode_entries(buf, [table[k] for k in part])):
				write_ogg(Path(vo_dir, f'{path.stem[1:]}{k:05d}.ogg'), ch, freq, pcm)
		return [path.stem[1:] + f'{k:05d}' for k in want]

	for name in sorted(res['bgm'] | {'bgm11'}):
		src = ci_path(input_dir, 'BGM', name + '.nwa')
		if src.is_file():
			bgm_ok.add(name)
			jobs.append(('f', do_nwa, src, Path(bgm_dir, name + '.ogg')))
	for name in sorted(res['se']):
		src = ci_path(input_dir, 'WAV', name + '.nwa')
		if src.is_file():
			se_ok.add(name)
			jobs.append(('f', do_nwa, src, Path(se_dir, name + '.ogg')))
	byfile = {}
	for k in sorted(res['koe'] | {888800009, 888800010, 888800011, 888800012}):
		byfile.setdefault(k // 100000, []).append(k % 100000)
	for f, entries in byfile.items():
		src = ci_path(input_dir, 'KOE', f'z{f:04d}.nwk')
		if src.is_file():
			jobs.append(('k', do_nwk, src, entries))
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = [(j[0], executor.submit(j[1], j[2], j[3])) for j in jobs]
		for kind, f in futures:
			r = f.result()
			if kind == 'k':
				koe_ok.update(int(x) for x in r)
	return bgm_ok, se_ok, koe_ok


# 式の定数畳み込み(リプレイモードフラグintF[810]は常に0)
def rl_const(e):
	t = e[0]
	if t == 'int':
		return e[1]
	if t == 'mem' and e[1] == 5 and e[2] == ('int', 810):
		return 0
	if t == 'neg':
		v = rl_const(e[1])
		return None if v is None else -v
	if t == 'bin':
		a, b = rl_const(e[2]), rl_const(e[3])
		if a is None or b is None:
			return None
		f = {0: lambda: a + b, 1: lambda: a - b, 2: lambda: a * b, 40: lambda: int(a == b), 41: lambda: int(a != b),
			42: lambda: int(a <= b), 43: lambda: int(a < b), 44: lambda: int(a >= b), 45: lambda: int(a > b),
			60: lambda: int(bool(a) and bool(b)), 61: lambda: int(bool(a) or bool(b))}.get(e[1])
		return None if f is None else f()
	return None


# 変数名(intA[n]→%100番台)
def rl_var(e, varmap):
	if e[0] != 'mem' or e[1] != 0 or e[2][0] != 'int':
		raise RuntimeError(f'未対応の変数参照です: {e}')
	k = e[2][1]
	if k not in varmap:
		varmap[k] = 100 + len(varmap)
		if varmap[k] > 199:
			raise RuntimeError('使用する変数が多すぎます')
	return f'%{varmap[k]}'


def rl_operand(e, varmap):
	if e[0] == 'int':
		return str(e[1])
	if e[0] == 'neg' and e[1][0] == 'int':
		return str(-e[1][1])
	return rl_var(e, varmap)


# 条件分岐(cond==want のとき飛ぶ)をONScripterの行にする
def rl_jump_lines(cond, want, label, varmap):
	c = rl_const(cond)
	if c is not None:
		return [f'goto *{label}'] if bool(c) == want else []
	if cond[0] == 'bin' and 40 <= cond[1] <= 45:
		op = {40: '==', 41: '!=', 42: '<=', 43: '<', 44: '>=', 45: '>'}[cond[1]]
		if not want:
			op = {'==': '!=', '!=': '==', '<=': '>', '<': '>=', '>=': '<', '>': '<='}[op]
		return [f'if {rl_operand(cond[2], varmap)}{op}{rl_operand(cond[3], varmap)} goto *{label}']
	if cond[0] == 'bin' and cond[1] in (60, 61):
		# (a && b) を want 側で飛ぶ / (a || b) を want 側で飛ぶ
		both = (cond[1] == 60) == want
		if both:
			l = []
			ca = rl_jump_lines(cond[2], want, label, varmap)
			cb = rl_jump_lines(cond[3], want, label, varmap)
			if len(ca) != 1 or len(cb) != 1 or not ca[0].startswith('if ') or not cb[0].startswith('if '):
				raise RuntimeError('未対応の条件式です')
			return [ca[0][:-len(f' goto *{label}')] + ' && ' + cb[0][3:]]
		return rl_jump_lines(cond[2], want, label, varmap) + rl_jump_lines(cond[3], want, label, varmap)
	raise RuntimeError(f'未対応の条件式です: {cond}')


# 名前表示用の座標(名前枠ファイル名,枠X,文字X)
def name_layout(name):
	w = sum(24 if ord(c) > 0x7f else 12 for c in name)
	n = -(-w // 24)
	fw = 112 if n <= 4 else 24 * n + 16
	fx = max(2, 100 - fw // 2)
	return ('howb.png' if n <= 4 else f'howb{n}.png'), fx, fx + (fw - w) // 2


# バイトコード→ONScripter(0.txt)の本文へ
def scenario_cnv(parsed, ctx):
	ops = rl_ops()
	lines = []
	varmap = {}
	names = {}
	lab_cnt = [0]

	def newlab(scene):
		lab_cnt[0] += 1
		return f's{scene}_{lab_cnt[0]}'

	for scene in sorted(parsed):
		els = parsed[scene]
		targets = {}
		for e in els:
			if e[1] in ('goto', 'gotoif'):
				targets.setdefault(e[-1], None)
			elif e[1] in ('goto_on', 'goto_case', 'gosub_with'):
				raise RuntimeError('未対応の分岐命令です')
		for off in sorted(targets):
			targets[off] = newlab(scene)
		lines.append(f'*s{scene}')
		voice = 0
		last_text = False
		i = 0
		while i < len(els):
			e = els[i]
			off, kind = e[0], e[1]
			i += 1
			if off in targets:
				lines.append('*' + targets[off])
				last_text = False
			if kind in ('line', 'kidoku', 'entry', 'comma'):
				continue
			if kind == 'text':
				s = e[2].decode('cp932').replace('＊Ａ', '秋吉').replace('＊Ｂ', '拓巳')
				if s.startswith('ＳｅｅｎＥｎｄ'):
					continue
				m = re.match(r'【(.*?)】', s)
				name = to_zen(m.group(1)) if m else ''
				body = to_zen(s[m.end():] if m else s)
				if body == '':
					continue
				if name:
					if name not in names:
						names[name] = len(names) + 1
					lines.append(f'nv {names[name]},{voice}' if voice else f'nm {names[name]}')
				elif voice:
					lines.append(f'vo {voice}')
				voice = 0
				lines.append(body)
				last_text = True
				continue
			if kind == 'expr':
				op, lhs, rhs = e[2][1], e[2][2], e[2][3]
				if lhs[0] == 'mem' and lhs[1] == 51:
					continue
				if lhs[0] == 'mem' and lhs[1] == 0 and op in (0x14, 0x15, 0x1e) and rhs[0] == 'int':
					cmd = {0x14: 'add', 0x15: 'sub', 0x1e: 'mov'}[op]
					lines.append(f'{cmd} {rl_var(lhs, varmap)},{rhs[1]}')
					last_text = False
					continue
				raise RuntimeError(f'未対応の代入式です: {e[2]}')
			if kind == 'goto':
				lines.append(f'goto *{targets[e[3]]}')
				continue
			if kind == 'gotoif':
				key = e[2][1:3]
				want = {(1, 1): True, (1, 2): False}.get(key)
				if want is None:
					raise RuntimeError('未対応の条件分岐です')
				lines.extend(rl_jump_lines(e[3], want, targets[e[4]], varmap))
				continue
			if kind == 'select':
				opts = e[4]
				if any(c for c, _ in opts):
					raise RuntimeError('条件付き選択肢は未対応です')
				var = None
				j = i
				while j < len(els) and els[j][1] in ('line', 'kidoku'):
					j += 1
				if j < len(els) and els[j][1] == 'expr' and els[j][2][3] == ('store',):
					var = rl_var(els[j][2][2], varmap)
					i = j + 1
				end = newlab(scene)
				labs = [newlab(scene) for _ in opts]
				txts = ','.join(f'"{to_zen(t.decode("cp932"))}",*{l}' for (_, t), l in zip(opts, labs))
				lines.append('hn')
				lines.append(f'select {txts}')
				for k, l in enumerate(labs):
					lines.append('*' + l)
					if var:
						lines.append(f'mov {var},{k}')
					if k < len(labs) - 1:
						lines.append(f'goto *{end}')
				lines.append('*' + end)
				last_text = False
				continue
			name = ops.get(e[2][:3])
			a = e[3]
			if name is None:
				raise RuntimeError(f'未対応の命令です: scene {scene} {e[2]}')
			if name in ('ignore', 'stackClear', 'rtl', 'end'):
				continue
			if name != 'pause':
				last_text = False
			if name == 'pause':
				if last_text:
					lines[-1] += '\\'
				else:
					lines.append('\\')
				last_text = False
			elif name == 'msgHide':
				lines.append('hn')
			elif name == 'koePlay':
				voice = a[0][1] if a[0][1] in ctx['koe'] else 0
			elif name == 'koeStop':
				lines.append('dwavestop 0')
				voice = 0
			elif name in ('grpOpenBg', 'grpMulti'):
				lines.append(gfx_line(name, a, ctx))
			elif name == 'pan':
				sx, sy, ex, ey = (x[1] for x in a[:4])
				dx1, dy1 = a[5][1], a[6][1]
				if sx != ex:
					raise RuntimeError('横方向のパンは未対応です')
				lines.append(f'pn {dy1 - sy},{dy1 - ey},{a[9][1]}')
			elif name in ('bgmLoop', 'bgmPlay'):
				bn = a[0][1].decode('cp932').lower()
				if bn in ctx['bgm']:
					fade = a[1][1] if name == 'bgmLoop' and len(a) > 1 and a[1][0] == 'int' else 0
					lines.append(f'bgmfadein {fade}')
					lines.append(f'{"bgm" if name == "bgmLoop" else "bgmonce"} "bgm\\{bn}.ogg"')
			elif name == 'bgmFadeOut':
				lines.append(f'bgmfadeout {a[0][1]}')
				lines.append('bgmstop')
			elif name == 'bgmStop':
				lines.append('bgmstop')
			elif name in ('wavPlay', 'wavLoop'):
				sn = a[0][1].decode('cp932').lower()
				if sn in ctx['se']:
					if name == 'wavPlay':
						lines.append(f'dwave 6,"se\\{sn}.ogg"')
					else:
						lines.append(f'dwaveloop {a[1][1]},"se\\{sn}.ogg"')
			elif name == 'wavFadeOut':
				lines.append(f'dwavestop {a[0][1]}')
			elif name in ('wavStop', 'wavStopAll'):
				lines.append('sa')
			elif name == 'shake':
				lines.append(f'quake {({3: 10, 4: 16, 5: 5}.get(a[0][1], 8))},500')
			elif name == 'wait':
				lines.append(f'wait {min(a[0][1], 1000)}')
			elif name == 'waitC':
				lines.append(f'delay {min(a[0][1], 1500)}')
			elif name == 'movStop':
				continue
			elif name == 'movPlay':
				lines.append('bgmstop:dwavestop -1:skipoff')
				lines.append(f'mpegplay "{a[0][1].decode("cp932").lower()}.mpg",1')
			elif name == 'menuReturn':
				lines.append('bgmstop:dwavestop -1:skipoff')
				lines.append('reset')
			elif name == 'jump':
				lines.append(f'goto *s{a[0][1]}')
			else:
				raise RuntimeError(f'未対応の命令です: scene {scene} {name}')
		lines.append('end')
	nt = []
	for name, idx in names.items():
		fn, fx, tx = name_layout(name)
		nt.append(f'if %10=={idx} lsp 21,"image\\{fn}",{fx}*%98/%99,279*%98/%99:lsp 20,$96+"{name}",{tx}*%98/%99,292*%98/%99:return')
	return '\n'.join(lines), '\n'.join(nt)


# 画面切り替え命令(背景+重ね合わせ画像)
def gfx_line(name, a, ctx):
	bg = a[0][1].decode('cp932').lower()
	bgf = ctx['bg'][bg]
	if name == 'grpOpenBg':
		if len(a) == 2:
			return f'gb "{bgf}"'
		if len(a) == 8:
			x1, y1, dx, dy = a[2][1], a[3][1], a[6][1], a[7][1]
			return f'gp "{bgf}",{dx - x1},{dy - y1}'
		raise RuntimeError('未対応のgrpOpenBg形式です')
	parts = []
	layers = [(x[2][0][1].decode('cp932').lower(), x[2][1][1]) for x in a[2:]]
	for key in sorted(layers, key=lambda k: k[1] == 200):
		info = ctx['layer'][key]
		if info:
			parts.append(f'"{info[0]}",{info[1]},{info[2]}')
	if not parts:
		return f'gb "{bgf}"'
	if len(parts) > 3:
		raise RuntimeError('重ね合わせ画像が多すぎます')
	return f'g{len(parts)} "{bgf}",' + ','.join(parts)


# 変換後シナリオが開始からエンディングまで途切れず繋がっているか確認
def check_scenario(scn, start_label):
	L = scn.split('\n')
	lab = {}
	for i, l in enumerate(L):
		if re.fullmatch(r'\*\w+', l):
			lab[l[1:]] = i

	def parse(l):
		m = re.fullmatch(r'goto \*(\w+)', l)
		if m:
			return ('goto', m.group(1))
		m = re.fullmatch(r'if (%\d+)(==|!=|<=|>=|<|>)(-?\d+) goto \*(\w+)', l)
		if m:
			return ('if', m.group(1), m.group(2), int(m.group(3)), m.group(4))
		if l.startswith('if '):
			raise RuntimeError(f'確認できない条件分岐があります: {l}')
		if l.startswith('select '):
			return ('select', re.findall(r',\*(\w+)', l))
		m = re.fullmatch(r'(mov|add|sub) (%\d+),(-?\d+)', l)
		if m:
			return (m.group(1), m.group(2), int(m.group(3)))
		if l in ('reset', 'end'):
			return (l,)
		return ('nop',)

	P = [parse(l) for l in L]
	for p in P:
		for t in ([p[1]] if p[0] == 'goto' else [p[4]] if p[0] == 'if' else p[1] if p[0] == 'select' else []):
			if t not in lab:
				raise RuntimeError(f'飛び先ラベルが存在しません: {t}')

	# 条件を無視した到達確認(行き止まりがないか)
	seen = set()
	todo = [lab[start_label]]
	ends = 0
	while todo:
		i = todo.pop()
		if i in seen:
			continue
		seen.add(i)
		p = P[i]
		nxt = []
		if p[0] == 'goto':
			nxt = [lab[p[1]]]
		elif p[0] == 'if':
			nxt = [lab[p[4]], i + 1]
		elif p[0] == 'select':
			nxt = [lab[t] for t in p[1]]
		elif p[0] == 'reset':
			ends += 1
		elif p[0] == 'end':
			raise RuntimeError(f'エンディングに到達せず途切れる箇所があります: {i + 1}行目')
		else:
			nxt = [i + 1]
		for j in nxt:
			if j >= len(L):
				raise RuntimeError('シナリオの末尾を越えて続く箇所があります')
			todo.append(j)
	if ends == 0:
		raise RuntimeError('エンディングに到達できません')

	# 変数の値を追って最初・最後・交互に選択肢を選んで最後まで進む
	for policy in (0, 1, 2):
		var = {}
		pc = lab[start_label]
		steps = 0
		sel_cnt = 0
		while True:
			steps += 1
			if steps > 5000000:
				raise RuntimeError('シナリオが終了しません')
			p = P[pc]
			pc += 1
			if p[0] == 'goto':
				pc = lab[p[1]]
			elif p[0] == 'if':
				v = var.get(p[1], 0)
				if {'==': v == p[3], '!=': v != p[3], '<=': v <= p[3], '>=': v >= p[3], '<': v < p[3], '>': v > p[3]}[p[2]]:
					pc = lab[p[4]]
			elif p[0] == 'select':
				k = {0: 0, 1: len(p[1]) - 1, 2: sel_cnt % len(p[1])}[policy]
				sel_cnt += 1
				pc = lab[p[1][k]]
			elif p[0] == 'mov':
				var[p[1]] = p[2]
			elif p[0] == 'add':
				var[p[1]] = var.get(p[1], 0) + p[2]
			elif p[0] == 'sub':
				var[p[1]] = var.get(p[1], 0) - p[2]
			elif p[0] == 'reset':
				break
			elif p[0] == 'end':
				raise RuntimeError('エンディングに到達せず終了する経路があります')


# 0.txtにはじめから書いておくもの
def default_txt(txt: str, nt: str):
	head = '''*define
mov %98,1:mov %99,1

caption "いたいけな彼女 for ONScripter"

rmenu "セーブ",save,"ロード",load,"ログ",lookback,"スキップ",skip,"タイトルへ戻る",reset
menusetwindow 24*%98/%99,24*%98/%99,2*%98/%99,2*%98/%99,0,1,#334455
menuselectcolor #ffff80,#ffffff,#808080
selectcolor #ffff80,#ffffff
savename "ＳＡＶＥ","ＬＯＡＤ","ＤＡＴＡ"
savenumber 15
transmode alpha
globalon
saveon
windowback
humanz 700
defaultspeed 40,20,5
effect 10,10,500
bgmfadeout 1500
bgmfadein 0
lookbackbutton "image\\\\lb1.png","image\\\\lb0.png","image\\\\lb3.png","image\\\\lb2.png"
pretextgosub *pt

defsub nm
defsub nv
defsub vo
defsub hn
defsub sa
defsub gb
defsub gp
defsub g1
defsub g2
defsub g3
defsub pn
game
;----------------------------------------
*start
	mov %98,1:mov %99,1
	gosub *sw
	gosub *bk
	print 1
	gettimer %0
	if %0>3000 goto *title
	goto *warn
;----------------------------------------
*bk
	csp -1
	lsp 900,"image\\\\black.png",0,0
return
;----------------------------------------
*sw
	setwindow 56*%98/%99,351*%98/%99,21,3,24*%98/%99,24*%98/%99,0,5*%98/%99,20,0,1,"image\\\\win.png",16*%98/%99,309*%98/%99
	setcursor 0,":a/18,60,2;image\\\\kcur.png",0,0
	setcursor 1,":a/18,60,2;image\\\\kcur.png",0,0
	itoa $97,24*%98/%99
	mov $96,":s/"+$97+","+$97+",0;#ffffff"
	mov $95,$96+"#666666"
	mov $93,":s/"+$97+","+$97+",0;#223355"
return
;----------------------------------------
*pt
	csp 20:csp 21
	dwavestop 0
	if %10>0 gosub *nt
	if %11>0 itoa $11,%11:dwave 0,"v\\\\"+$11+".ogg"
	mov %10,0:mov %11,0
	print 1
	saveon
return
;----------------------------------------
*nt
'''
	tail = '''
return
;----------------------------------------
*nm
	getparam %10
return
*nv
	getparam %10,%11
return
*vo
	getparam %11
return
*hn
	csp 20:csp 21:print 10
return
*sa
	dwavestop 1:dwavestop 2:dwavestop 3:dwavestop 4:dwavestop 6
return
;----------------------------------------
*gc
	csp 20:csp 21:csp 896:csp 897:csp 898:csp 899
	lsp 900,"image\\\\"+$0,0,0
return
*gb
	getparam $0
	gosub *gc
	print 10
return
*gp
	getparam $0,%0,%1
	gosub *gc
	amsp 900,%0*%98/%99,%1*%98/%99,255
	print 10
return
*g1
	getparam $0,$1,%0,%1
	gosub *gc
	lsp 899,"image\\\\"+$1,%0*%98/%99,%1*%98/%99
	print 10
return
*g2
	getparam $0,$1,%0,%1,$2,%2,%3
	gosub *gc
	lsp 899,"image\\\\"+$1,%0*%98/%99,%1*%98/%99
	lsp 898,"image\\\\"+$2,%2*%98/%99,%3*%98/%99
	print 10
return
*g3
	getparam $0,$1,%0,%1,$2,%2,%3,$3,%4,%5
	gosub *gc
	lsp 899,"image\\\\"+$1,%0*%98/%99,%1*%98/%99
	lsp 898,"image\\\\"+$2,%2*%98/%99,%3*%98/%99
	lsp 897,"image\\\\"+$3,%4*%98/%99,%5*%98/%99
	print 10
return
;----------------------------------------
*pn
	getparam %0,%1,%2
	resettimer
*pn1
	gettimer %3
	if %3>%2 mov %3,%2
	amsp 900,0,(%0+(%1-%0)*%3/%2)*%98/%99,255
	print 1
	if %3<%2 goto *pn1
return
;----------------------------------------
*warn
	trap *wend
	lsp 900,"image\\\\z_tai01a.png",0,0
	print 10
	wait 3000
	lsp 900,"image\\\\z_tai02a.png",0,0
	print 10
	dwave 0,"v\\\\888800009.ogg"
	wait 7600
	dwave 0,"v\\\\888800010.ogg"
	wait 15000
	dwave 0,"v\\\\888800011.ogg"
	wait 5300
	dwave 0,"v\\\\888800012.ogg"
	wait 4000
*wend
	trap off
	dwavestop -1
	gosub *bk
	print 10
;----------------------------------------
*title
	trap off
	csp -1:bgmstop:dwavestop -1
	lsp 900,"image\\\\z_titl1.png",0,0
	lsp 31,":a/2,0,3;image\\\\tb1.png",230*%98/%99,135*%98/%99
	lsp 32,":a/2,0,3;image\\\\tb2.png",230*%98/%99,188*%98/%99
	lsp 33,":a/2,0,3;image\\\\tb3.png",230*%98/%99,241*%98/%99
	lsp 34,":a/2,0,3;image\\\\tb4.png",230*%98/%99,294*%98/%99
	lsp 35,$96+"設定",540*%98/%99,440*%98/%99
	lsph 36,$93+"設定",540*%98/%99,440*%98/%99
	bgmfadein 0
	bgm "bgm\\\\bgm11.ogg"
	print 10
*title_loop
	bclear
	spbtn 31,1
	spbtn 32,2
	spbtn 33,3
	spbtn 34,4
	exbtn 35,5,"P36C35"
	exbtn_d "P35C36"
	btnwait %50
	if %50==1 bgmfadeout 1500:bgmstop:gosub *bk:print 10:goto *s90
	if %50==2 gosub *bk:print 1:systemcall load:goto *title
	if %50==3 gosub *unsup:goto *title_loop
	if %50==4 bgmstop:gosub *bk:print 10:end
	if %50==5 goto *cfg
goto *title_loop
;----------------------------------------
*unsup
	lsp 12,"image\\\\black.png",0,0,170
	lsp 11,$96+"ＣＧ・ＢＧＭ・回想モードには対応していません",32*%98/%99,200*%98/%99
	lsp 10,$96+"クリックでタイトルにもどります",116*%98/%99,260*%98/%99
	print 1
	click
	csp 10:csp 11:csp 12:print 1
return
;----------------------------------------
*cfg
	gosub *bk
	mov $130,$96+"○――――――――――"
	mov $131,$96+"―○―――――――――"
	mov $132,$96+"――○――――――――"
	mov $133,$96+"―――○―――――――"
	mov $134,$96+"――――○――――――"
	mov $135,$96+"―――――○―――――"
	mov $136,$96+"――――――○――――"
	mov $137,$96+"―――――――○―――"
	mov $138,$96+"――――――――○――"
	mov $139,$96+"―――――――――○―"
	mov $140,$96+"――――――――――○"
*cfg_loop
	getbgmvol %130
	getsevol %131
	getvoicevol %132
	itoa2 $141,%130
	itoa2 $142,%131
	itoa2 $143,%132
	mov $146,$130:if %130>0 mov $146,$131
	if %130>=20 mov $146,$132
	if %130>=30 mov $146,$133
	if %130>=40 mov $146,$134
	if %130>=50 mov $146,$135
	if %130>=60 mov $146,$136
	if %130>=70 mov $146,$137
	if %130>=80 mov $146,$138
	if %130>=90 mov $146,$139
	if %130>=100 mov $146,$140
	mov $147,$130:if %131>0 mov $147,$131
	if %131>=20 mov $147,$132
	if %131>=30 mov $147,$133
	if %131>=40 mov $147,$134
	if %131>=50 mov $147,$135
	if %131>=60 mov $147,$136
	if %131>=70 mov $147,$137
	if %131>=80 mov $147,$138
	if %131>=90 mov $147,$139
	if %131>=100 mov $147,$140
	mov $148,$130:if %132>0 mov $148,$131
	if %132>=20 mov $148,$132
	if %132>=30 mov $148,$133
	if %132>=40 mov $148,$134
	if %132>=50 mov $148,$135
	if %132>=60 mov $148,$136
	if %132>=70 mov $148,$137
	if %132>=80 mov $148,$138
	if %132>=90 mov $148,$139
	if %132>=100 mov $148,$140
	lsp 130,$96+"［環境設定］",50*%98/%99,50*%98/%99
	lsp 131,$95+"テスト再生",150*%98/%99,420*%98/%99
	lsp 132,$95+"初期値",310*%98/%99,420*%98/%99
	lsp 133,$95+"戻る",450*%98/%99,420*%98/%99
	lsp 135,$96+"ＢＧＭ",40*%98/%99,150*%98/%99
	lsp 136,$95+"＜",160*%98/%99,150*%98/%99
	lsp 137,$146,200*%98/%99,150*%98/%99
	lsp 138,$95+"＞",490*%98/%99,150*%98/%99
	lsp 139,$95+$141,540*%98/%99,150*%98/%99
	lsp 140,$96+"ＳＥ",40*%98/%99,250*%98/%99
	lsp 141,$95+"＜",160*%98/%99,250*%98/%99
	lsp 142,$147,200*%98/%99,250*%98/%99
	lsp 143,$95+"＞",490*%98/%99,250*%98/%99
	lsp 144,$95+$142,540*%98/%99,250*%98/%99
	lsp 145,$96+"ボイス",40*%98/%99,350*%98/%99
	lsp 146,$95+"＜",160*%98/%99,350*%98/%99
	lsp 147,$148,200*%98/%99,350*%98/%99
	lsp 148,$95+"＞",490*%98/%99,350*%98/%99
	lsp 149,$95+$143,540*%98/%99,350*%98/%99
	print 1
	bclear
	spbtn 131,131
	spbtn 132,132
	spbtn 133,133
	spbtn 136,136
	spbtn 138,138
	spbtn 141,141
	spbtn 143,143
	spbtn 146,146
	spbtn 148,148
	btnwait %140
	if %140==131 dwave 0,"v\\\\888800009.ogg"
	if %140==132 dwavestop 0:bgmvol 100:sevol 100:voicevol 100
	if %140==133 csp -1:dwavestop -1:goto *title
	if %140==136 if %130!=0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	if %140==146 if %132!=0 sub %132,10:voicevol %132
	if %140==148 if %132!=100 add %132,10:voicevol %132
goto *cfg_loop
;----------------------------------------
;<scenario>
'''
	return (head + nt + tail).replace('\\\\', '\\') + txt + '\n'


# メイン処理関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):
	input_dir = find_game_root(values['input_dir'] if values else 'game_file')
	num_workers = values_ex.get('num_workers', (os.cpu_count() or 4) + 4)
	pre_converted_dir = Path(pre_converted_dir)
	pre_converted_dir.mkdir(parents=True, exist_ok=True)

	# シナリオ展開
	scenes = rl_load_seen(ci_path(input_dir, 'SEEN.TXT'))
	parsed = story_scan(scenes, 90)
	res = collect_resources(parsed)

	# 画像・音声・動画
	bg_files, layer_files = image_processing(input_dir, pre_converted_dir, res, read_sel(input_dir), num_workers)
	bgm_ok, se_ok, koe_ok = audio_processing(input_dir, pre_converted_dir, res, num_workers)
	for name in res['mov']:
		shutil.copy(ci_path(input_dir, 'MOV', name + '.mpg'), Path(pre_converted_dir, name + '.mpg'))

	# シナリオ変換
	ctx = {'bg': bg_files, 'layer': layer_files, 'bgm': bgm_ok, 'se': se_ok, 'koe': koe_ok}
	txt, nt = scenario_cnv(parsed, ctx)
	check_scenario(txt, 's90')

	# 0.txt書込み
	with open(Path(pre_converted_dir, '0.txt'), 'w', encoding='cp932', newline='\r\n') as f:
		f.write(default_txt(txt, nt))

	return


# 単体動作 (引数: [入力フォルダ [出力フォルダ]])
if __name__ == "__main__":
	import sys
	main({'input_dir': sys.argv[1]} if len(sys.argv) > 1 else {}, {}, Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd())
