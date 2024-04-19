# Apresentação

Este projeto é destinado à resolução do desafio proposto para o Tech Challenge da Fase 1 do curso de Pós graduação em Inteligencia Artificial da FIAP de 2024.

# Desafio

Desenvolver um modelo preditivo de regressão que preveja o valor dos custos médicos individuais cobrados pelo plano de saúde, com base nos dados de idade, gênero, IMC, quantidade de filhos, se a pessoa é fumante e a região do brasil onde mora.

# Modelo desenvolvido

O projeto foi desenvolvido e testado utulizando Google Colab (Runtime T4 GPU), porém é possivel executá-lo em qualquer ambiente que suporte Python 3+.

Bibliotecas necessárias:

- numpy
- pandas
- seaborn
- matplotlib
- scikit-learn

Comando para instalação:

`!pip install numpy pandas scikit-learn matplotlib seaborn`

O Script é composto por 6 etapas:

### 0. Criação de dataset
*   Criação de conjunto de dados (aleatórios) + calculo de encargos com base nos dados inseridos previamente. (É possivel tambem subir seu proprio arquivo, deste que este respeite a configuração dos dados de entrada expostos no código. A inclusão do path do arquivo diretamente no código pode ser necessária)
### 1. Exploração de dados
*   Carregamento da base de dados e exploração suas características.           
*   Analise estatística descritiva e visualização de distribuições relevantes.
### 2. Pré-processamento dos dados
* Limpeza dos dados.
* Conversão de variáveis categóricas em formatos adequados para modelagem, utilizando o modelo One Hot Encoder.
### 3. Modelagem
* Criação de modelos preditivos de Regressão Linear e Árvore de Decisão
* Divisão do conjunto de dados em conjuntos de treinamento e teste
### 4. Treinamento e avaliação do modelo
### 5. Validação estatistica (Resultados)
Métricas estatísticas para validação à eficácia dos modelo:
* Erro Quadrático Médio (MSE)
* Coeficiente de Determinação (R²)
* Erro Absoluto Médio (MAE)
* Grafico de comparação de eficiência dos dois modelos
