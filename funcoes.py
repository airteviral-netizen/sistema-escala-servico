"""Regras de geração automática da escala de serviço."""
from __future__ import annotations

import calendar
import datetime as dt

TURNOS = ["DIURNO", "NOTURNO"]
# Sábado de referência para manter a rotação contínua entre meses e anos.
SABADO_REFERENCIA = dt.date(2024, 1, 6)


def _dados_fim_de_semana(sabado: dt.date, grupo: list[dict]) -> tuple[list[dict], dt.date]:
    """Retorna o par escalado e o único dia de serviço daquele fim de semana.

    O par A trabalha em uma semana e o par B na semana seguinte. Assim,
    quem trabalhou fica automaticamente fora do fim de semana imediatamente
    seguinte. Cada par alterna entre sábado e domingo em suas participações.
    """
    indice_semana = (sabado - SABADO_REFERENCIA).days // 7
    indice_par = indice_semana % 2

    if indice_par == 0:
        par = grupo[:2]
        ocorrencia_do_par = indice_semana // 2
    else:
        par = grupo[2:4]
        ocorrencia_do_par = (indice_semana - 1) // 2

    dia_servico = sabado if ocorrencia_do_par % 2 == 0 else sabado + dt.timedelta(days=1)
    return par, dia_servico


def gerar_escala_automatica(pessoas: list[dict], ano: int, mes: int) -> list[tuple]:
    """Gera a escala mensal.

    Regras:
    - Segunda a sexta: todos ficam em EXPEDIENTE, exceto quem estiver
      recebendo a folga compensatória do fim de semana anterior.
    - Em cada fim de semana, somente um dia (sábado OU domingo) tem serviço.
    - Nesse único dia, trabalham duas pessoas de cada turno; as outras duas
      ficam de FOLGA. No outro dia do fim de semana, todos ficam de FOLGA.
    - Os pares alternam a cada fim de semana. Quem trabalhou não concorre ao
      fim de semana seguinte.
    - Cada pessoa escalada recebe uma FOLGA COMP. na semana útil seguinte.
      As duas folgas são separadas: primeira pessoa na segunda, segunda pessoa
      na terça-feira.

    A rotação usa uma data de referência fixa para continuar corretamente
    mesmo quando o usuário gera meses separados ou atravessa o ano.
    """
    por_turno = {
        turno: sorted(
            [p for p in pessoas if p.get("turno") == turno],
            key=lambda pessoa: pessoa["id"],
        )
        for turno in TURNOS
    }

    for turno, grupo in por_turno.items():
        if len(grupo) != 4:
            raise ValueError(
                f"O turno {turno} precisa ter exatamente 4 pessoas cadastradas; "
                f"foram encontradas {len(grupo)}."
            )

    primeiro_dia = dt.date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    registros: list[tuple] = []

    for numero_dia in range(1, ultimo_dia + 1):
        data = dt.date(ano, mes, numero_dia)

        for turno, grupo in por_turno.items():
            if data.weekday() < 5:
                # Descobre o sábado que iniciou a semana útil atual.
                sabado_anterior = data - dt.timedelta(days=data.weekday() + 2)
                par_anterior, _ = _dados_fim_de_semana(sabado_anterior, grupo)

                # Uma folga compensatória por pessoa, em dias diferentes.
                compensacoes = {}
                for indice, pessoa in enumerate(par_anterior):
                    dia_folga = indice  # 0 = segunda; 1 = terça.
                    compensacoes[pessoa["id"]] = dia_folga

                for pessoa in grupo:
                    situacao = (
                        "FOLGA COMP."
                        if pessoa["id"] in compensacoes
                        and data.weekday() == compensacoes[pessoa["id"]]
                        else "EXPEDIENTE"
                    )
                    registros.append((data.isoformat(), pessoa["id"], situacao, turno))
                continue

            # Identifica o sábado do fim de semana atual.
            sabado = data if data.weekday() == 5 else data - dt.timedelta(days=1)
            par, dia_servico = _dados_fim_de_semana(sabado, grupo)
            ids_em_servico = {pessoa["id"] for pessoa in par} if data == dia_servico else set()

            for pessoa in grupo:
                situacao = "SERVIÇO" if pessoa["id"] in ids_em_servico else "FOLGA"
                registros.append((data.isoformat(), pessoa["id"], situacao, turno))

    return registros
