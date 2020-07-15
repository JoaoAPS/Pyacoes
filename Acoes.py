from __future__ import annotations
import pandas as pd
import os
from pathlib import Path
import config

pd.options.mode.chained_assignment = None

date = pd.to_datetime
dataDir = Path(__file__).parent / "dados/"


class Acoes:
    """ Contém informações sobre ações

    Propriedades:
    `hist`: DataFrame com o histórico de todas movimentações já feitas.
    Possui as colunas:
        - tipo: tipo de movimentação (venda/compra)
        - codigo: código de negociação da ação
        - data: data de execução da ordem
        - qnt: quantidade de ações movimentadas na ordem
        - precoPorAcao: Preço de 1 ação na hora da execução da ordem, sem
        contar taxas
        - taxas: Total gasto com taxas (corretagem, emolumentos, etc)
        - total: Total líquido gasto(recebido) na compra(venda) da ação
        - precoMedio: Preço médio efetido de cada ação após considerar as taxas
    `carteira`: DataFrame com as ações atualmente em posse
        - codigo: código da ação. Serve como index.
        - qnt: quantidade de ações em posse
        - precoMedio: preço médio pago por cada ação
        - total: total gasto com as ações
        - precoParaLucro: preço médio mínimo que a ação deve ser vendida para
        obtenção de lucro, após contar as taxas, caso todas as ações sejam
        vendidas de uma vez
    A carteira sempre possui apenas uma linha por ação (código).
    Se uma ação que já está na carteira é comprada novamente por um preço
    diferente a linha da ação correspondente é atualizada. O preço médio é
    recalculado com uma média ponderada de 2 ítems: as ações na carteira e as
    novas. Uma venda simplesmente descresce a quantidade atual, sem mudar o
    preço médio. O sistema de cálculo do preço médio não é trivial, especial
    atenção deve ser tomada para adicionar as ordens na ordem correta. O preço
    médio é calculado assim pois é o formato padrão usado pela receita federal.
    `histLucro`: DataFrame com o lucro obtido com cada venda de ação executada
        - codigo: código da ação
        - data: data de execução da ordem
        - qnt: quantidade de ações movimentadas na ordem
        - precoMedioCarteira: preço médio gasto por ação nas compras,
        contando taxas
        - precoMedioVenda: preço médio obtido por ação na venda, contando taxas
        - lucroMedio: lucro líquido obtido por ação
        - lucro: lucro líquido obtido na venda
    `codigos`: DataFrame com legendas para os códigos de negociação.
    Deve ser criado manualmente.

    Métodos Disponíveis:
    # Análise
    - getAcoesEm(data)
    - getCompras()
    - getVendas()
    - getLegenda(codigo)
    # Manipulação
    - addOrdem(
        tipo:str,
        codigo:str
        data:datatime
        qnt:int
        precoPorAcao:float
        taxas:float
        shouldSort:bool=True
    )
    - addLegenda(codigo:str, empresa:str)
    - updatePrecoParaLucro()
    - save()
    # Info
    - resumo()
    - movimentacaoMensal()
    - estimarLucro(
        codigo:str
        precoPorAcao:float
        qnt:int=-1
        taxas:float=-1
        verbose:bool=True
    )
    """

    def __init__(self, readFromFiles: bool = False):
        """
        Parameters
        ----------
        readFromFiles : bool, optional
            Indica se o objeto deve usar os dados salvos nos arquivos
            (defualt=False)
        """

        # Taxa média de corretagem e emolumentos por ordem executada
        self.taxaMedia = config.taxaMedia

        # Lê dados principais
        if readFromFiles:
            self.hist = pd.read_csv(dataDir / 'hist.csv')
            self.hist['data'] = self.hist['data'].apply(pd.to_datetime)
            os.system('cp ' + str(dataDir / 'hist.csv') + ' '
                + str(dataDir / 'backups/hist.csv'))

            tmp = self.getAcoesEm(max(self.hist['data']))
            self.carteira = tmp.carteira
            self.histLucro = tmp.histLucro
            self.lucro = tmp.lucro
        else:
            self.hist = pd.DataFrame(columns=["tipo", "codigo", "data", "qnt",
                "precoPorAcao", "taxas", "total", "precoMedio"])
            self.carteira = pd.DataFrame(columns=["codigo", "qnt",
                "precoMedio", "total", "precoParaLucro"]).set_index('codigo')
            self.histLucro = pd.DataFrame(columns=['codigo', 'data', 'qnt',
                'precoMedioCarteira', 'precoMedioVenda', 'lucroMedio', 'lucro'])
            self.lucro = 0

        # Lê legenda dos códigos
        if os.path.isfile(dataDir / 'codigos.csv'):
            self.codigos = pd.read_csv(dataDir / 'codigos.csv')
            self.codigos.set_index('codigo', inplace=True)
            os.system('cp ' + str(dataDir / 'codigos.csv ')
                + str(dataDir / 'backups/codigos.csv'))
        else:
            self.codigos = pd.DataFrame(
                columns=['codigo', 'empresa']).set_index('codigo')

    # ************************** Methods *************************************

    # ----------------- Análise ------------------------
    def getCompras(self) -> pd.DataFrame:
        return self.hist[self.hist["tipo"] == "compra"]

    def getVendas(self) -> pd.DataFrame:
        return self.hist[self.hist["tipo"] == "venda"]

    def getLegenda(self, codigo: str) -> str:
        """ Retorna o texto que identifica o código de negociação """
        if codigo not in self.codigos.index:
            print("Código não encontrado na lista!")
            return
        return self.codigos.loc[codigo]["empresa"]

    def getAcoesEm(self, data) -> Acoes:
        """ Retorna um objeto Acoes com a situação das ações em na data passada

        Arguments
        ---------
        data : datetime
        """

        # Checagem de Erro
        if type(data) == str:
            data = pd.to_datetime(data)
        if type(data) != pd._libs.tslibs.timestamps.Timestamp:
            print("`data` deve ser um objeto datetime. Use pd.to_datetime()")
            return

        # Cria objeto vazio
        result = Acoes(readFromFiles=False)

        # Preenche objeto até a data estabelecida
        for idx, ordem in self.hist[self.hist['data'] <= data].iterrows():
            result.addOrdem(
                ordem['tipo'],
                ordem['codigo'],
                ordem['data'],
                ordem['qnt'],
                ordem['precoPorAcao'],
                ordem['taxas'],
                shouldSort=False
            )

        # Ordena
        result.hist.sort_values(['data', 'tipo'], inplace=True)
        result.histLucro.sort_values('data', inplace=True)

        return result

    # ----------- Updates --------------------
    def addOrdem(
        self,
        tipo: str,
        codigo: str,
        data,
        qnt: int,
        precoPorAcao: float,
        taxas: float,
        shouldSort: bool = True
    ):
        """ Adiciona uma nova ordem (compra ou venda) ao objeto

        Arguments
        ---------
        tipo : str
            Tipo da ordem. 'compra' ou 'venda'
        codigo : str
            Código de negociação da ação
         data : datetime
             Data da ordem
        qnt : int
            Quantidade de ações envolvidas
        precoPorAcao : float
            Preço de cada ação
        taxas : float
            Taxas de corretagem, etc. gastas na ordem
        shouldSort : bool, optional
            Indice se as propriedades do objeto devem ser ordenadas ao final
            (default=True)
        """

        # ----- Checagem de Erro -----
        assert tipo in ['compra', 'venda']
        assert qnt > 0
        assert precoPorAcao > 0
        assert taxas > 0

        if isinstance(data, str):
            data = pd.to_datetime(data)
        if not isinstance(data, pd._libs.tslibs.timestamps.Timestamp):
            print("`data` deve ser um objeto datetime. Use pd.to_datetime()")
            return

        codigo = codigo.upper()

        # Checa se é uma venda impossível
        if tipo == 'venda':
            assert codigo in self.carteira.index

            if qnt > self.carteira.at[codigo, 'qnt']:
                print("Erro! Há uma ordem de venda de %d ações %s, mas na"
                    "carteira há apenas %d dessas ações!"
                    % (qnt, codigo, self.carteira.at[codigo, 'qnt'])
                )
                return
        # ----------------------------

        total = (
            qnt * precoPorAcao + taxas
            if tipo == 'compra'
            else qnt * precoPorAcao - taxas
        )
        precoMedio = total / qnt
        ordem = pd.Series({
            'tipo': tipo,
            'codigo': codigo,
            'data': data,
            'qnt': qnt,
            'precoPorAcao': precoPorAcao,
            'taxas': taxas,
            'total': total,
            'precoMedio': precoMedio
        })

        # Atualiza histórico de compras
        self.hist = self.hist.append(ordem, ignore_index=True)

        # ----- Atualiza carteira e lucros -----
        if ordem['tipo'] == 'compra':
            # Se é a primeira compra dessa ação, só adiciona à carteira
            if codigo not in self.carteira.index:
                self.carteira.loc[codigo] = \
                    ordem[['qnt', 'precoMedio', 'total']].copy()

            # Se já existe essa ação na carteira
            else:
                existingRow = self.carteira.loc[codigo]

                # Atualiza preço médio com uma média ponderada
                self.carteira.at[codigo, 'precoMedio'] = (
                    (existingRow['qnt'] * existingRow['precoMedio']
                    + ordem['qnt'] * ordem['precoMedio'])
                    / (existingRow['qnt'] + ordem['qnt'])
                )

                # Atualiza quantidades
                self.carteira.at[codigo, 'qnt'] = existingRow['qnt'] \
                    + ordem['qnt']
                self.carteira.at[codigo, 'total'] += ordem['total']

            # Recalcula preço para lucro
            self.carteira.at[codigo, 'precoParaLucro'] \
                = (self.carteira.at[codigo, 'total'] + self.taxaMedia) \
                / self.carteira.at[codigo, 'qnt']

        if ordem['tipo'] == 'venda':
            # Calcula lucro da venda
            lucroMedio = ordem['precoMedio'] \
                - self.carteira.at[codigo, 'precoMedio']
            lucroAtual = {
                'codigo': codigo,
                'data': ordem['data'],
                'qnt': ordem['qnt'],
                'precoMedioCarteira': self.carteira.at[codigo, 'precoMedio'],
                'precoMedioVenda': ordem['precoMedio'],
                'lucroMedio': lucroMedio,
                'lucro': ordem['qnt'] * lucroMedio
            }

            self.histLucro = self.histLucro.append(
                lucroAtual,
                ignore_index=True
            )
            self.lucro += ordem['qnt'] \
                * (ordem['precoMedio']
                    - self.carteira.at[codigo, 'precoMedio'])

            self.carteira.at[codigo, 'qnt'] -= ordem['qnt']

            # Se todas as ações disponíveis foram vendidas, remove a linha
            if self.carteira.loc[codigo]['qnt'] == 0:
                self.carteira.drop(codigo, inplace=True)
            # Se ainda está na carteira, atualiza valores
            else:
                self.carteira.at[codigo, 'total'] = (
                    self.carteira.at[codigo, 'qnt']
                    * self.carteira.at[codigo, 'precoMedio']
                )
                self.carteira.at[codigo, 'precoParaLucro'] = (
                    (self.carteira.at[codigo, 'total'] + self.taxaMedia)
                    / self.carteira.at[codigo, 'qnt']
                )
        # --------------------------------------

        # Reordena os DataFrames
        if shouldSort:
            self.hist.sort_values(['data', 'tipo'], inplace=True)
            self.histLucro.sort_values('data', inplace=True)

    def addLegenda(self, codigo: str, legenda: str):
        """ Adiciona a legenda de um código de negociação em `codigos`.

        Arguments
        ---------
        codigo : str
            Código de negociação
        legenda : str
            Texto que identifica o código
        """

        self.codigos[codigo] = legenda

    def updatePrecoParaLucro(self):
        """ Recalcula o preço de venda necessário para lucro """
        self.carteira['precoParaLucro'] = \
            (self.carteira['total'] + self.taxaMedia) / self.carteira['qnt']

    # ----------- Info --------------------
    def movimentacaoMensal(self):
        """ Retorna o total que foi gasto, recebido, e lucrado em cada mês. """

        ordems = pd.DataFrame()
        ordems['mes'] = self.hist['data'].apply(lambda x: x.month)
        ordems['ano'] = self.hist['data'].apply(lambda x: x.year)
        ordems['compras'] = self.hist.apply(
            lambda col: col['total']
            if col['tipo'] == 'compra'
            else 0,
            axis=1
        )
        ordems['vendas'] = self.hist.apply(
            lambda col: col['total']
            if col['tipo'] == 'venda'
            else 0,
            axis=1
        )

        lucros = pd.DataFrame()
        lucros['mes'] = self.histLucro['data'].apply(lambda x: x.month)
        lucros['ano'] = self.histLucro['data'].apply(lambda x: x.year)
        lucros['lucros'] = self.histLucro['lucro']

        ords = ordems.groupby(['ano', 'mes']).sum()
        lucs = lucros.groupby(['ano', 'mes']).sum()

        return ords.join(lucs)

    def resumo(self):
        """ Imprime um resumo da situação atual """
        print("----------------------")
        print("--- Situação Atual ---")
        print("----------------------")
        print("Primeira movimentação: %s" % (self.hist['data'].min().date()))
        print("Última movimentação:   %s" % (self.hist['data'].max().date()))

        print("\n\nCarteira Atual:")
        print(self.carteira)

        print("\n\nDados:")
        print("Total comprado:      R$%10.2f"
            % (self.getCompras()['total'].sum()))
        print("Total vendido:       R$%10.2f"
            % (self.getVendas()['total'].sum()))
        print("")
        print("Custódia total:      R$%10.2f"
            % (self.carteira['total'].sum()))
        print("Lucro líquido total: R$%10.2f"
            % (self.histLucro['lucro'].sum()))
        print("")

    def estimarLucro(
        self,
        codigo: str,
        precoPorAcao: float,
        qnt: int = -1,
        taxas: float = -1,
        verbose: bool = True
    ):
        """ Estima o lucro que será recebido pela venda de ações a um
            determinado preço

            Arguments
            ---------
            codigo : str
                Código de negociação, deve estar presente na carteira
            precoPorAcao : float
                Preço a ser usado na estimativa
            qnt : int, optional
                Quantidade de ações vendidas. Se menor 0 considera-se a venda de todas 
                ações disponíveis na carteira (default -1)
            taxas : float, optional
                Valor que se espera pagar em taxas. Se menor que 0 usa self.taxaMedia (default -1)
            verbose : bool, optional (default True)
        """

        # ----- Checagem de Erro -----
        assert precoPorAcao > 0

        # Checa se é uma venda impossível
        codigo = codigo.upper()
        assert codigo in self.carteira.index, "Código " \
            + codigo + " não foi encontrado na carteira"

        if qnt > self.carteira.at[codigo, 'qnt']:
            print("Erro! Foi passada uma venda de %d ações %s, "
                "mas na carteira há apenas %d dessas ações!"
                %(qnt, codigo, self.carteira.at[codigo, 'qnt']))
            return
        # ----------------------------

        cartRow = self.carteira.loc[codigo]

        if qnt < 0:
            qnt = cartRow['qnt']

        lucro = (qnt * precoPorAcao - self.taxaMedia) \
            - (qnt * cartRow['precoMedio'])

        if verbose:
            print("Lucro na venda de %d ações %s à %f cada"
                % (qnt, codigo, precoPorAcao))
            print("Lucro médio: R$%f" % (lucro / qnt))
            print("Lucro total: R$%-9.2f" % lucro)

        return lucro

    def save(self):
        """ Salva o estado atual da classe em arquivo """

        self.hist.to_csv(dataDir / 'hist.csv', index=False)
        self.codigos.to_csv(dataDir / 'codigos.csv', index=True)
