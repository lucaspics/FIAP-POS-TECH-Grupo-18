import codecs
import csv
import random
import numpy as np

# Definindo as faixas de valores para cada coluna
faixas_idade = range(18, 90)  # Idade entre 18 e 90 anos
generos = ["masculino", "feminino"]  # Gêneros masculino e feminino
faixas_imc = [x / 10 for x in range(120, 501)]  # IMC entre 12.0 e 50.0
numero_filhos = range(0, 5)  # Número de filhos entre 0 e 4
fumantes = ["sim", "não"]  # Fumante ou não fumante
regioes = ["norte", "nordeste", "sudeste", "sul", "centro-oeste"]  # Regiões do Brasil


# Função para calcular os encargos com base nas características individuais
def calcular_encargos(idade, genero, imc, filhos, fumante, regiao):
    encargos_base = (
            idade * 80.33  # Baseado na idade
            + imc * 255.52  # Baseado no IMC
    )
    # Multiplicadores adicionais
    if genero == "masculino":
        encargos_base *= 1.1  # Homens possuem maior taxa de mortalidade
    if genero == "feminino" and filhos > 0:
        encargos_base *= 1.05  # Mulheres que já tiveram filhos possuem uma tendência maior a aparição de sintomas de saúde
    if fumante == "sim":
        encargos_base *= 1.5  # Indivíduos fumantes apresentam um enorme acréscimo na taxa de aparição de sintomas de saúde
    if regiao in ["sul", "sudeste"]:
        encargos_base *= 1.2  # Regiões sul e sudeste possuem hospitais mais caros

    return encargos_base


# Abrindo o arquivo CSV para escrita com codificação UTF-8
with codecs.open('dados_ficticios.csv', 'w', 'utf-8') as arquivo_csv:
    # Criando o objeto escritor de CSV
    escritor_csv = csv.writer(arquivo_csv)

    # Escrevendo a linha de cabeçalho
    escritor_csv.writerow(["idade", "gênero", "imc", "filhos", "fumante", "região", "encargos"])

    # Gerando e escrevendo 10.000 linhas de dados fictícios
    for _ in range(10000):
        # Gerando dados aleatórios para cada linha
        idade = random.choice(faixas_idade)
        genero = random.choice(generos)
        imc = random.choice(faixas_imc)
        filhos = random.choice(numero_filhos)
        fumante = random.choice(fumantes)
        regiao = random.choice(regioes)
        # Calculando os encargos com base nos dados gerados
        encargos = calcular_encargos(idade, genero, imc, filhos, fumante, regiao)
        # Escrevendo os dados no arquivo CSV
        dados_linha = [str(idade), genero, "{:.15f}".format(imc), str(filhos), fumante, regiao,
                       "{:.15f}".format(encargos)]
        escritor_csv.writerow(dados_linha)
