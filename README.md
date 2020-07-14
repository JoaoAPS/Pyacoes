Pyacoes
=======

Uma biblioteca rudimentar em python para guardar o histórico de compras e vendas de ações.
Todas informações são guardadas como DataFrames do pacote [pandas](https://pandas.pydata.org/).
A biblioteca é particularmente útil para declaração de imposto de renda, pois calcula automaticamente o 
lucro de cada venda e o novo preço médio com cada compra.

*Dependências: numpy, pandas*

## Uso
Para abrir execute no terminal
``` bash
python -i /path/to/pyacoes/launch.py
```
O comando pode ser posto num *alias* para facilitar.

Isso abrirá um shell python com um objeto `acoes` da classe `Acoes` já inicializado.

As informações relevantes estão nas seguintes variáveis

- `acoes.hist`: Contém o histórico de todas ordens realizadas
- `acoes.carteira`: Contém as ações atualmente em posse
- `acoes.histLucro`: Contém o histórico dos lucros obtidos com cada venda
- `acoes.lucro`: O lucro total obtido até agora

Há alguns métodos para manipular os dados

#### - acoes.save()
Salva o estado atual da classe em arquivo.
Chame esse método sempre que fizer alterações que devem ser permanentes.

#### - acoes.addOrdem(tipo, codigo, data, qnt, precoPorAcao, taxas, shouldSort=True)
Adiciona uma nova ordem (compra ou venda) ao histórico.

- `tipo`:str - Tipo da ordem. 'compra' ou 'venda'
- `codigo`:str - Código de negociação da ação
- `data`:datetime - Data da ordem
- `qnt`:int - Quantidade de ações envolvidas
- `precoPorAcao`:float - Preço de cada ação
- `taxas`:float - Taxas de corretagem, etc. gastas na ordem
- `shouldSort`:bool, optional - Indice se as propriedades do objeto devem ser ordenadas ao final (default=True)

#### - acoes.getAcoesEm(data)
Retorna um objeto Acoes com a situação das ações em uma determinada data.

- `data`:datetime - Também pode ser uma string no formato datetime (ex. '2000-12-31')

#### - acoes.estimarLucro(codigo, precoPorAcao, qnt=-1, taxas=-1, verbose=True)
Estima o lucro que será recebido pela venda de ações a um determinado preço.

- `codigo`:str - Código de negociação, deve estar presente na carteira
- `precoPorAcao`:float - Preço de venda a ser usado na estimativa
- `qnt`:int, optional - Quantidade de ações vendidas. Se menor 0 considera-se a venda de todas ações disponíveis na carteira (default -1)
- `taxas`:float, optional - Valor que se espera pagar em taxas. Se menor que 0 usa self.taxaMedia (default -1)
- `verbose`:bool, optional (default True)

#### - acoes.getCompras()
Retorna um DataFrame com o historico de compras.

#### - acoes.getVendas()
Retorna um DataFrame com o historico de vendas.

#### - acoes.getLegenda(codigo)
Retorna o texto que identifica o código de negociação.

#### - acoes.updatePrecoParaLucro()
Recalcula o preço de venda necessário para lucro.
Chame essa função quando a taxa média for alterada.

#### - acoes.resumo()
Imprime um resumo da situação atual.

#### - acoes.movimentacaoMensal()
Retorna o total que foi gasto, recebido, e lucrado em cada mês.

#### - addLegenda(codigo, legenda)
Adiciona a legenda de um código de negociação em `codigos`.

- `codigo`:str - Código de negociação
- `legenda`:str - Texto que identifica o código
