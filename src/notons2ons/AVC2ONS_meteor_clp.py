from __future__ import annotations

import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import hashlib
import json
import operator
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
from tempfile import TemporaryDirectory
from typing import TypedDict

from PIL import Image, ImageDraw, ImageEnhance


def _avc_xor(data: bytes, key: bytes, offset: int) -> bytes:
    result = bytearray(data)
    for lane in range(8):
        symbol = key[(offset + lane) & 7]
        table = bytes(value ^ symbol for value in range(256))
        result[lane::8] = data[lane::8].translate(table)
    return bytes(result)


@dataclass(frozen=True)
class AVCEntry:
    name: str
    offset: int
    size: int


def _read_avc_index(archive: Path) -> tuple[int, bytes, list[AVCEntry]]:
    """Read ArcAVC's XOR-encrypted header and 0x114-byte directory records."""
    with archive.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        prefix = stream.read(0x80)
        if len(prefix) != 0x80:
            raise ValueError(f"Truncated AVC archive: {archive}")
        # ArcAVC's scheme table is external. Recover the key from ARCHIVE\0
        # and locate the header within the same 0x80-byte probe instead.
        for header_offset in range(0x80 - 0x24 + 1):
            key = bytes(a ^ b for a, b in zip(
                prefix[header_offset:header_offset + 8], b"ARCHIVE\0"
            ))
            header = _avc_xor(prefix[header_offset:header_offset + 0x24], key, 0)
            index_offset, entry_size = struct.unpack_from("<ii", header, 0x10)
            count = struct.unpack_from("<i", header, 0x20)[0]
            if entry_size != 0x114 or not 0 < count <= 0xFFFF or index_offset < 0x24:
                continue
            index_start = header_offset + index_offset
            index_size = entry_size * count
            if index_start + index_size > size:
                raise ValueError(f"Truncated AVC index: {archive}")
            stream.seek(index_start)
            index = _avc_xor(stream.read(index_size), key, index_offset)
            entries: list[AVCEntry] = []
            for position in range(0, index_size, entry_size):
                record = index[position:position + entry_size]
                if record[0] != 0:
                    raise ValueError(f"Invalid AVC index record: {archive}")
                raw_name = record[1:0x101].split(b"\0", 1)[0]
                if not raw_name:
                    continue
                name = raw_name.decode("cp932")
                if (name in (".", "..") or name.endswith((" ", "."))
                        or any(c in name for c in '\\/:*?"<>|')
                        or any(ord(c) < 32 for c in name)
                        or re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name, re.I)):
                    raise ValueError(f"Unsafe AVC filename in {archive}: {name!r}")
                relative_offset, length = struct.unpack_from("<II", record, 0x108)
                offset = header_offset + relative_offset
                if offset + length > size:
                    raise ValueError(f"AVC entry outside archive {archive}: {name}")
                entries.append(AVCEntry(name, offset, length))
            return header_offset, key, entries
    raise ValueError(f"AVC header not found: {archive}")


def _extract_avc(archive: Path, destination: Path) -> None:
    header_offset, key, entries = _read_avc_index(archive)
    destination.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as stream:
        for entry in entries:
            target = destination / entry.name
            pending = destination / (entry.name + ".pending")
            if target.is_symlink() or pending.exists() or pending.is_symlink():
                raise FileExistsError(f"Unsafe or unfinished extraction output: {target}")
            try:
                with pending.open("xb") as output:
                    stream.seek(entry.offset)
                    written = 0
                    while written < entry.size:
                        chunk = stream.read(min(1024 * 1024, entry.size - written))
                        if not chunk:
                            raise ValueError(f"Truncated AVC entry {archive}: {entry.name}")
                        output.write(_avc_xor(chunk, key, entry.offset - header_offset + written))
                        written += len(chunk)
                pending.replace(target)
            finally:
                if pending.exists():
                    pending.unlink()


def extract_resource(
    values: dict[str, object], values_ex: dict[str, object], pre_converted_dir: Path,
) -> None:
    input_dir = values["input_dir"]
    if not isinstance(input_dir, (str, Path)):
        raise TypeError("input_dir must be a path")
    source = Path(input_dir).resolve()
    workers = values_ex.get("num_workers", 1)
    if type(workers) is not int or workers < 1:
        raise ValueError("num_workers must be a positive integer")
    archives = [source / (name + ".dat") for name in ("bgm", "data", "grp", "se", "snr", "voice")]
    for archive in archives:
        if not archive.is_file():
            raise FileNotFoundError(archive)
    destination = pre_converted_dir.resolve() / "game_file"
    if destination == source or source in destination.parents:
        raise ValueError("Extraction output must be outside the input folder")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_extract_avc, archive, destination / archive.stem)
            for archive in archives
        ]
        for future in futures:
            future.result()


def _join_bgm_pair(
    intro: Path, loop: Path, destination: Path, values: bool,
) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    pending = destination.with_name(destination.stem + ".pending" + destination.suffix)
    if values:
        from requiredfile_locations import location_env  # type: ignore
        from utils2 import subprocess_args  # type: ignore

        ffmpeg = location_env("ffmpeg")
        process_args = subprocess_args()
    else:
        ffmpeg = "ffmpeg"
        process_args = {}
    try:
        subprocess.run(
            [
                str(ffmpeg), "-y", "-i", str(intro), "-i", str(loop),
                "-filter_complex", "concat=n=2:v=0:a=1[out]",
                "-map", "[out]", "-ar", "44100", "-ac", "2",
                "-c:a", "libvorbis", str(pending),
            ],
            check=True,
            **process_args,
        )
        pending.replace(destination)
    finally:
        if pending.exists():
            pending.unlink()
    return destination.name


def join_bgm_pairs(
    source: Path, output: Path, values: bool, values_ex: dict[str, object],
) -> dict[tuple[str, str], str]:
    bgm_dir = source / "bgm"
    files = {path.name.casefold(): path for path in bgm_dir.glob("*.ogg")}
    pairs: list[tuple[Path, Path, Path]] = []
    for intro in sorted(bgm_dir.glob("*.ogg")):
        match = re.fullmatch(r"(.+)_intro", intro.stem, re.IGNORECASE)
        if not match:
            continue
        loop = files.get(f"{match[1]}_loop.ogg".casefold())
        if loop is None:
            continue
        destination = output / "assets" / "bgm_joined" / f"{match[1]}.ogg"
        pairs.append((intro, loop, destination))

    workers = values_ex.get("num_workers", (os.cpu_count() or 1) + 4)
    if type(workers) is not int or workers < 1:
        raise ValueError("num_workers must be a positive integer")
    joined: dict[tuple[str, str], str] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            (intro, loop, executor.submit(_join_bgm_pair, intro, loop, destination, values))
            for intro, loop, destination in pairs
        ]
        for intro, loop, future in futures:
            joined[(intro.name.casefold(), loop.name.casefold())] = future.result()
    return joined


