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

O Script é composto por 6 etapas, sendo a primeira delas desnecessária caso o usuário opte por efetuar o upload de uma base propria:

### Criação de dataset
* Criação de conjunto de dados ficticios:
    - **Total de Registros**: 10.000
    - **Gênero**: "masculino" ou "feminino" (Distribuição aleatória)
    - **Idade**: 18 a 90 anos (Distribuição aleatória)
    - **IMC**: Indice de massa corpórea do individuo, valores gerados simulados entre 12 e 50 (Distribuição aleatória)
    - **Filhos**: Entre 0 e 5 filhos (Distribuição aleatória)
    - **Fumante**: O hábito de fumar, rótulos possiveis: "Sim" ou "Não" (Distribuição aleatória)
    - **Região**: "norte", "nordeste", "centro-oeste", "sul" ou "sudeste" (Distribuição aleatória).
    - **Encargos**: Os encargos foram calculados com base em cada um dos dados fictícios gerados para as colunas anteriores, seguindo uma ordem lógica, fiel a um cenário real, dado que o valor a ser cobrado por um Plano de Saúde não é aleatório, e sim baseado nas características do contratante, sendo os multiplicadores:
        - **Cálculo Base**:
            - **Idade**: Idade * R$ 80,33
            - **IMC**: IMC * R$ 255,52
        - **Multiplicadores (aplicados à soma do calculo base)**:
            - **Gênero**:
                - **Homem**: +10% (Devido a maior taxa de mortalidade)
                - **Mulher + Filhos > 0**: +5% (Recém-gestantes/gestante possuem uma tendencia maior a necessidade de cuidados médicos)
            - **Fumante**:
                - **Sim**: +40% (Individuos fumantes apresentam um enorme acrescimo na taxa de aparição de sintomas de saúde)
            - **Região**:
                - **Sul, Sudeste**: +20% (Regiões sul e sudeste possuem maior custo com serviços médicos em hospitais)

* Em caso de upload de arquivo pessoal, o mesmo deve respeitar o layout dos dados de entrada expostos no código. A inclusão do path do arquivo diretamente no código tambem pode ser necessária.
### 1. Exploração de dados
*   Carregamento da base de dados e exploração suas características.           
*   Analise estatística descritiva e visualização de distribuições relevantes.
### 2. Pré-processamento dos dados
* Limpeza dos dados.
* Conversão de variáveis categóricas em formatos adequados para modelagem, utilizando o modelo One Hot Encoder.
### 3. Modelagem
* Criação de modelos preditivos de Regressão Linear, Árvore de Decisão e Gradient Boosting Machine (Regressão)
* Divisão do conjunto de dados em conjuntos de treinamento e teste
### 4. Treinamento e avaliação do modelo
### 5. Validação estatistica (Resultados)
Métricas estatísticas para validação à eficácia dos modelo:
* Erro Quadrático Médio (MSE)
* Coeficiente de Determinação (R²)
* Erro Absoluto Médio (MAE)
* Grafico de comparação de eficiência dos três modelos

# Observações Importantes
* Este conjunto de dados é fictício e destinado apenas para fins de simulação e demonstração. Não deve ser utilizado para análises estatísticas ou de pesquisa sem a devida avaliação por especialistas.
* A simulação de dados pessoais, como idade, gênero e renda, pode apresentar vieses e não representar com precisão a realidade da população.
* É essencial considerar a ética e a responsabilidade ao lidar com dados pessoais, garantindo a privacidade e o uso adequado das informações.