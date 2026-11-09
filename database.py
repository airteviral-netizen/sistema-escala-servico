"""Camada de acesso ao banco de dados SQLite."""
import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).with_name("escalas.db")


def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def iniciar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS militares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT UNIQUE,
                escala TEXT NOT NULL DEFAULT 'Semana + Fim de Semana',
                turno TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                militar_id INTEGER NOT NULL,
                situacao TEXT NOT NULL,
                turno TEXT NOT NULL,
                UNIQUE(data, militar_id),
                FOREIGN KEY(militar_id) REFERENCES militares(id) ON DELETE CASCADE
            )
        """)


def cadastrar_militar(nome, matricula, escala, turno):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO militares(nome, matricula, escala, turno) VALUES (?, ?, ?, ?)",
            (nome.strip(), matricula.strip() or None, escala, turno),
        )


def atualizar_militar(militar_id, nome, matricula, escala, turno):
    with conectar() as conn:
        conn.execute(
            "UPDATE militares SET nome=?, matricula=?, escala=?, turno=? WHERE id=?",
            (nome.strip(), matricula.strip() or None, escala, turno, militar_id),
        )


def excluir_militar(militar_id):
    with conectar() as conn:
        conn.execute("DELETE FROM militares WHERE id=?", (militar_id,))


def listar_militares(apenas_ativos=True):
    with conectar() as conn:
        sql = "SELECT id, nome, COALESCE(matricula,''), escala, turno, ativo FROM militares"
        if apenas_ativos:
            sql += " WHERE ativo=1"
        sql += " ORDER BY turno, nome, id"
        rows = conn.execute(sql).fetchall()
    return [
        {
            "id": row[0], "nome": row[1], "matricula": row[2],
            "escala": row[3], "turno": row[4], "ativo": bool(row[5]),
        }
        for row in rows
    ]


def salvar_escala(registros):
    with conectar() as conn:
        conn.executemany("""
            INSERT INTO escalas(data, militar_id, situacao, turno)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(data, militar_id) DO UPDATE SET
                situacao=excluded.situacao,
                turno=excluded.turno
        """, registros)


def apagar_escala_mes(ano, mes):
    with conectar() as conn:
        conn.execute(
            "DELETE FROM escalas WHERE data LIKE ?",
            (f"{ano:04d}-{mes:02d}-%",),
        )


def buscar_escala_mes(ano, mes):
    with conectar() as conn:
        rows = conn.execute("""
            SELECT e.data, e.militar_id, m.nome, e.situacao, e.turno
            FROM escalas e
            JOIN militares m ON m.id=e.militar_id
            WHERE e.data LIKE ?
            ORDER BY e.data, e.turno, m.nome
        """, (f"{ano:04d}-{mes:02d}-%",)).fetchall()

    resultado = {}
    for data, pessoa_id, nome, situacao, turno in rows:
        resultado.setdefault(data, []).append({
            "militar_id": pessoa_id,
            "nome": nome,
            "situacao": situacao,
            "turno": turno,
        })
    return resultado