TitleInfo = TypedDict("TitleInfo", {
    "brand": str, "date": int, "title": str, "cli_arg": str,
    "requiredsoft": list[str], "is_4:3": bool, "program_name": list[str],
    "exe_name": list[str], "version": list[str], "notes": list[str],
})


def title_info() -> TitleInfo:
    return {
        "brand": "Meteor", "date": 20071221, "title": "Clover Point", "cli_arg": "meteor_clp",
        "requiredsoft": [], "is_4:3": True, "program_name": [],
        "exe_name": ["Adv"], "version": ["Clover Point DLsite DL版(VJ004373)"],
        "notes": [
            "This converter was generated by an AI agent.",
            "一応作成途中に一度全ルート完走確認済みですが細かな不具合は把握できてません",
            "クローバーを見つけるシーンで、キャラのボイスが何故かループで再生される",
            "BGMのループ処理が雑、一周するとイントロ含め最初からループされる",
            "セーブ/ロード/コンフィグ/演出など簡略化されてる部分多数",
            "鑑賞モード未実装",
        ],
    }


def crop_buttons(image_path, output_dir):

    image = Image.open(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    x_positions = [0, 252, 720, 972, image.width]
    y_positions = [round(image.height * i / 5) for i in range(6)]

    names = ["start", "continue", "config", "gallery", "exit"]
    states = ["state1", "state2", "state3"]

    for row, name in enumerate(names):
        for col, state in enumerate(states):
            image.crop((
                x_positions[col],
                y_positions[row],
                x_positions[col + 1],
                y_positions[row + 1],
            )).save(output_dir / f"{name}_{state}.png")


def string_sprite(number: int, text: str, x: int | None, y: int, size: int,
                  colors: tuple[str, ...]) -> str:
    """strsp line for a one-line fullwidth text sprite (x=None centers it on 800px)."""
    if not text or any(ord(c) < 0x80 for c in text):
        raise ValueError(f"Title text must be non-empty fullwidth text: {text!r}")
    if x is None:
        x = (800 - len(text) * size) // 2
    # ONScripter wraps the last glyph onto a second line when the column count
    # equals the text length, so one spare column is reserved (ynum is 1).
    return (f"strsp {number},{quote(text)},{x},{y},{len(text) + 1},1,"
            f"{size},{size},0,0,0,1,{','.join(colors)}")


def default_txt() -> str:
    return r""";mode800
*define
caption "Clover Point for ONScripter"
globalon
rubyon
windowback
humanz 10
windowchip 0
lookbackbutton ":s/18,18,0;#ffffff▲",":s/18,18,0;#888888▲",":s/18,18,0;#ffffff▼",":s/18,18,0;#888888▼"
savenumber 18
rmenu "Ｓａｖｅ",save,"Ｌｏａｄ",load,"Ｓｋｉｐ",skip,"Ｌｏｇ",lookback,"Ｔｉｔｌｅ",reset
menusetwindow 24,24,0,4,0,0,#999999
pretextgosub *pretext
defsub ll
defsub lv
defsub lc
defsub lp
defsub la
defsub ds
defsub wa
defsub ms
defsub ap
defsub pb
defsub pc
effect 2,10,500
dim ?0[199][4]
dim ?1[5]
dim ?2[49]
game

*start
resettimer
mov $310,""
mov $311,""
setwindow 25,465,30,4,24,24,0,7,20,0,1,#AAAAAA,0,425,799,599
;setcursor 0,":s/14,14,0;#ffffff▼",0,0
;setcursor 1,":s/14,14,0;#ffffff▼",0,0
gosub *apply_volume
__BOOT__

*pretext
csp 0
if %332=1 dwavestop 0
mov %332,0
if $310!="" strsp 0,$310,40,430,40,1,24,24,0,0,0,1,#ffffff
if $311!="" ap %334,0,0,$311
mov $311,""
return

__TITLE_UI__

*title_begin
gosub *title_audio_stop
csp -1
bg black,2
for %320=0 to 199
for %321=0 to 4
mov ?0[%320][%321],0
next
next
for %320=0 to 5
mov ?1[%320],1
next
mov %333,0
saveon
return

*apply_volume
if %353=0 mov %350,10:mov %351,10:mov %352,10:mov %353,1
bgmvol %350*10
sevol %351*10
voicevol %352*10
return

*lc0
if %300>199 goto *le
return
*le
mov $310,""
mov $311,""
レイヤー番号が範囲外です。変換元の制御を確認してください。\
end

*ll
getparam %300,%301,%302,$300,%304
if %300<0 return
gosub *lc0
if %304=0 mov $300,":a;assets/grp/"+$300
if %304=1 mov $300,":a;assets/generated/"+$300
mov %303,240-%300
mov ?0[%300][0],%301
mov ?0[%300][1],%302
mov ?0[%300][2],255
mov ?0[%300][3],1
mov ?0[%300][4],0
lsph %303,$300,%301,%302
return

*ap
getparam %300,%301,%302,$300
if %300=0 if %302=0 dwave %301,"assets/se/"+$300
if %300=0 if %302=1 dwaveloop %301,"assets/se/"+$300
if %300=1 dwave %301,"assets/voice/"+$300
return

*pb
getparam $300
bgmonce "assets/bgm/"+$300
return

*pc
getparam $300
bgm "assets/bgm_joined/"+$300
return

*lv
getparam %300,%301
if %300<0 return
gosub *lc0
if ?0[%300][3]=0 return
mov ?0[%300][4],%301
mov %303,240-%300
vsp %303,%301
amsp %303,?0[%300][0],?0[%300][1],?0[%300][2]
return

*lc
getparam %300
if %300<0 return
gosub *lc0
mov %303,240-%300
csp %303
mov ?0[%300][3],0
mov ?0[%300][4],0
return

*lp
getparam %300,%301,%302
if %300<0 return
gosub *lc0
mov ?0[%300][0],%301
mov ?0[%300][1],%302
if ?0[%300][3]=0 return
mov %303,240-%300
amsp %303,%301,%302,?0[%300][2]
return

*la
getparam %300,%301
if %300<0 return
gosub *lc0
mov ?0[%300][2],%301
if ?0[%300][3]=0 return
mov %303,240-%300
amsp %303,?0[%300][0],?0[%300][1],%301
return

*ds
getparam %300
textoff
csp 0
if %333=1 csp 20
mov %333,0
if %300<=0 print 1
if %300>0 print 10,%300
return

*wa
getparam %300
gettimer %301
mov %302,?2[%300]-%301
if %302>0 wait %302
return

*ms
getparam $312
mov $310,""
mov $311,""
参照先シナリオがありません。変換レポートを確認してください。@
参照先：$312\
reset
"""


@dataclass(frozen=True)
class Issue:
    kind: str
    file: str
    line: int
    detail: str


def split_args(text: str) -> list[str]:
    result: list[str] = []
    current = ""
    quoted = False
    for char in text:
        if char == '"':
            quoted = not quoted
        if char == "," and not quoted:
            result.append(current.strip())
            current = ""
        else:
            current += char
    if quoted:
        raise ValueError(f"Unclosed string: {text}")
    if current.strip():
        result.append(current.strip())
    return result


def unquote(value: str) -> str:
    if len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
        raise ValueError(f"Expected quoted string: {value}")
    return value[1:-1]


def quote(value: str) -> str:
    if any(c in value for c in '"\r\n'):
        raise ValueError(f"Invalid ONS string: {value!r}")
    return f'"{value}"'


def integer(expression: str) -> int:
    operations = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.floordiv, ast.Mod: operator.mod,
    }

    def evaluate(node: ast.AST) -> int:
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -evaluate(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError(f"Not a constant integer expression: {expression}")

    return evaluate(ast.parse(expression, mode="eval").body)


def text_units(text: str) -> list[tuple[str, int]]:
    units: list[tuple[str, int]] = []
    for part in re.split(r"(\{[^{}]*:[^{}]*\})", text):
        match = re.fullmatch(r"\{([^{}]*):([^{}]*)\}", part)
        if match:
            base = plain_text(match[1])
            ruby = plain_text(match[2].replace(" ", "").replace("　", ""))
            units.append((f"({base}/{ruby})", len(base)))
        else:
            units.extend((plain_text(char), 1) for char in part)
    return units


def plain_text(text: str) -> str:
    # Fullwidth punctuation cannot be interpreted as ONS inline commands.
    return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in text)


