#!/usr/bin/env python3
"""
Confere o versao.txt antes que ele chegue nos aparelhos.

Roda sozinho a cada push (.github/workflows/validar-publicacao.yml) e tambem
na mao:  python3 ferramentas/validar.py

O que ele NAO faz: assinar. A chave privada nunca entra aqui.
So a chave publica e usada, e so para conferir.
"""

import base64
import hashlib
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTO = os.path.join(RAIZ, "versao.txt")
PASTA_BIN = os.path.join(RAIZ, "firmware")
CHAVE_PUBLICA = os.path.join(RAIZ, "chave-publica.pem")

# Tamanho da particao de app do ESP32.
# 1310720 = 1,25 MB (modulo de 4 MB, particionamento atual)
# 1966080 = 1,875 MB (modulo N16, previsto para a producao)
PARTICAO = 1310720

erros = []
avisos = []


def erro(msg):
    erros.append(msg)
    print("  ERRO   " + msg)


def aviso(msg):
    avisos.append(msg)
    print("  AVISO  " + msg)


def ok(msg):
    print("  ok     " + msg)


def como_numero(v):
    """4.7 -> (4, 7). Mesma comparacao que o firmware faz desde a 3.3."""
    partes = v.split(".")
    if not all(p.isdigit() for p in partes) or not 1 <= len(partes) <= 3:
        return None
    return tuple(int(p) for p in partes)


def manifesto_anterior():
    """Le o versao.txt do commit anterior, se houver."""
    try:
        txt = subprocess.run(
            ["git", "show", "HEAD^:versao.txt"],
            cwd=RAIZ, capture_output=True, text=True, check=True,
        ).stdout
        return [l.strip() for l in txt.strip().splitlines()]
    except Exception:
        return None


def confere_assinatura(assinatura, versao, sha_hex, caminho_bin):
    """
    Confere a assinatura ECDSA com a chave publica.

    O formato exato do que foi assinado esta no gerador de licencas, nao aqui.
    Entao testamos os formatos plausiveis e dizemos qual fechou -- o que
    passar vira a documentacao viva do formato.
    """
    if not os.path.exists(CHAVE_PUBLICA):
        aviso("chave-publica.pem nao esta no repositorio: assinatura nao conferida.")
        aviso("  Coloque a chave PUBLICA (nunca a privada) em chave-publica.pem")
        aviso("  e esta checagem liga sozinha.")
        return

    try:
        sig = base64.b64decode(assinatura, validate=True)
    except Exception:
        erro("linha 3 nao e base64 valido.")
        return
    if not sig or sig[0] != 0x30:
        erro("linha 3 nao e uma assinatura DER (deveria comecar com 0x30).")
        return

    candidatos = {
        "versao + '|' + sha256hex": f"{versao}|{sha_hex}".encode(),
        "versao + '\\n' + sha256hex": f"{versao}\n{sha_hex}".encode(),
        "versao + sha256hex": f"{versao}{sha_hex}".encode(),
        "sha256hex": sha_hex.encode(),
        "versao + sha256 (32 bytes crus)": versao.encode() + bytes.fromhex(sha_hex),
        "binario inteiro": open(caminho_bin, "rb").read(),
    }

    with tempfile.TemporaryDirectory() as tmp:
        arq_sig = os.path.join(tmp, "sig.der")
        with open(arq_sig, "wb") as f:
            f.write(sig)
        for nome, dados in candidatos.items():
            arq_dados = os.path.join(tmp, "dados.bin")
            with open(arq_dados, "wb") as f:
                f.write(dados)
            r = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", CHAVE_PUBLICA,
                 "-signature", arq_sig, arq_dados],
                capture_output=True,
            )
            if r.returncode == 0:
                ok(f"assinatura CONFERE. Formato assinado: {nome}")
                return
    erro("assinatura NAO confere com a chave publica em nenhum formato testado.")
    erro("  Ou a assinatura esta errada, ou a chave e outra, ou o .bin mudou.")
    erro("  NAO publique: todo aparelho 4.7+ vai recusar esta atualizacao.")


