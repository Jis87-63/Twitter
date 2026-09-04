#!/usr/bin/env python3
"""Painel local para organizar contas X autorizadas.

Não cria contas, não automatiza logins e não armazena senhas/tokens. Use somente
para contas que você administra e conecte integrações apenas pela API oficial.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DB = Path.home() / ".xpanel" / "accounts.db"
ALLOWED_STATUS = {"ativa", "pausada", "arquivada"}


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY, handle TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'ativa'
          CHECK(status IN ('ativa','pausada','arquivada')),
        owner TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY, occurred_at TEXT NOT NULL, action TEXT NOT NULL,
        handle TEXT NOT NULL, details TEXT NOT NULL DEFAULT ''
    )""")
    return db


def clean_handle(value: str) -> str:
    value = value.strip().lstrip("@")
    if not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for c in value):
        raise ValueError("handle inválido: use apenas letras, números e _")
    return value


def audit(db: sqlite3.Connection, action: str, handle: str, details: str = "") -> None:
    db.execute("INSERT INTO audit_log(occurred_at, action, handle, details) VALUES (?, ?, ?, ?)",
               (now(), action, handle, details))


def add(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    handle = clean_handle(args.handle)
    stamp = now()
    db.execute("INSERT INTO accounts(handle, display_name, status, owner, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (handle, args.name or "", args.status, args.owner or "", args.notes or "", stamp, stamp))
    audit(db, "adicionada", handle, args.owner or "")
    db.commit(); print(f"✓ @{handle} adicionada como {args.status}.")


def rows(db: sqlite3.Connection, status: str | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM accounts"; params: tuple[str, ...] = ()
    if status: sql += " WHERE status = ?"; params = (status,)
    return list(db.execute(sql + " ORDER BY handle COLLATE NOCASE", params))


def print_table(items: list[sqlite3.Row]) -> None:
    if not items: print("Nenhuma conta encontrada."); return
    headings = ("HANDLE", "NOME", "STATUS", "RESPONSÁVEL", "ATUALIZADA")
    data = [("@" + r["handle"], r["display_name"] or "—", r["status"], r["owner"] or "—", r["updated_at"].replace("+00:00", "Z")) for r in items]
    widths = [max(len(h), *(len(row[i]) for row in data)) for i, h in enumerate(headings)]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(line); print("|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headings)) + "|"); print(line)
    for row in data: print("|" + "|".join(f" {v:<{widths[i]}} " for i, v in enumerate(row)) + "|")
    print(line)


def list_accounts(db: sqlite3.Connection, args: argparse.Namespace) -> None: print_table(rows(db, args.status))


def set_status(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    handle = clean_handle(args.handle)
    result = db.execute("UPDATE accounts SET status=?, updated_at=? WHERE handle=?", (args.status, now(), handle))
    if not result.rowcount: raise ValueError(f"@{handle} não encontrada")
    audit(db, "status", handle, args.status); db.commit(); print(f"✓ @{handle}: {args.status}.")


def show(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    handle = clean_handle(args.handle); row = db.execute("SELECT * FROM accounts WHERE handle=?", (handle,)).fetchone()
    if not row: raise ValueError(f"@{handle} não encontrada")
    for label, key in (("Handle", "handle"), ("Nome", "display_name"), ("Status", "status"), ("Responsável", "owner"), ("Notas", "notes"), ("Criada no painel", "created_at"), ("Atualizada", "updated_at")):
        print(f"{label:18} {('@' if key == 'handle' else '')}{row[key] or '—'}")


def dashboard(db: sqlite3.Connection, _args: argparse.Namespace) -> None:
    counts = {s: db.execute("SELECT COUNT(*) FROM accounts WHERE status=?", (s,)).fetchone()[0] for s in ALLOWED_STATUS}
    total = sum(counts.values())
    print("\n╔════════════════ X PANEL • LOCAL ════════════════╗")
    print(f"║ Contas registradas: {total:<29}║")
    print(f"║ Ativas: {counts['ativa']:<8} Pausadas: {counts['pausada']:<8}║")
    print(f"║ Arquivadas: {counts['arquivada']:<28}║")
    print("╚══════════════════════════════════════════════════╝")
    print("Somente contas autorizadas • sem senhas ou automação\n")
    print_table(rows(db))


def export_csv(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    path = Path(args.file).expanduser(); path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["handle", "display_name", "status", "owner", "notes", "created_at", "updated_at"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows(db))
    print(f"✓ Exportadas {len(rows(db))} contas para {path}.")


def audit_history(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    items = list(db.execute("SELECT occurred_at, action, handle, details FROM audit_log ORDER BY id DESC LIMIT ?", (args.limit,)))
    if not items: print("Nenhum evento de auditoria."); return
    for row in items: print(f"{row['occurred_at']} | @{row['handle']} | {row['action']} {row['details']}")


def backup(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    destination = Path(args.file).expanduser(); destination.parent.mkdir(parents=True, exist_ok=True); db.commit()
    with sqlite3.connect(destination) as target: db.backup(target)
    print(f"✓ Backup criado em {destination}. Proteja esse arquivo.")


def doctor(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    print("X Panel • diagnóstico local")
    print(f"Banco: {args.db}\nIntegridade SQLite: {db.execute('PRAGMA integrity_check').fetchone()[0]}\nContas: {db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]}")
    print("Segurança: sem credenciais, automação de login ou execução remota de comandos.")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="X Panel — inventário local de contas autorizadas")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="arquivo SQLite (padrão: ~/.xpanel/accounts.db)")
    subs = p.add_subparsers(dest="command", required=True)
    subs.add_parser("dashboard", aliases=["painel"]).set_defaults(func=dashboard)
    a = subs.add_parser("add", help="registrar uma conta existente autorizada"); a.add_argument("handle"); a.add_argument("--name"); a.add_argument("--owner"); a.add_argument("--notes"); a.add_argument("--status", choices=sorted(ALLOWED_STATUS), default="ativa"); a.set_defaults(func=add)
    l = subs.add_parser("list", aliases=["listar"]); l.add_argument("--status", choices=sorted(ALLOWED_STATUS)); l.set_defaults(func=list_accounts)
    s = subs.add_parser("status"); s.add_argument("handle"); s.add_argument("status", choices=sorted(ALLOWED_STATUS)); s.set_defaults(func=set_status)
    sh = subs.add_parser("show", aliases=["ver"]); sh.add_argument("handle"); sh.set_defaults(func=show)
    e = subs.add_parser("export", aliases=["exportar"]); e.add_argument("file"); e.set_defaults(func=export_csv)
    h = subs.add_parser("audit", aliases=["auditoria"], help="mostrar histórico local"); h.add_argument("--limit", type=int, default=20); h.set_defaults(func=audit_history)
    b = subs.add_parser("backup", help="criar cópia local do banco SQLite"); b.add_argument("file"); b.set_defaults(func=backup)
    subs.add_parser("doctor", aliases=["diagnostico"], help="verificar o banco local").set_defaults(func=doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        db = connect(args.db); args.func(db, args); db.close(); return 0
    except (ValueError, sqlite3.IntegrityError) as error:
        print(f"Erro: {error}", file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
