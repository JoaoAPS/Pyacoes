from pathlib import Path
import os
import importlib

#Importa pacote
cwd = os.getcwd() + '/'
ModulePath = str(Path(__file__).parent / 'Acoes').replace(cwd,'')
ModuleAcoes = importlib.import_module( ModulePath.replace('/','.') )
Acoes = ModuleAcoes.Acoes

#Carrega variáveis
dataFilePath = str(Path(__file__) / 'dados/hist.csv').replace('launch.py/', '')
acoes = ModuleAcoes.Acoes(readFromFiles = os.path.isfile(dataFilePath))
date  = ModuleAcoes.date

#Imprime boas vindas
print("")
print("-----------------------------------------")
print("API em python para administração de ações")
print("-----------------------------------------")
print("")
print("Todas informações estão na variável `acoes`")
print("")
print("acoes.hist:      Histórico de movimentação")
print("acoes.carteira:  Ações em custódia")
print("acoes.histLucro: Histórico de lucros em vendas")
print("acoes.addOrdem:  Cria uma nova ordem de compra ou venda")
print("")
print("Para informação completa digite: `help(Acoes)`")
print("")