def main():
    print("Conferindo a publicacao do Extreme DDS\n")

    if not os.path.exists(MANIFESTO):
        erro("versao.txt nao existe.")
        return 1

    bruto = open(MANIFESTO, "rb").read()
    if b"\r\n" in bruto:
        erro("versao.txt tem quebra de linha do Windows (CRLF). O aparelho espera LF.")
    linhas = [l.strip() for l in bruto.decode("utf-8").strip().splitlines()]

    if len(linhas) < 2:
        erro(f"versao.txt tem {len(linhas)} linha(s); precisa de 3 "
             "(versao, endereco, assinatura).")
        return 1
    if len(linhas) == 2:
        erro("versao.txt tem 2 linhas: FALTA A ASSINATURA na linha 3.")
        erro("  Firmware 4.7+ recusa manifesto sem assinatura.")
        return 1
    if len(linhas) > 3:
        erro(f"versao.txt tem {len(linhas)} linhas; o aparelho le exatamente 3.")

    versao, url, assinatura = linhas[0], linhas[1], linhas[2]

    # --- 1. versao ---
    print("1) Versao")
    num = como_numero(versao)
    if num is None:
        erro(f"'{versao}' nao e um numero de versao (esperado 4.7 ou 4.7.1).")
        return 1
    ok(f"linha 1 = {versao}")

    ant = manifesto_anterior()
    if ant:
        num_ant = como_numero(ant[0])
        if num_ant is None:
            pass
        elif num < num_ant:
            erro(f"DOWNGRADE: {versao} e menor que a publicada antes ({ant[0]}).")
            erro("  Os aparelhos comparam numericamente e vao ignorar esta.")
        elif num > num_ant:
            ok(f"maior que a anterior ({ant[0]})")
        elif linhas != ant:
            # Mesma versao, conteudo diferente: quem ja esta nela nao rebaixa.
            aviso(f"a versao continua {versao} mas o manifesto mudou.")
            aviso("  Aparelhos ja em " + versao + " NAO vao baixar o binario novo.")
            aviso("  Se o binario mudou, suba o numero da versao.")
        else:
            ok(f"manifesto identico ao anterior (nada novo publicado)")

    # --- 2. endereco ---
    print("\n2) Endereco do binario")
    if not url.startswith("https://"):
        erro("a linha 2 precisa ser https://")
    nome_arq = url.rsplit("/", 1)[-1]
    if not re.fullmatch(r"extreme_dds_[0-9.]+\.bin", nome_arq):
        aviso(f"nome fora do padrao extreme_dds_X.Y.bin: {nome_arq}")
    esperado = f"extreme_dds_{versao}.bin"
    if nome_arq != esperado:
        erro(f"a linha 2 aponta para {nome_arq}, mas a linha 1 diz {versao} "
             f"(esperado {esperado}).")
    caminho = os.path.join(PASTA_BIN, nome_arq)
    if not os.path.exists(caminho):
        erro(f"firmware/{nome_arq} NAO existe no repositorio.")
        erro("  O aparelho vai baixar 404 e dar 'Firmware inacessivel'.")
        return 1
    ok(f"firmware/{nome_arq} existe")

    # --- 3. o binario ---
    print("\n3) O binario")
    dados = open(caminho, "rb").read()
    if dados[0] != 0xE9:
        erro("nao parece firmware de ESP32 (primeiro byte deveria ser 0xE9).")
    else:
        ok("cabecalho de ESP32 (0xE9)")
    sha = hashlib.sha256(dados).hexdigest()
    ok(f"SHA-256 {sha}")
    ok(f"tamanho {len(dados):,} bytes")
    pct = len(dados) / PARTICAO * 100
    if len(dados) > PARTICAO:
        erro(f"NAO CABE na particao de {PARTICAO:,} bytes ({pct:.1f}%).")
    elif pct > 90:
        aviso(f"{pct:.1f}% da particao ({PARTICAO - len(dados):,} bytes livres). "
              "Hora do modulo N16.")
    else:
        ok(f"{pct:.1f}% da particao, {PARTICAO - len(dados):,} bytes livres")

    # --- 4. assinatura ---
    print("\n4) Assinatura")
    confere_assinatura(assinatura, versao, sha, caminho)

    # --- resultado ---
    print("\n" + "-" * 60)
    if erros:
        print(f"REPROVADO: {len(erros)} erro(s), {len(avisos)} aviso(s).")
        print("NAO publique assim.")
        return 1
    print(f"APROVADO. {len(avisos)} aviso(s).")
    print(f"Versao {versao} -> firmware/{os.path.basename(caminho)}")
    print(f"SHA-256 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
