"""
encoding_utils.py
文本编码自动检测，支持 UTF-8 / GB18030 / GBK / Big5 等
"""

from pathlib import Path


def read_text_safe(path: str | Path, fallback_encoding: str = 'utf-8') -> str:
    path = Path(path)
    raw = path.read_bytes()
    try:
        return raw.decode(fallback_encoding)
    except UnicodeDecodeError:
        import chardet
        result = chardet.detect(raw)
        detected = result.get('encoding', 'utf-8')
        if detected.lower() in ('gb2312', 'gbk'):
            detected = 'gb18030'
        return raw.decode(detected)
