# Extreme DDS - firmware
Binarios de atualizacao OTA do Extreme DDS VFO.
Kit DDS para radio PX, chassi Uniden EPT3600-14B.
Extreme Truck Acessorios - Sinop, MT
## Como o aparelho atualiza
O DDS le o `versao.txt` na raiz deste repositorio. Ele tem DUAS linhas:
- linha 1: o numero da versao
- linha 2: o endereco do binario
O aparelho compara a linha 1 com a versao que ele roda. Se for diferente, baixa o arquivo da linha 2 e se atualiza sozinho.
## Publicar uma versao nova
1. Subir o `.bin` novo na pasta `firmware/`
2. Editar as duas linhas do `versao.txt`
So isso. Nao mudar o nome nem o formato do `versao.txt`.
## Aviso
Este repositorio guarda SOMENTE binarios. O codigo-fonte nao entra aqui: ele contem o segredo da licenca, e publica-lo permitiria gerar chave para qualquer aparelho.
## Versoes
- 3.0 - OTA por HTTPS, endereco do servidor editavel no painel, recuperacao automatica do barramento I2C
