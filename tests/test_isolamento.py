"""LST-21: o sandbox de uma demanda não alcança nada fora do próprio staging, mesmo sem a trava de SQL."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import pytest

from lastro.config import RAIZ, carregar
from lastro.conectores import Fonte, Sandbox

EXEMPLO = RAIZ / "exemplos" / "orcamentos.csv"


@pytest.fixture
def dois_tenants(tmp_path: Path):
    acme = tmp_path / "tenants" / "acme"
    outra = tmp_path / "tenants" / "outra"
    for t in (acme, outra):
        (t / "fontes").mkdir(parents=True)
    shutil.copy(EXEMPLO, acme / "fontes" / "orcamentos.csv")
    segredo = outra / "fontes" / "segredo.csv"
    segredo.write_text("cliente,valor\nconcorrente,999\n")
    demanda = acme / "demandas" / "1"
    sb = Sandbox(demanda / "staging", gravavel=demanda)
    sb.anexar(Fonte("orcamentos", "arquivo", str(acme / "fontes" / "orcamentos.csv")))
    sb.travar()
    yield sb, segredo
    sb.fechar()


def test_fonte_continua_consultavel_depois_de_travar(dois_tenants):
    sb, _ = dois_tenants
    assert sb.consultar("SELECT count(*) FROM fonte_orcamentos")[1][0][0] == 612


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM read_csv('{p}')",
        "SELECT * FROM '{p}'",
        "SELECT content FROM read_text('{p}')",
        "COPY (SELECT 1) TO '{d}/vazou.csv'",
        "SET enable_external_access = true",
        "SET allowed_directories = ['/']",
        "ATTACH '{d}/outro.duckdb' AS x",
        "INSTALL httpfs",
    ],
)
def test_sql_cru_nao_sai_do_staging(dois_tenants, sql):
    sb, segredo = dois_tenants
    with pytest.raises(duckdb.Error):
        # sb.con direto: simula um SQL que escapou da trava de somente leitura
        sb.con.execute(sql.format(p=segredo.as_posix(), d=segredo.parent.as_posix()))
    assert not (segredo.parent / "vazou.csv").exists()


def test_pipeline_grava_so_na_pasta_da_demanda(dois_tenants):
    sb, segredo = dois_tenants
    gold = sb.gravavel / "gold"
    gold.mkdir()
    sb.executar_pipeline(f"COPY (SELECT 1 AS x) TO '{(gold / 'ok.parquet').as_posix()}' (FORMAT parquet)")
    assert (gold / "ok.parquet").exists()
    # outra empresa; outra demanda da mesma empresa; demanda cujo nome começa igual (1 e 10)
    for fora in (segredo.parent, sb.gravavel.parent / "2", sb.gravavel.parent / "10"):
        fora.mkdir(exist_ok=True)
        with pytest.raises(duckdb.Error):
            sb.executar_pipeline(f"COPY (SELECT 1) TO '{(fora / 'x.parquet').as_posix()}' (FORMAT parquet)")


def test_banco_de_trabalho_fica_fora_do_staging(dois_tenants):
    sb, _ = dois_tenants
    # o staging pode ser um bucket montado; o arquivo do DuckDB fica no disco local do container
    assert not list(sb.staging.glob("*.duckdb*"))


def test_pasta_de_tenants_configuravel(monkeypatch, tmp_path):
    monkeypatch.setenv("LASTRO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LASTRO_TENANTS", str(tmp_path / "bucket"))
    assert carregar().pasta_tenant("acme") == (tmp_path / "bucket" / "acme").resolve()
    monkeypatch.delenv("LASTRO_TENANTS")
    assert carregar().pasta_tenant("acme") == (tmp_path / "home" / "tenants" / "acme").resolve()