def pages(text: str, columns: int = 30, rows: int = 4) -> list[str]:
    lines: list[str] = []
    line = ""
    width = 0
    for unit, size in text_units(text):
        if width + size > columns and line:
            lines.append(line)
            line, width = "", 0
        line += unit
        width += size
    if line:
        lines.append(line)
    return ["\n".join(lines[i:i + rows]) for i in range(0, len(lines), rows)]


def parse_command(line: str) -> tuple[str, list[str]] | None:
    match = re.match(r"^[ \t]+([A-Za-z_][A-Za-z_0-9]*)(?:[ \t]+(.*))?$", line.rstrip())
    if not match:
        return None
    return match[1].lower(), split_args(match[2] or "")


class Converter:
    def __init__(
        self, source: Path, output: Path, bgm_pairs: dict[tuple[str, str], str],
    ) -> None:
        self.source = source.resolve()
        self.output = output.resolve()
        self.bgm_pairs = bgm_pairs
        for folder in ("bgm", "data", "grp", "se", "snr", "voice"):
            if not (self.source / folder).is_dir():
                raise FileNotFoundError(self.source / folder)
        if self.output == self.source or self.source in self.output.parents:
            raise ValueError("Output must be outside the source folder")
        self.scripts = {
            p.stem.casefold(): p for p in sorted((self.source / "snr").glob("*.txt"))
        }
        self.texts = {
            name: path.read_text(encoding="cp932")
            for name, path in self.scripts.items()
        }
        self.files = {
            folder: {p.name.casefold(): p for p in (self.source / folder).iterdir() if p.is_file()}
            for folder in ("grp", "bgm", "data", "se", "voice")
        }
        reachable = {"title"}
        pending = ["title"]
        while pending:
            name = pending.pop()
            for line in self.texts.get(name, "").splitlines():
                command = parse_command(line)
                if command and command[0] in ("sub", "sptload"):
                    target = unquote(command[1][0]).casefold().removesuffix(".txt")
                    if target in self.texts and target not in reachable:
                        reachable.add(target)
                        pending.append(target)
        self.regular = [name for name in self.scripts if name in reachable]
        self.excluded = [name for name in self.scripts if name not in reachable and not name.startswith("anm")]
        self.entries = {name: f"s{i:04d}" for i, name in enumerate(self.regular)}
        self.labels: dict[tuple[str, str], str] = {}
        self.missing_labels: dict[tuple[str, str], str] = {}
        label_id = 0
        for name in self.regular:
            for label in re.findall(r"^[ \t]*\[([^\]]+)\]", self.texts[name], re.M):
                key = (name, label.casefold())
                if key in self.labels:
                    raise ValueError(f"Duplicate label: {name} [{label}]")
                self.labels[key] = f"x{label_id:x}"
                label_id += 1
        variables = set(re.findall(r"@([A-Za-z_]*\d+|[A-Za-z_]+)", "\n".join(
            self.texts[name] for name in self.regular
        )))
        local = sorted((v for v in variables if not re.fullmatch(r"G\d+", v)), key=lambda v: (len(v), v))
        if len(local) > 200:
            raise ValueError("Too many source local variables")
        self.variables = {v: i for i, v in enumerate(local)}
        self.variables.update({v: 200 + int(v[1:]) for v in variables if re.fullmatch(r"G\d+", v)})
        if any(v >= 300 for k, v in self.variables.items() if k.startswith("G")):
            raise ValueError("Source globals overlap runtime variables")
        self.issues: list[Issue] = []
        self.commands: Counter[str] = Counter()
        self.linked: dict[Path, str] = {}
        self.generated: dict[str, str] = {}
        self.location = ("", 0)
        self.dialogues = 0
        self.voiced = 0
        self.source_lines: dict[str, list[int]] = {}

    def issue(self, kind: str, detail: str) -> None:
        self.issues.append(Issue(kind, *self.location, detail))

    def expression(self, text: str) -> str:
        text = text.replace("%", "MOD")
        result = re.sub(
            r"@([A-Za-z_]*\d+|[A-Za-z_]+)",
            lambda m: f"%{self.variables[m[1]]}",
            text,
        ).replace(" ", "").replace("\t", "")
        if not re.fullmatch(r"(?:%\d+|\d+|MOD|[+\-*/()])+", result):
            raise ValueError(f"Invalid numeric expression: {text}")
        return result.replace("MOD", " mod ")

    def target(self, script: str, label: str | None = None) -> str:
        name = script.casefold().removesuffix(".txt")
        if label is None:
            if name not in self.entries:
                raise ValueError(f"Missing script: {script}")
            return "*" + self.entries[name]
        key = name, label.casefold()
        if key not in self.labels:
            self.issue("missing_label", f"{script} [{label}]")
            if key not in self.missing_labels:
                self.missing_labels[key] = f"missing_l{len(self.missing_labels):04d}"
            return "*" + self.missing_labels[key]
        return "*" + self.labels[key]

    def link(self, path: Path) -> str:
        if path in self.linked:
            return self.linked[path]
        if self.source not in path.resolve().parents:
            raise ValueError(f"Asset outside game_file: {path}")
        relative = Path("assets") / path.relative_to(self.source)
        dest = self.output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            try:
                os.link(path, dest)
            except OSError:
                shutil.copy2(path, dest)
        elif not os.path.samefile(path, dest):
            if dest.read_bytes() != path.read_bytes():
                raise FileExistsError(f"Conflicting output asset: {dest}")
        result = str(relative)
        self.linked[path] = result
        return result

    def generated_path(self, key: str) -> tuple[str, Path]:
        name = hashlib.sha256(key.encode()).hexdigest()[:20] + ".png"
        relative = str(Path("assets") / "generated" / name)
        dest = self.output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        return relative, dest

    def placeholder(self, description: str) -> str:
        relative, dest = self.generated_path("missing:" + description)
        if not dest.exists():
            image = Image.new("RGBA", (800, 600), (40, 0, 0, 255))
            draw = ImageDraw.Draw(image)
            draw.text((25, 25), "MISSING ASSET", fill="yellow")
            draw.text((25, 50), description.encode("ascii", "backslashreplace").decode(), fill="white")
            image.save(dest)
        return relative

    def find_asset(self, folder: str, name: str, extension: str) -> Path | None:
        candidates = [name, name + extension]
        if Path(name).suffix:
            candidates.append(str(Path(name).with_suffix(extension)))
        for candidate in candidates:
            path = self.files[folder].get(candidate.casefold())
            if path:
                return path
        return None

    def asset(self, folder: str, name: str, extension: str) -> str | None:
        normalized = name.lstrip("\\/")
        if normalized != name:
            self.issue("source_anomaly", f"Virtual-root asset name: {folder}\\{name} -> {normalized}")
            name = normalized
        path = self.find_asset(folder, name, extension)
        if path is None and folder == "voice" and re.fullmatch(r"SE\d+", name, re.I):
            path = self.find_asset("se", name, extension)
            if path:
                self.issue("source_anomaly", f"VOICE_P references SE asset: {name}")
        if path is None:
            self.issue("missing_asset", f"{folder}\\{name}")
            return self.placeholder(f"{folder}\\{name}") if folder == "grp" else None
        return self.link(path)

    def joined_bgm(self, intro: Path, loop: Path) -> str:
        key = intro.name.casefold(), loop.name.casefold()
        try:
            return self.bgm_pairs[key]
        except KeyError as exc:
            raise FileNotFoundError(
                f"No prejoined BGM for {intro.name} and {loop.name}"
            ) from exc

    def image(self, name: str) -> str:
        if name in ("黒", "白"):
            color = "#000000" if name == "黒" else "#ffffff"
            return f":c;>800,600,{color}"
        path = self.asset("grp", name, ".png")
        if path is None:
            raise ValueError(f"Image resolution failed: {name}")
        return ":a;" + path

    def image_load_reference(self, image: str) -> tuple[str, int]:
        if image.startswith(":c;"):
            return image, 2
        path = image[3:]
        mode = 1 if Path(path).parent.name.casefold() == "generated" else 0
        return Path(path).name, mode

    def animation(self, name: str) -> str:
        key = name.casefold().removesuffix(".txt")
        self.issue("approximation", f"AnmLoad {name}: first visible frame (no parallel animation)")
        if key in self.generated:
            return ":a;" + self.generated[key]
        if key not in self.texts:
            self.issue("missing_asset", f"snr\\{name}")
            return ":a;" + self.placeholder(name)
        loaded: dict[int, Image.Image] = {}
        cells: dict[int, tuple[int, int, int, int, int, int, int]] = {}
        visible: dict[int, bool] = {}
        frame = Image.new("RGBA", (800, 600))
        for line in self.texts[key].splitlines():
            cmd = parse_command(line)
            if not cmd:
                continue
            op, args = cmd
            if op in ("wait", "end"):
                break
            if op == "grpload":
                image_name = unquote(args[1])
                path = self.find_asset("grp", image_name, ".png")
                if path is None:
                    self.issue("missing_asset", f"animation {name}: {image_name}")
                else:
                    with Image.open(path) as source:
                        loaded[integer(args[0])] = source.convert("RGBA")
            elif op == "setgrpcell":
                values = [integer(arg) for arg in args]
                cells[values[0]] = (
                    values[1], values[2], values[3], values[4],
                    values[5], values[6], values[7],
                )
            elif op == "setgrpvisible":
                visible[integer(args[0])] = bool(integer(args[1]))
        for slot in sorted(cells):
            if not visible.get(slot):
                continue
            source_slot, x1, y1, x2, y2, x, y = cells[slot]
            if source_slot not in loaded:
                continue
            image = loaded[source_slot]
            x2 = image.width if x2 < 0 else x2
            y2 = image.height if y2 < 0 else y2
            image = image.crop((x1, y1, x2, y2))
            frame.alpha_composite(image, (x, y))
        if frame.getbbox() is None:
            self.issue("approximation", f"Animation {name}: no static visible frame")
        relative, dest = self.generated_path("animation:" + key)
        frame.save(dest)
        self.generated[key] = relative
        return ":a;" + relative

    def config_background(self, title: str) -> str:
        """Darkened copy of the title image, used behind the CONFIG screen."""
        relative, dest = self.generated_path("config_background:" + title)
        if not dest.exists():
            with Image.open(self.output / title) as source:
                dark = ImageEnhance.Brightness(source.convert("RGB")).enhance(0.25)
                dark.save(dest)
        return relative

    def sample(self, folder: str) -> str | None:
        """Volume preview asset: SE003 for SE, sa0567 for voice, first OGG for BGM."""
        if folder in ("se", "voice"):
            name = "SE003" if folder == "se" else "sa0567"
            audio = self.asset(folder, name, ".ogg")
            if audio is None:
                raise FileNotFoundError(self.source / folder / (name + ".ogg"))
            return audio
        paths = sorted(p for p in self.files[folder].values() if p.suffix.casefold() == ".ogg")
        return self.link(paths[0]) if paths else None

    def title_ui(self, title: str) -> str:
        """ONS code for the title menu (button sprites) and the CONFIG screen."""
        white = ("#ffffff",)
        arrow_colors = ("#ffffff", "#ffd966")       # normal / mouse-over
        size = 24                                   # same as in-game text and right-click menu
        rows = (("ＢＧＭ", "bgm"), ("ＳＥ", "se"), ("ＶＯＩＣＥ", "voice"))
        config_bg = self.config_background(title)
        background = self.image("title_01")
        music_intro = self.find_asset("bgm", "BGM01_intro", ".ogg")
        if music_intro is None:
            raise FileNotFoundError(self.source / "bgm" / "BGM01_intro.ogg")
        music_loop = self.find_asset("bgm", "BGM01_loop", ".ogg")
        if music_loop is None:
            raise FileNotFoundError(self.source / "bgm" / "BGM01_loop.ogg")
        music_joined = self.joined_bgm(music_intro, music_loop)
        button_se = self.asset("se", "SE001", ".ogg")
        if button_se is None:
            raise FileNotFoundError(self.source / "se" / "SE001.ogg")
        out: list[str] = []

        # ---- title menu: grp/<name>_state1/2/3.png written by crop_buttons -----
        # state1 normal, state2 mouse-over, state3 pressed; one sprite per state.
        # Top-left (x, y) of each button image. Edit by hand: state1/2/3 of a button
        # all use the same top-left, so the wider mouse-over image grows to the right.
        positions = {
            "start":    (24, 280),
            "continue": (24, 280+56*1),
            "config":   (24, 280+56*2),
            "gallery":  (24, 280+56*3),
            "exit":     (24, 280+56*4),
        }
        names = list(positions)
        labels = ("title_begin", "title_load", "title_config", "title_gallery", "title_exit")
        grp = Path("assets") / "grp"
        self.issue("approximation", "Gallery button: no gallery mode, shows a notice screen")
        out += [
            "*title_menu", "saveoff", "csp -1", "gosub *title_audio_stop",
            'mov $310,""', 'mov $311,""',
            "gosub *title_music_start",
            f"lsp 240,{quote(background)},0,0", "print 2", "wait 500",
            "*title_menu_screen", "csp -1",
            f'lsph 240,{quote(":a;" + title)},0,0', "vsp 240,1",
        ]
        # sprites: normal 10-14, mouse-over 15-19, pressed 21-25; buttons 30-34
        for i, name in enumerate(names):
            x, y = positions[name]
            for sprite, command, k in ((10 + i, "lsp", 1), (15 + i, "lsph", 2), (21 + i, "lsph", 3)):
                path = quote(f":a;{grp / f'{name}_state{k}.png'}")
                out.append(f"{command} {sprite},{path},{x},{y}")
        rest = lambda skip: "".join(f"P{10 + j}C{15 + j}" for j in range(5) if j != skip)
        out += ["print 2", "wait 500", "*title_menu_loop", "btndef clear"]
        out += [f'exbtn {10 + i},{30 + i},"{rest(i)}C{10 + i}P{15 + i}"' for i in range(5)]
        out += [f'exbtn_d "{rest(-1)}"', "btnwait %359", "if %359<=0 goto *title_menu_loop"]
        out += [f"if %359={30 + i} vsp {10 + i},0:vsp {15 + i},0:vsp {21 + i},1" for i in range(5)]
        out += [f"ap 0,1,0,{quote(Path(button_se).name)}", "print 1", "wait 650"]
        out += [f"if %359={30 + i} goto *{label}" for i, label in enumerate(labels)]
        out += [
            "goto *title_menu_loop",
            "*title_exit", "gosub *title_audio_stop", "csp -1", "bg black,2", "end",
            # the menu sprites would overlap the engine's load list, so clear them
            "*title_load", "csp -1",
            f'lsph 240,{quote(":a;" + config_bg)},0,0', "vsp 240,1", "print 1",
            "systemcall load", "goto *title_menu_screen",
            "*title_gallery", "csp -1",
            f'lsph 240,{quote(":a;" + config_bg)},0,0', "vsp 240,1",
            string_sprite(2, "鑑賞モードは未対応です", None, 280, size, white),
            "print 1", "click", "goto *title_menu_screen",
            "*title_audio_stop", "loopbgmstop", "bgmstop",
            "for %320=0 to 49", "dwavestop %320", "next", "return",
            "*title_music_start",
            f"pc {quote(music_joined)}", "return",
        ]

        # ---- CONFIG: BGM / SE / VOICE volume (0-100 in steps of 10) -----------
        # %350-%352 hold the steps 0-10, %353 is "initialised" (see *apply_volume).
        out += [
            "*title_config", "gosub *title_audio_stop", "csp -1",
            f'lsph 240,{quote(":a;" + config_bg)},0,0', "vsp 240,1",
            "gosub *title_config_sprites", "print 2",
            "*title_config_loop", "btndef clear",
        ]
        arrows = [12, 13, 14, 15, 16, 17]
        out += [f"spbtn {n},{n}" for n in arrows + [18, 19]]
        out += ["btnwait %359",
                "if %359=-1 goto *title_config_exit",
                "if %359<=0 goto *title_config_loop",
                "if %359=19 goto *title_config_exit",
                "mov %360,0"]
        for i in range(len(rows)):
            var = 350 + i
            out.append(f"if %359={12 + 2 * i} if %{var}>0 sub %{var},1:mov %360,{i + 1}")
            out.append(f"if %359={13 + 2 * i} if %{var}<10 add %{var},1:mov %360,{i + 1}")
        out += [
            "if %359=18 mov %350,10:mov %351,10:mov %352,10",
            "gosub *apply_volume",
            "if %360=1 gosub *title_test_bgm",
            "if %360=2 gosub *title_test_se",
            "if %360=3 gosub *title_test_voice",
            "gosub *title_config_sprites", "print 1", "goto *title_config_loop",
            "*title_config_exit", "gosub *title_audio_stop",
            "gosub *title_music_start", "goto *title_menu_screen",
        ]

        # a sample is played right after a change so the new level can be heard
        for name in ("bgm", "se", "voice"):
            audio = self.sample(name)
            out.append(f"*title_test_{name}")
            if audio:
                if name == "bgm":
                    out.append(f"pb {quote(Path(audio).name)}")
                else:
                    mode, channel = (0, 1) if name == "se" else (1, 0)
                    out.append(f"ap {mode},{channel},0,{quote(Path(audio).name)}")
            out.append("return")

        out += ["*title_config_bar", 'mov $380,""', "for %357=0 to 10",
                'if %357=%356 add $380,"○"', 'if %357!=%356 add $380,"―"',
                "next", "return"]

        out += ["*title_config_sprites",
                string_sprite(2, "［ＣＯＮＦＩＧ］", 60, 60, size, white)]
        z = size
        for i, (label, _) in enumerate(rows):
            y = 180 + i * 90
            out += [
                string_sprite(3 + i, label, 80, y, z, white),
                f"mov %356,%{350 + i}", "gosub *title_config_bar",
                f"mov %358,%{350 + i}*10", "itoa2 $381,%358",
                f"strsp {6 + i},$380,336,{y},12,1,{z},{z},0,0,0,1,#ffffff",
                f"strsp {9 + i},$381,660,{y},4,1,{z},{z},0,0,0,1,#ffffff",
                string_sprite(12 + 2 * i, "＜", 300, y, z, arrow_colors),
                string_sprite(13 + 2 * i, "＞", 612, y, z, arrow_colors),
            ]
        out += [string_sprite(18, "ＲＥＳＥＴ", 220, 480, z, arrow_colors),
                string_sprite(19, "ＢＡＣＫ", 480, 480, z, arrow_colors), "return"]
        return "\n".join(out)

    def dialogue(self, text: str) -> list[str]:
        name, voice, body = "", "", text.strip()
        match = re.match(r"^([^：]*?)(?:\(([^()]*)\))?：(.*)$", body)
        if match:
            name, voice, body = match[1], match[2] or "", match[3]
        output: list[str] = []
        for i, page in enumerate(pages(body)):
            output.append("print 1")
            if i == 0:
                output.append("mov %332,1")
                output.append(f"mov $310,{quote(plain_text(name))}")
                audio = self.asset("voice", voice, ".ogg") if voice else ""
                if audio:
                    self.voiced += 1
                audio_name = Path(audio).name if audio else ""
                audio_mode = int(Path(audio).parent.name.casefold() == "voice") if audio else 0
                output.append(f"mov %334,{audio_mode}")
                output.append(f"mov $311,{quote(audio_name)}")
            output.append(page + "\\")
            self.dialogues += 1
        return output

    def effect(self, duration: str) -> list[str]:
        return [f"ds {self.expression(duration)}"]

    def command(self, script: str, op: str, args: list[str]) -> list[str]:
        self.commands[op] += 1
        e = self.expression
        if op == "sub":
            return [f"gosub {self.target(unquote(args[0]), unquote(args[1]))}"]
        if op == "goto":
            return [f"goto {self.target(script, unquote(args[0]))}"]
        if op == "sptload":
            name = unquote(args[0])
            if name.casefold().removesuffix(".txt") not in self.entries:
                self.issue("missing_script", name)
                return [f"ms {quote(name)}"]
            return [f"goto {self.target(name)}"]
        if op == "return":
            return ["return"]
        if op == "if":
            comparison = unquote(args[1])
            if comparison not in ("==", "!=", ">=", "<=", ">", "<"):
                raise ValueError(f"Unknown comparison: {comparison}")
            return [f"if {e(args[0])}{comparison.replace('==', '=')}{e(args[2])} goto "
                    + self.target(script, unquote(args[3]))]
        if op == "switch":
            return [f"if {e(args[0])}={i} goto {self.target(script, unquote(label))}"
                    for i, label in enumerate(args[1:])]
        if op == "bg":
            image, mode = self.image_load_reference(self.image(unquote(args[0])))
            return [f"ll 0,0,0,{quote(image)},{mode}"]
        if op == "grpload":
            image, mode = self.image_load_reference(self.image(unquote(args[3])))
            return [f"ll {e(args[0])},{e(args[1])},{e(args[2])},"
                    f"{quote(image)},{mode}"]
        if op == "anmload":
            image, mode = self.image_load_reference(self.animation(unquote(args[1])))
            return [f"ll {e(args[0])},0,0,{quote(image)},{mode}"]
        if op == "grpvisible":
            return [f"lv {e(args[0])},{e(args[1])}"]
        if op == "gr":
            return [f"lc {e(args[0])}"]
        if op in ("setgrppos", "setgrpputpos"):
            if len(args) > 3 and args[3] != "0":
                self.issue("approximation", f"{op}: endpoint position, no interpolation")
            return [f"lp {e(args[0])},{e(args[1])},{e(args[2])}"]
        if op == "setrate":
            if len(args) > 2 and args[2] != "0":
                self.issue("approximation", "SetRate: endpoint alpha, crossfade at next draw")
            return [f"la {e(args[0])},{e(args[1])}"]
        if op in ("grpdraw", "grayscalefade", "grayscalewipe", "mosaicchange", "braind"):
            if op != "grpdraw":
                self.issue("approximation", f"{op}: standard crossfade")
            return self.effect(args[0])
        if op == "grayscaledelayfade":
            self.issue("approximation", "GrayScaleDelayFade: standard crossfade")
            return self.effect(args[-1])
        if op == "grpeffectstart":
            self.issue("approximation", "GrpEffectStart: synchronous crossfade")
            return ["ds 500"]
        if op in ("grpeffectdelete", "grpeffectstop"):
            self.issue("approximation", f"{op}: no parallel effect to cancel")
            return []
        if op == "vibration":
            self.issue("approximation", "Vibration: standard quake")
            return [f"quake 3,{e(args[0])}"]
        if op in ("fadein", "fadeout"):
            self.issue("approximation", f"{op}: overlay crossfade")
            color = "#{:02x}{:02x}{:02x}".format(*(integer(a) for a in args[1:4]))
            # The source FadeOut is a transient flash: the next scene draw replaces it.
            if op == "fadeout":
                return ["mov %333,0", f'lsp 20,":c;>800,600,{color}",0,0'] + self.effect(args[0]) + ["mov %333,1"]
            return ["csp 20", "mov %333,0"] + self.effect(args[0])
        if op in ("clk", "wait"):
            return ["print 1", f"wait {e(args[0])}"]
        if op == "wc":
            return ['mov $310,""', 'mov $311,""', "csp 0", "textoff"]
        if op == "mes":
            return self.dialogue(unquote(args[0]))
        if op == "setinfo":
            return [f"caption {quote(unquote(args[0]) or 'Clover Point for ONScripter')}"]
        if op == "bgm2_p":
            if args[0] != "0" or args[3] != "0":
                self.issue("approximation", "BGM2_P: one music stream; no music crossfade")
            intro = self.find_asset("bgm", unquote(args[1]), ".ogg")
            loop = self.find_asset("bgm", unquote(args[2]), ".ogg")
            if intro and loop:
                return [f"pc {quote(self.joined_bgm(intro, loop))}"]
            for name in (args[1], args[2]):
                self.asset("bgm", unquote(name), ".ogg")
            return ["loopbgmstop", "bgmstop"]
        if op == "bgm_p":
            audio = self.asset("bgm", unquote(args[1]), ".ogg")
            return [f"pb {quote(Path(audio).name)}"] if audio else ["loopbgmstop", "bgmstop"]
        if op == "bgm_s":
            if args[1] != "0":
                self.issue("approximation", "BGM_S: immediate stop (no unsupported bgmfadeout)")
            return ["loopbgmstop", "bgmstop"]
        if op in ("se_p", "voice_p"):
            voice = op == "voice_p"
            if not voice and len(args) > 2 and args[2] != "0":
                self.issue("approximation", "SE_P: no SE fade-in")
            channel = "0" if voice else f"({e(args[0])}+1)"
            audio = self.asset("voice" if voice else "se", unquote(args[0] if voice else args[1]), ".ogg")
            if not audio:
                return [f"dwavestop {channel}"]
            path = self.output / audio
            duration = ogg_duration(path)
            play = "dwaveloop" if not voice and len(args) > 3 and args[3] == "1" else "dwave"
            folder = Path(audio).parent.name.casefold()
            audio_mode = int(folder == "voice")
            loop = int(play == "dwaveloop")
            return [f"ap {audio_mode},{channel},{loop},{quote(Path(audio).name)}", "gettimer %330",
                    f"mov ?2[{channel}],%330+{duration}"]
        if op in ("se_s", "voice_s"):
            if len(args) > 1 and args[1] != "0":
                self.issue("approximation", f"{op}: immediate stop (no SE fade)")
            return ["dwavestop 0" if op == "voice_s" else f"dwavestop ({e(args[0])}+1)"]
        if op in ("se_w", "voice_w"):
            return [f"wa {'0' if op == 'voice_w' else '(' + e(args[0]) + '+1)'}"]
        if op == "setselbtn":
            return [f"mov ${340 + integer(args[0])},{quote(plain_text(unquote(args[3])))}"]
        if op == "enableselbtn":
            return [f"mov ?1[{e(args[0])}],{e(args[1])}"]
        if op == "select":
            # csel does not support disabled items; build a select for each enabled mask.
            count = len(args)
            result = ['mov $310,""', 'mov $311,""', "mov %331,0"]
            for i in range(count):
                result.append(f"if ?1[{i}]!=0 add %331,{1 << i}")
            for mask in range(1, 1 << count):
                choices = ",".join(f"${340+i},{self.target(script, unquote(args[i]))}"
                                   for i in range(count) if mask & (1 << i))
                result.append(f"if %331={mask} select {choices}")
            result += ['ms "No enabled choice"']
            return result
        if op == "title":
            return ["gosub *title_menu"]
        if op == "playmovie":
            self.issue("missing_asset", f"Movie not supplied: {unquote(args[-1])}")
            return ["; Movie unavailable"]
        if op in ("enablemenu", "enablezoom", "setmeswnd"):
            self.issue("approximation", f"{op}: ONS standard UI")
            return []
        if op == "setmode":
            self.issue("approximation", f"SetMode {','.join(args)}: standard dialogue mode")
            return []
        if op == "setgrpblendtype" and args[1] == "5":
            # Standard ONS sprites cannot add light; normal alpha would tint the scene gray.
            self.issue("approximation", "setgrpblendtype 5: additive light overlay omitted")
            return [f"lc {e(args[0])}"]
        if op in ("setgrpblendtype", "eftsnow", "anmwait", "anmjump"):
            self.issue("approximation", f"{op}: static-frame compatibility mode")
            return []
        raise ValueError(f"Unsupported command: {op} {args}")

    def compile_script(self, script: str) -> list[str]:
        output = [self.target(script)]
        self.source_lines[script] = []
        for number, line in enumerate(self.texts[script].splitlines(), 1):
            self.location = (self.scripts[script].name, number)
            text = line.strip()
            if not text or text.startswith((";", "//")):
                continue
            label = re.fullmatch(r"\[([^\]]+)\]", text)
            if label:
                output.append(self.target(script, label[1]))
                continue
            assignment = re.fullmatch(r"@([A-Za-z_]*\d+|[A-Za-z_]+)\s*=\s*(.*)", text)
            try:
                if assignment:
                    value = assignment[2]
                    if not value and script in ("tu340-01", "tu370-01") and assignment[1] == "4":
                        value = "5"
                        self.issue("source_anomaly", "Empty @4 assignment: set to 5 (no calendar icon), user approved")
                    output.append(f"mov %{self.variables[assignment[1]]},{self.expression(value)}")
                else:
                    command = parse_command(line)
                    if command:
                        op, args = command
                        for i, arg in enumerate(args):
                            trailing = re.fullmatch(r'("[^"]*")([^\x00-\x7f]+)', arg)
                            if trailing:
                                self.issue("source_anomaly", f"Trailing text after quoted argument: {arg}")
                                args[i] = trailing[1]
                        output.extend(self.command(script, op, args))
                    else:
                        output.extend(self.dialogue(line))
                        self.source_lines[script].append(number)
            except (ValueError, KeyError, IndexError) as exc:
                raise ValueError(f"{self.location[0]}:{number}: {text}\n{exc}") from exc
        # Scripts normally transfer explicitly; never fall through into another file.
        output.append("reset")
        return output

    def run(self) -> dict[str, object]:
        if "title" not in self.entries:
            raise FileNotFoundError("snr\\title.txt")
        self.output.mkdir(parents=True, exist_ok=True)
        self.location = ("<runtime>", 0)
        title = self.asset("grp", "title_02", ".png")
        if title is None:
            raise FileNotFoundError("grp\\title_02.png")
        sheet = self.find_asset("grp", "title_bg", ".png")
        if sheet is None:
            raise FileNotFoundError("grp\\title_bg.png")
        crop_buttons(sheet, self.output / "assets" / "grp")
        boot_lines = ["saveoff", "textoff", "csp -1", "bg black,1", "wait 500"]
        for name in ("CSA_R-18_A", "CSA_R-18_B", "meteorロゴ"):
            boot_lines += [f"lsp 240,{quote(self.image(name))},0,0", "print 2", "wait 500"]
        boot_lines += ["csp 240", "bg black,2", "wait 500",
                       f"mov %{self.variables['52']},2", f"goto {self.target('title')}"]
        boot = "\n".join(boot_lines)
        runtime = default_txt().replace("__BOOT__", boot).replace("__TITLE_UI__", self.title_ui(title))
        parts = [runtime]
        for name in self.regular:
            parts.append("\n".join(self.compile_script(name)))
        for (name, label), target in self.missing_labels.items():
            parts.append(f"*{target}\nms {quote(name + ':' + label)}")
        script = "\n".join(parts) + "\n"
        validate_script(script)
        # CP932 is Windows Shift-JIS; strict encoding never discards game text.
        encoded = script.encode("cp932")
        report: dict[str, object] = {
            "source": str(self.source), "encoding": "cp932 (Windows Shift-JIS)",
            "scripts": len(self.regular), "animation_frames": len(self.generated),
            "excluded_unreferenced_scripts": self.excluded,
            "text_pages": self.dialogues, "voiced_pages": self.voiced,
            "assets": len(self.linked) + len(self.bgm_pairs), "commands": dict(self.commands),
            "issue_counts": dict(Counter(issue.kind for issue in self.issues)),
            "issues": [asdict(issue) for issue in self.issues],
            "script_labels": self.entries, "variables": self.variables,
            "source_text_lines": self.source_lines,
        }
        pending = self.output / "0.txt.pending"
        pending.write_bytes(encoded)
        pending.replace(self.output / "0.txt")
        return report


