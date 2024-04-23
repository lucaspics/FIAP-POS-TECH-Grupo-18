# Modelo Preditivo de Custos de Seguro de Saúde

Este é um código Python que desenvolve um modelo preditivo de regressão para prever o valor dos custos médicos individuais cobrados pelo seguro de saúde com base em características como idade, gênero, IMC, número de filhos, se a pessoa é fumante e a região onde mora.

## Pré-requisitos

Certifique-se de ter Python instalado no seu computador. Você também precisa instalar as seguintes bibliotecas Python:

- pandas
- seaborn
- matplotlib
- scikit-learn

Você pode instalar essas bibliotecas usando o pip. Por exemplo:

pip install pandas seaborn matplotlib scikit-learn

## Como usar

1. Clone ou baixe este repositório para o seu computador.
2. Coloque seu conjunto de dados em um arquivo CSV chamado `arquivo.csv` no mesmo diretório que o script Python.
3. Execute o script Python `tech-challenge.py`.

O script irá:

1. Carregar o conjunto de dados e explorar suas características.
2. Converter variáveis categóricas em numéricas.
3. Pré-processar os dados, escalando as variáveis e dividindo-os em conjuntos de treinamento e teste.
4. Treinar modelos de regressão linear e árvore de decisão.
5. Avaliar o desempenho dos modelos e mostrar um gráfico com as previsões versus os valores reais.

## Resultados

O script imprimirá o Mean Squared Error (MSE) e o Coefficient of Determination (R²) como métricas de avaliação dos modelos. Além disso, você verá um gráfico mostrando as previsões do modelo versus os valores reais dos custos médicos.


# Conjunto de Dados Fictícios para Simulação

Este conjunto de dados fictícios foi gerado para simulação e demonstração. Ele contém informações fictícias sobre idade, gênero, índice de massa corporal (IMC), número de filhos, hábito de fumar, região e encargos. As seguintes seções fornecem detalhes sobre como esses dados foram gerados.

## Detalhes da Geração

- **Total de Registros:** 10.000
- **Distribuição de Gênero:** A distribuição de gênero não é explicitamente controlada no código fornecido. No entanto, foi modificado para garantir uma distribuição exata de 50% masculino e 50% feminino.
- **Faixa Etária:** Os registros foram gerados com idades entre 18 e 80 anos, seguindo uma distribuição uniforme.
- **IMC:** O IMC foi calculado com base em dados simulados de altura e peso, seguindo uma distribuição uniforme entre 18 e 40.
- **Filhos:** O número de filhos por pessoa foi gerado com uma média de 1.5 filhos, seguindo uma distribuição binomial.
- **Fumante:** O hábito de fumar foi simulado com 20% dos registros sendo fumantes e 80% não fumantes.
- **Região:** A distribuição dos registros foi proporcional às populações regionais do Brasil.
- **Encargos:** Os encargos foram simulados com base em diversos fatores, incluindo idade, gênero, região, renda e outros, seguindo um modelo probabilístico.

## Observações Importantes

- Este conjunto de dados é fictício e destinado apenas para fins de simulação e demonstração. Não deve ser utilizado para análises estatísticas ou de pesquisa sem a devida avaliação por especialistas.
- A simulação de dados pessoais, como idade, gênero e renda, pode apresentar vieses e não representar com precisão a realidade da população.
- É essencial considerar a ética e a responsabilidade ao lidar com dados pessoais, garantindo a privacidade e o uso adequado das informações.