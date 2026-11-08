#!/usr/bin/env python3
"""Рендер шаблонов поместья с приватными переменными (протокол: Docs/TEMPLATING.md).

Разделение правды:
- шаблоны templates/*.j2 — источник правды, в git;
- реальные координаты — ТОЛЬКО Workspace/private/vars/*.json (Workspace/private/
  вне git, per-host, между машинами через git не синхронизируется);
- сгенерированное с реальными значениями — Docs/generated/ (вне git).

Отсутствующая переменная рендерится плейсхолдером <имя>, а не ошибкой: так
repo-режим (артефакт для коммита) не раскрывает и не требует приватных значений.

Режимы:
  python tools/render_templates.py                    # все шаблоны -> Docs/generated/
  python tools/render_templates.py --repo             # все шаблоны с плейсхолдерами
  python tools/render_templates.py templates/x.md.j2 --out PATH [--repo]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from jinja2 import Environment, Undefined
except ImportError:  # pragma: no cover
    sys.exit("jinja2 не установлен: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
VARS_DIR = ROOT / "Workspace" / "private" / "vars"
OUT_DIR = ROOT / "Docs" / "generated"


class PlaceholderUndefined(Undefined):
    """Отсутствующая переменная -> плейсхолдер <имя> (repo-режим)."""

    def __str__(self) -> str:
        return f"<{self._undefined_name}>"


def load_vars(vars_dir: Path = VARS_DIR) -> dict:
    """Слить все *.json из каталога переменных (по алфавиту, позже перетирает раньше)."""
    merged: dict = {}
    if not vars_dir.is_dir():
        return merged
    for path in sorted(vars_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: ожидается JSON-объект, получено {type(data).__name__}")
        merged.update(data)
    return merged


def render_string(text: str, variables: dict, repo_mode: bool = False) -> str:
    """Отрендерить шаблон; в repo-режиме переменные игнорируются (всё в плейсхолдеры)."""
    env = Environment(
        undefined=PlaceholderUndefined,
        keep_trailing_newline=True,
        autoescape=False,  # markdown-доки, не html
    )
    return env.from_string(text).render({} if repo_mode else variables)


def render_file(src: Path, dst: Path, variables: dict, repo_mode: bool = False) -> str:
    """Отрендерить один файл и записать результат (возвращает текст)."""
    text = render_string(src.read_text(encoding="utf-8"), variables, repo_mode)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    return text


def _output_name(src: Path) -> str:
    return src.name[: -len(".j2")] if src.name.endswith(".j2") else src.name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("template", nargs="?", help="один шаблон (по умолчанию — все)")
    parser.add_argument("--out", help="куда писать (только с template)")
    parser.add_argument("--repo", action="store_true", help="repo-режим: все переменные -> <плейсхолдеры>")
    parser.add_argument("--vars-dir", default=str(VARS_DIR), help="каталог приватных переменных")
    parser.add_argument("--out-dir", default=str(OUT_DIR), help="каталог вывода по умолчанию")
    args = parser.parse_args()

    variables = {} if args.repo else load_vars(Path(args.vars_dir))
    if args.template:
        src = Path(args.template)
        if not src.is_absolute():
            src = ROOT / src
        if not args.out:
            parser.error("--out обязателен при одиночном шаблоне (или запустите без аргументов)")
        dst = Path(args.out)
        if not dst.is_absolute():
            dst = ROOT / dst
        render_file(src, dst, variables, args.repo)
        print(f"OK {src.name} -> {dst}")
        return 0

    sources = sorted(TEMPLATES_DIR.glob("*.j2"))
    if not sources:
        print(f"Шаблонов нет в {TEMPLATES_DIR}")
        return 1
    for src in sources:
        dst = Path(args.out_dir) / _output_name(src)
        render_file(src, dst, variables, args.repo)
        print(f"OK {src.name} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