def ogg_duration(path: Path) -> int:
    data = path.read_bytes()
    marker = data.find(b"\x01vorbis")
    if marker < 0 or marker + 16 > len(data):
        raise ValueError(f"Not Ogg Vorbis: {path}")
    sample_rate = int.from_bytes(data[marker + 12:marker + 16], "little")
    position, granule = 0, 0
    while position < len(data):
        if data[position:position + 4] != b"OggS" or position + 27 > len(data):
            raise ValueError(f"Invalid Ogg page: {path}")
        count = data[position + 26]
        segments = data[position + 27:position + 27 + count]
        if len(segments) != count:
            raise ValueError(f"Truncated Ogg page: {path}")
        value = int.from_bytes(data[position + 6:position + 14], "little")
        if value != (1 << 64) - 1:
            granule = max(granule, value)
        position += 27 + count + sum(segments)
    if not sample_rate or position != len(data):
        raise ValueError(f"Invalid Ogg stream: {path}")
    return (granule * 1000 + sample_rate - 1) // sample_rate


def validate_script(script: str) -> None:
    labels = re.findall(r"^\*([A-Za-z_0-9]+)\s*$", script, re.M)
    if len(labels) != len(set(labels)):
        raise ValueError("Duplicate output labels")
    references: set[str] = set()
    for line in script.splitlines():
        # Strings and dialogue must not introduce false label references.
        code = re.sub(r'"[^"]*"', '""', line)
        if re.match(r"(?:pretextgosub|gosub|goto|if|select)\b", code):
            references.update(re.findall(r"\*([A-Za-z_0-9]+)", code))
    missing = references - set(labels)
    if missing:
        raise ValueError(f"Unresolved output labels: {sorted(missing)}")
    if not script.startswith(";mode800\n"):
        raise ValueError("Missing ;mode800")


