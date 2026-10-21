# ============================================================
# LÓGICA DA ESCALA
# ============================================================
# 4 pessoas por turno.
# Dias úteis: 2 das 4 trabalham por dia.
# Final de semana: 2 das 4 fazem o rodízio do período.
# A escala de segunda a sexta é INDEPENDENTE da escala de sábado/domingo.
# ============================================================
import calendar
import datetime as dt
from itertools import combinations

TURNOS = ["DIURNO", "NOTURNO"]
MAX_POR_TURNO = 4


def datas_do_mes(ano, mes):
    ultimo = calendar.monthrange(ano, mes)[1]
    return [dt.date(ano, mes, d) for d in range(1, ultimo + 1)]


def gerar_escala_automatica(pessoas, ano, mes, data_inicio=None):
    """Gera a escala: 2 de 4 nos dias úteis e 2 de 4 no fim de semana."""
    por_turno = {t: [] for t in TURNOS}
    for pessoa in pessoas:
        por_turno.setdefault(pessoa["turno"], []).append(pessoa)

    for turno in TURNOS:
        if len(por_turno[turno]) != MAX_POR_TURNO:
            raise ValueError(
                f"O turno {turno} precisa ter 4 pessoas. "
                f"Atualmente existem {len(por_turno[turno])}."
            )

    datas = datas_do_mes(ano, mes)
    registros = []

    # As seis duplas possíveis entre quatro pessoas.
    # A ordem foi escolhida para distribuir os serviços.
    ordem = [0, 3, 1, 5, 2, 4]

    for turno in TURNOS:
        grupo = por_turno[turno]
        duplas = list(combinations(grupo, 2))

        # ---------------- DIAS ÚTEIS ----------------
        dias_uteis = [d for d in datas if d.weekday() < 5]
        for pos, data in enumerate(dias_uteis):
            dupla = duplas[ordem[pos % len(ordem)]]
            for pessoa in grupo:
                situacao = "SERVIÇO" if pessoa in dupla else "FOLGA"
                registros.append((data.isoformat(), pessoa["id"], situacao, turno))

        # ---------------- FIM DE SEMANA ----------------
        # Um único par fica responsável por sábado + domingo.
        # No próximo fim de semana o par muda.
        domingos = [d for d in datas if d.weekday() == 6]
        for numero, domingo in enumerate(domingos):
            sabado = domingo - dt.timedelta(days=1)
            dupla = duplas[ordem[(numero + 1) % len(ordem)]]

            for data in (sabado, domingo):
                if data.month != mes:
                    continue
                for pessoa in grupo:
                    situacao = "SERVIÇO" if pessoa in dupla else "FOLGA"
                    registros.append((data.isoformat(), pessoa["id"], situacao, turno))

    return registros
