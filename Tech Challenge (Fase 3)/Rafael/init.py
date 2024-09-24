import json
import torch
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, Trainer, TrainingArguments


# Carregar dataset
def load_dataset(path):
    """
    Carrega um dataset a partir de um arquivo JSON.

    Args:
        path (str): Caminho para o arquivo JSON que contém os dados.

    Returns:
        list: Lista de dicionários com os dados carregados.
    """
    try:
        with open(path, 'r') as file:
            data = [json.loads(line) for line in file]
        return data
    except FileNotFoundError:
        print(f"Erro: O arquivo {path} não foi encontrado.")
        return []
    except json.JSONDecodeError:
        print("Erro: O arquivo contém dados inválidos.")
        return []


# Função para encontrar os índices de início e fim da resposta no contexto
def add_token_positions(examples, tokenizer):
    """
    Adiciona as posições de início e fim das respostas no contexto e tokeniza os dados.

    Args:
        examples (dict): Dicionário com os exemplos de entrada (títulos e conteúdos).
        tokenizer: Tokenizer do modelo BERT.

    Returns:
        dict: Dados tokenizados com posições de início e fim das respostas.
    """
    start_positions = []
    end_positions = []

    # Considerando que a resposta será o conteúdo inteiro
    for i in range(len(examples['content'])):
        context = examples['content'][i]
        start_idx = 0
        end_idx = len(context) - 1  # A resposta será todo o contexto

        start_positions.append(start_idx)
        end_positions.append(end_idx)

    # Tokenizar o conteúdo
    tokenized_inputs = tokenizer(
        examples['content'],
        examples['title'],
        truncation=True,
        padding="max_length",
        max_length=512
    )

    tokenized_inputs["start_positions"] = start_positions
    tokenized_inputs["end_positions"] = end_positions

    return tokenized_inputs


# Função de avaliação do modelo
def evaluate_model(trainer, eval_dataset):
    """
    Avalia o modelo utilizando o dataset de validação.

    Args:
        trainer (Trainer): Objeto Trainer do Hugging Face.
        eval_dataset: Dataset de validação.

    Returns:
        None
    """
    eval_results = trainer.evaluate(eval_dataset)
    print(f"Avaliação do modelo: {eval_results}")


# Função de Fine-tuning com BERT
def fine_tune_model(tokenized_datasets, tokenizer, model):
    """
    Realiza o fine-tuning do modelo BERT utilizando os dados tokenizados.

    Args:
        tokenized_datasets (Dataset): Dataset tokenizado para treinamento e validação.
        tokenizer: Tokenizer do modelo BERT.
        model: Modelo BERT para fine-tuning.

    Returns:
        Trainer: Objeto Trainer após o treinamento.
    """
    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        save_total_limit=2,
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets['train'],
        eval_dataset=tokenized_datasets['test'],
        tokenizer=tokenizer
    )

    trainer.train()
    return trainer  # Retorna o objeto trainer para avaliação posterior


# Função para gerar respostas com BERT (QA)
def generate_responses(model, tokenizer, questions, contexts):
    """
    Gera respostas para perguntas dadas com base nos contextos fornecidos.

    Args:
        model: Modelo BERT treinado.
        tokenizer: Tokenizer do modelo BERT.
        questions (list): Lista de perguntas.
        contexts (list): Lista de contextos correspondentes.

    Returns:
        str: Resposta gerada pelo modelo.
    """
    inputs = tokenizer(contexts, questions, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

    # Pegando os índices da resposta
    answer_start_scores = outputs.start_logits
    answer_end_scores = outputs.end_logits

    all_tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
    answer_start = torch.argmax(answer_start_scores)
    answer_end = torch.argmax(answer_end_scores)

    return tokenizer.decode(input_ids[0][answer_start:answer_end + 1])


# Função principal
def main():
    dataset_path = "trn.json"  # Certifique-se de que este caminho esteja correto

    # Carregar o dataset
    raw_data = load_dataset(dataset_path)

    # Convertendo para DataFrame
    df = pd.DataFrame(raw_data)

    # Selecionando as colunas necessárias
    df = df[['title', 'content']]  # Removendo a coluna 'answer'

    # Removendo entradas com valores nulos
    df.dropna(inplace=True)

    # Reduzir o tamanho do dataset para acelerar o processamento (opcional)
    df = df.sample(n=500, random_state=42)

    # Transformar dados em um Dataset da Hugging Face
    dataset = Dataset.from_pandas(df)

    # Carregar modelo e tokenizer (BERT para Question Answering)
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    model = AutoModelForQuestionAnswering.from_pretrained("bert-base-uncased")

    # Tokenizar o dataset e adicionar as posições de início e fim das respostas
    tokenized_data = dataset.map(lambda x: add_token_positions(x, tokenizer), batched=True)

    # Remover as colunas que não são usadas pelo modelo
    tokenized_data = tokenized_data.remove_columns(['content', 'title'])

    # Dividir o dataset em treino e teste
    tokenized_data = tokenized_data.train_test_split(test_size=0.2)

    # Exemplo de perguntas e contexto para teste antes do fine-tuning
    test_contexts = [
        "O produto XYZ é um dispositivo de alta performance que oferece várias funcionalidades...",
        "O produto ABC vem com acessórios de primeira linha, como..."
    ]
    test_questions = [
        "Quais são as características do produto XYZ?",
        "O que contém na caixa do produto ABC?"
    ]

    # Testar o modelo antes do fine-tuning
    print("Respostas geradas pelo modelo antes do fine-tuning:")
    for i in range(len(test_questions)):
        response = generate_responses(model, tokenizer, test_questions[i], test_contexts[i])
        print(f"Pergunta {i + 1}: {test_questions[i]}")
        print(f"Resposta {i + 1}: {response}")
        print("")

    # Fine-tune no modelo
    trainer = fine_tune_model(tokenized_data, tokenizer, model)

    # Avaliar o modelo após o fine-tuning
    evaluate_model(trainer, tokenized_data['test'])

    # Testar o modelo após o fine-tuning
    print("Respostas geradas pelo modelo após o fine-tuning:")
    for i in range(len(test_questions)):
        response = generate_responses(model, tokenizer, test_questions[i], test_contexts[i])
        print(f"Pergunta {i + 1}: {test_questions[i]}")
        print(f"Resposta {i + 1}: {response}")
        print("")

    # Salvar o modelo treinado
    model.save_pretrained("./trained_model")
    tokenizer.save_pretrained("./trained_model")
    print("Modelo treinado e tokenizer salvos em './trained_model'.")


if __name__ == "__main__":
    main()
