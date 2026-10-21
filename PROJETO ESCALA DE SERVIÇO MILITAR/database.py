# ============================================================
# BANCO DE DADOS
# ============================================================

import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).with_name("escalas.db")


def conectar():
    """Abre a conexão com o banco."""
    return sqlite3.connect(DB_NAME)


def iniciar_banco():
    """Cria as tabelas usadas pelo sistema."""
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS militares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT UNIQUE,
                escala TEXT NOT NULL,
                turno TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
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
                FOREIGN KEY(militar_id)
                    REFERENCES militares(id)
                    ON DELETE CASCADE
            )
        """)


def cadastrar_militar(nome, matricula, escala, turno):
    """Cadastra um militar."""
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO militares(nome, matricula, escala, turno)
            VALUES (?, ?, ?, ?)
            """,
            (nome.strip(), matricula.strip() or None, escala, turno)
        )


def atualizar_militar(militar_id, nome, matricula, escala, turno):
    """Atualiza os dados de um militar."""
    with conectar() as conn:
        conn.execute(
            """
            UPDATE militares
            SET nome=?, matricula=?, escala=?, turno=?
            WHERE id=?
            """,
            (nome.strip(), matricula.strip() or None, escala, turno, militar_id)
        )


def excluir_militar(militar_id):
    """Exclui o militar."""
    with conectar() as conn:
        conn.execute("DELETE FROM militares WHERE id=?", (militar_id,))


def listar_militares(apenas_ativos=True):
    """Lista os militares cadastrados."""
    with conectar() as conn:
        sql = """
            SELECT id, nome, COALESCE(matricula, ''), escala, turno, ativo
            FROM militares
        """

        if apenas_ativos:
            sql += " WHERE ativo=1"

        sql += " ORDER BY turno, nome"

        rows = conn.execute(sql).fetchall()

    return [
        {
            "id": r[0],
            "nome": r[1],
            "matricula": r[2],
            "escala": r[3],
            "turno": r[4],
            "ativo": bool(r[5])
        }
        for r in rows
    ]


def salvar_escala(registros):
    """Grava a escala calculada."""
    with conectar() as conn:
        conn.executemany(
            """
            INSERT INTO escalas(data, militar_id, situacao, turno)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(data, militar_id)
            DO UPDATE SET
                situacao=excluded.situacao,
                turno=excluded.turno
            """,
            registros
        )


def apagar_escala_mes(ano, mes):
    """Apaga somente a escala do mês selecionado."""
    prefixo = f"{ano:04d}-{mes:02d}-%"

    with conectar() as conn:
        conn.execute(
            "DELETE FROM escalas WHERE data LIKE ?",
            (prefixo,)
        )


def buscar_escala_mes(ano, mes):
    """Busca a escala do mês e organiza por data."""
    prefixo = f"{ano:04d}-{mes:02d}-%"

    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT e.data, e.militar_id, m.nome,
                   e.situacao, e.turno
            FROM escalas e
            JOIN militares m ON m.id=e.militar_id
            WHERE e.data LIKE ?
            ORDER BY e.data, e.turno, m.nome
            """,
            (prefixo,)
        ).fetchall()

    resultado = {}

    for data, militar_id, nome, situacao, turno in rows:
        resultado.setdefault(data, []).append({
            "militar_id": militar_id,
            "nome": nome,
            "situacao": situacao,
            "turno": turno
        })

    return resultado
