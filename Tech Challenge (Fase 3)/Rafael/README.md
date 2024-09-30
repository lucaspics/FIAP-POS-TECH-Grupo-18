# Fine-Tuning de Modelo BERT para Perguntas e Respostas TC3

Este projeto utiliza um modelo BERT (Bidirectional Encoder Representations from Transformers) para realizar a tarefa de Perguntas e Respostas (Question Answering). O modelo é ajustado (fine-tuned) em um conjunto de dados específico para melhorar a precisão na identificação das respostas corretas dentro de um contexto textual.

## Integrantes do Grupo
Rafael RM356292

Lucas RM355916

Lucca RM353944

Paulo RM355014

Fábio RM354943

## Link para o vídeo de Apresentação
https://youtu.be/m9YltBhwGvs?si=NPRQCScmcFEhaGgv

## Pré-requisitos
Antes de executar o código, é necessário garantir que você tem o ambiente de desenvolvimento correto. A versão mínima do Python requerida é 3.6.

### Bibliotecas Necessárias

Para rodar este projeto, as seguintes bibliotecas são necessárias:
-	torch: Biblioteca para operações com tensores e desenvolvimento de modelos de aprendizado profundo.
-	transformers: Biblioteca do Hugging Face que fornece o modelo BERT, além de vários outros modelos de linguagem.
-	datasets: Facilita o carregamento e manipulação de datasets.
-	pandas: Usado para manipulação e análise de dados.
-	scikit-learn: Usada para a avaliação do modelo, provendo métricas e ferramentas de aprendizado de máquina.
-	json: Biblioteca padrão do Python para manipulação de dados em formato JSON.

Você pode instalar as bibliotecas necessárias usando \`pip\`:

\`\`\`bash
pip install torch transformers datasets pandas scikit-learn
\`\`\`

ou se apresentar erro de permissão:

\`\`\`bash
pip install --user torch transformers datasets pandas scikit-learn
\`\`\`

## Instalação

Clone este repositório ou baixe o código fonte para o seu computador. Certifique-se de que você possui o arquivo \`trn.json\` contendo o dataset no mesmo diretório do script.

## Uso

### Carregar o Dataset

O primeiro passo é carregar os dados a partir de um arquivo JSON. O dataset deve conter pelo menos as colunas \`title\` e \`content\`.

\`\`\`python
raw_data = load_dataset("trn.json")
\`\`\`

### Tokenização e Adição de Posições

A função \`add_token_positions\` tokeniza os dados e adiciona as posições de início e fim das respostas com base no contexto.

\`\`\`python
tokenized_data = dataset.map(lambda x: add_token_positions(x, tokenizer), batched=True)
\`\`\`

### Fine-Tuning do Modelo

O modelo BERT é ajustado usando o conjunto de dados tokenizado. O \`Trainer\` do Hugging Face é utilizado para gerenciar o processo de treinamento.

\`\`\`python
trainer = fine_tune_model(tokenized_data, tokenizer, model)
\`\`\`

### Avaliação do Modelo

Após o fine-tuning, o modelo é avaliado com um conjunto de dados de teste. Os resultados da avaliação são exibidos.

\`\`\`python
evaluate_model(trainer, tokenized_data['test'])
\`\`\`

### Geração de Respostas

Para gerar respostas, você pode usar a função \`generate_responses\`, que requer as perguntas e os contextos correspondentes.

\`\`\`python
response = generate_responses(model, tokenizer, question, context)
\`\`\`

## Exemplo de Execução

O código completo pode ser executado a partir da função principal \`main\`. O exemplo abaixo demonstra o fluxo completo do carregamento de dados, tokenização, treinamento e geração de respostas.

\`\`\`python
if __name__ == "__main__":
    main()
\`\`\`

Este fluxo inclui a geração de respostas antes e depois do fine-tuning, permitindo que você compare o desempenho do modelo.

## Conclusão

Após a execução do código, o modelo treinado e o tokenizer serão salvos na pasta \`./trained_model\`. Você pode utilizar este modelo para gerar respostas baseadas em perguntas e contextos fornecidos.

\`\`\`python
model.save_pretrained("./trained_model")
tokenizer.save_pretrained("./trained_model")
\`\`\`

### Observações Finais

Certifique-se de que os dados de entrada estejam formatados corretamente e que as bibliotecas estejam instaladas antes de executar o código.