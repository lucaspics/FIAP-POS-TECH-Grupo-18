# Projeto de Otimização de Layout de Gôndola

## Descrição
Este projeto utiliza um algoritmo genético para otimizar o layout de uma gôndola de supermercado, agrupando produtos de forma a maximizar a conveniência para os clientes e aumentar a pontuação de fitness baseada na frequência e categorias dos produtos.

## Integrantes do Grupo
- **Rafael RM356292**
- **Lucas RM355916**
- **Lucca RM353944**
- **Paulo RM355014**
- **Fábio RM354943**

## Apresentação em Vídeo
https://youtu.be/Wp6ZQkQCezQ?si=5aostoBH0VTqjeGa

## Bibliotecas Utilizadas
- `random`: Para geração de números aleatórios.
- `pandas`: Para manipulação e leitura de dados.
- `itertools.groupby`: Para agrupamento de dados.
- `matplotlib`: Para criação de gráficos.

## Estrutura do Código
O código é composto pelas seguintes funções principais:

- **create_individual**: Cria um layout aleatório de produtos.
- **create_population**: Cria a população inicial de indivíduos.
- **fitness**: Avalia a pontuação (fitness) de um indivíduo.
- **select**: Seleciona os melhores indivíduos da população.
- **crossover**: Realiza o crossover (recombinação) entre dois indivíduos.
- **mutate**: Realiza a mutação de um indivíduo.
- **plot_gondola_layout**: Plota o layout da gôndola.
- **genetic_algorithm**: Função principal do algoritmo genético.

## Execução
Para executar o algoritmo genético e gerar o layout otimizado da gôndola, execute o script principal:

```bash
python gondola_optimization.py
```

## Resultados

### Layout Final da Gôndola
O layout final da gôndola é gerado e exibido como uma tabela colorida, onde cada cor representa uma categoria de produtos.

### Evolução da Pontuação de Fitness
A evolução da pontuação de fitness ao longo das gerações é exibida em um gráfico, mostrando o progresso do algoritmo genético.

### Arquivos Gerados
best_layouts.txt: Arquivo de texto contendo os melhores layouts de cada geração, com a categoria e frequência de cada produto.

## Exemplo de Uso
- Configuração dos Parâmetros: Os parâmetros do algoritmo genético (tamanho da população, número de gerações e taxa de mutação) podem ser ajustados no início do script.

- Dados dos Produtos: Os dados dos produtos são carregados a partir de um arquivo CSV (db/supermarket_products.csv). Certifique-se de que o arquivo está no formato correto e no caminho especificado.

- Execução do Algoritmo: Execute o script para iniciar o algoritmo genético e visualizar os resultados.