def main(
    values: dict[str, object] | None = None,
    values_ex: dict[str, object] | None = None,
    pre_converted_dir: Path | None = None,
    summary: bool = False,
) -> dict[str, object]:
    base = Path(__file__).resolve().parent
    source = base / "game_file"
    if values and "input_dir" in values:
        supplied = values["input_dir"]
        if not isinstance(supplied, (str, Path)):
            raise TypeError("input_dir must be a path")
        source = Path(supplied)
    output = Path(pre_converted_dir) if pre_converted_dir is not None else base / "testspace"
    if pre_converted_dir is None and not output.is_dir():
        raise FileNotFoundError(f"Output/validation folder must already exist: {output}")
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must be outside the input folder")
    output.mkdir(parents=True, exist_ok=True)
    # Keep extracted originals out of the folder passed to the GUI's packaging step.
    with TemporaryDirectory(prefix="meteor_clp_") as temporary:
        if (values and "input_dir" in values) or any(
            (source / (name + ".dat")).exists() for name in ("bgm", "data", "grp", "se", "snr", "voice")
        ):
            workspace = Path(temporary)
            extract_resource({"input_dir": source}, values_ex or {}, workspace)
            source = workspace / "game_file"
        bgm_pairs = join_bgm_pairs(source, output, bool(values), values_ex or {})
        report = Converter(source, output, bgm_pairs).run()
    if summary:
        print(json.dumps({key: report[key] for key in (
            "scripts", "animation_frames", "text_pages", "voiced_pages", "assets", "issue_counts"
        )}, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and convert game_file data for standard ONScripter")
    parser.add_argument("--input", type=Path, help="folder containing bgm/data/grp/se/snr/voice DAT archives")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "testspace")
    parser.add_argument("--summary", action="store_true", help="print the conversion summary as JSON")
    options = parser.parse_args()
    main(values={"input_dir": options.input} if options.input is not None else None,
         pre_converted_dir=options.output, summary=options.summary)
