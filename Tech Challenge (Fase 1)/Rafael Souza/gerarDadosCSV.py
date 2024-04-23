import codecs
import csv
import random

# Definindo as faixas de valores para cada coluna
faixas_idade = range(18, 81)  # Idade entre 18 e 80 anos
generos = ["masculino"] * 5000 + ["feminino"] * 5000  # Gêneros com distribuição igual
random.shuffle(generos)  # Mistura a lista para garantir a aleatoriedade
faixas_imc = [random.uniform(18.0, 40.0) for _ in range(10000)]  # IMC entre 18 e 40
numero_filhos = range(0, 5)  # Número de filhos entre 0 e 4
fumantes = ["sim", "não"]  # Fumante ou não
regioes = ["norte", "nordeste", "sudeste", "sul", "centro-oeste"]  # Regiões do Brasil
faixas_encargos = [random.uniform(15000.0, 50000.0) for _ in range(10000)]  # Encargos entre R$ 15.000 e R$ 50.000

# Abrindo o arquivo CSV para escrita com codificação UTF-8
with codecs.open('dados_ficticios.csv', 'w', 'utf-8') as arquivo_csv:

    # Criando o objeto escritor de CSV
    escritor_csv = csv.writer(arquivo_csv)

    # Escrevendo a linha de cabeçalho
    escritor_csv.writerow(["idade", "gênero", "imc", "filhos", "fumante", "região", "encargos"])

    # Gerando e escrevendo 10.000 linhas de dados fictícios
    for i in range(10000):
        dados_linha = [
            str(random.choice(faixas_idade)),
            generos[i],  # Escolhe o gênero correspondente ao índice atual
            "{:.15f}".format(random.choice(faixas_imc)),  # Formatando o IMC com 15 casas decimais
            str(random.choice(numero_filhos)),
            random.choice(fumantes),
            random.choice(regioes),
            "{:.15f}".format(faixas_encargos[i])  # Formatando os encargos com 15 casas decimais
        ]
        escritor_csv.writerow(dados_linha)