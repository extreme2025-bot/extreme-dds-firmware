# Extreme DDS - firmware

Binarios de atualizacao OTA do Extreme DDS VFO.
Kit DDS para radio PX, chassi Uniden EPT3600-14B.
Extreme Truck Acessorios - Sinop, MT

## Como o aparelho atualiza

O DDS le o `versao.txt` na raiz deste repositorio. Desde a versao 4.7 ele tem
**TRES linhas**:

| Linha | O que e |
|---|---|
| 1 | o numero da versao (ex. `4.7`) |
| 2 | o endereco do binario |
| 3 | a assinatura ECDSA P-256 do manifesto, em base64 |

O aparelho compara a linha 1 com a versao que ele roda. So atualiza se a
publicada for **maior** (numericamente - desde a 3.3 nao existe downgrade).
Antes de gravar, confere a assinatura da linha 3. Se ela nao bater, ele
mostra `Assinatura invalida` e nao grava nada.

> **Atencao:** firmware **anterior a 4.7 quebra** com um manifesto de 3 linhas.
> Aparelho que ainda esteja abaixo da 4.7 precisa ser levado a 4.7 com um
> manifesto de 2 linhas antes de voltar ao manifesto assinado.

## Publicar uma versao nova

1. Subir o `.bin` novo em `firmware/`, no padrao `extreme_dds_X.Y.bin`
2. Editar as tres linhas do `versao.txt`
3. **Conferir antes de mandar para os aparelhos:**

   ```
   python3 ferramentas/validar.py
   ```

   Ele checa que a versao subiu, que o arquivo da linha 2 existe e tem o nome
   certo, que o binario e mesmo de ESP32, quanto da particao ele ocupa, e que a
   assinatura confere. Enquanto ele nao disser `APROVADO`, nao publique.

O mesmo teste roda sozinho no GitHub a cada push
(`.github/workflows/validar-publicacao.yml`). Push vermelho = manifesto errado.

Nao mudar o nome nem o formato do `versao.txt`.

### Conferir a assinatura automaticamente

Coloque a chave **publica** ECDSA na raiz como `chave-publica.pem` e a
checagem de assinatura liga sozinha. A chave publica pode ficar no repositorio:
ela so serve para conferir. **A chave privada nunca entra aqui.**

## Por que nao existem versoes anteriores a 4.7 aqui

Da 3.0 a 4.6 o segredo de licenca ficava em texto puro dentro do `.bin` - um
`strings` no arquivo o entregava.  O segredo foi trocado na 4.7 e aqueles
binarios foram retirados.  Nao republique nenhum deles.

## Aviso

Este repositorio guarda SOMENTE binarios. O codigo-fonte nao entra aqui: ele
contem o segredo da licenca, e publica-lo permitiria gerar chave para qualquer
aparelho.

## Versoes

| Versao | O que mudou |
|---|---|
| 4.8 | Validacao da versao recebida no OTA (manifesto malicioso travava o aparelho na atualizacao) |
| 5.0 | Bloqueio de senha passa a sobreviver ao desliga-liga; segunda camada na conferencia do manifesto; limpeza de codigo orfao |
| 4.9 | Menu em fonte grande, rotulos curtos, item Passo retirado, saudacao com o nome do cliente |
| 4.8 | Validacao da versao recebida no OTA (manifesto malicioso travava o aparelho na atualizacao) |
| 4.7 | Assinatura ECDSA no OTA, senha do ponto de acesso por aparelho, licenca por nivel, medicao de ROE/potencia/tensao, protecao de ROE, TOT corrigido, leitura do modo pelos pinos |
| 4.4-4.6 | Senha mestra por serial, autoteste, horimetro, historico encadeado, selo do nivel na tela (versoes internas, nao publicadas) |
| 4.3 | Sentido do encoder |
| 4.2 | Canal 001, menus curtos, passo por digito, S-meter estilo radio, cadeado |
| 4.1 | Tela nova, restaurar padrao, trava de bolso, ajustes de menu |
| 4.0 | Brilho minimo 20 |
| 3.9 | Modo de emissao so com fonte = menu |
| 3.8 | Display sem piscar, vigia I2C seletivo |
| 3.6-3.7 | Telas de resposta grandes |
| 3.5 | Esquecer rede |
| 3.4 | "Atualizar" em primeiro, reconexao automatica |
| 3.3 | Comparacao numerica de versao (fim do downgrade) |
| 3.2 | Lista de redes, motivo da falha |
| 3.0 | OTA por HTTPS, endereco do servidor editavel no painel, recuperacao automatica do barramento I2C |

## Servidor de teste

`versao-teste.txt` existe para provar, no aparelho real, que firmware
adulterado e recusado.  Ele aponta para
`firmware/extreme_dds_4.9_TESTE_ADULTERADO.bin`, que e a 4.8 com **um bit
trocado** de proposito, e traz a assinatura da 4.8 - que por isso nao
confere.

Ele anuncia a versao 9.9 de proposito: precisa ser sempre maior que a versao
real, senao o aparelho responde "Ja esta atualizado" e o teste deixa de
exercitar a conferencia de assinatura.

Como usar: no painel do DDS, troque o endereco do servidor para o
`versao-teste.txt`, mande Atualizar, e o display tem que mostrar
`Assinatura invalida` sem gravar nada.  Depois devolva o endereco para o
`versao.txt`.

**Nunca aponte o `versao.txt` de producao para esse binario.**  O validador
so confere o `versao.txt`, entao este arquivo de teste nao interfere no CI.
