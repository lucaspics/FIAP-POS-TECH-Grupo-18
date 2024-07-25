# GRUPO 18 - POSTECH - IA PARA DEVS
# Rafael RM356292
# Lucas RM355916
# Lucca RM353944
# Paulo RM355014
# Fábio RM354943

import random  # Importa a biblioteca random para manipulação aleatória
import pandas as pd  # Importa a biblioteca pandas para manipulação de dados
from itertools import groupby  # Importa a função groupby da biblioteca itertools para agrupar dados
import matplotlib.pyplot as plt  # Importa a biblioteca matplotlib para criação de gráficos

# Parâmetros do algoritmo genético
POPULATION_SIZE = 100
NUM_GENERATIONS = 50
MUTATION_RATE = 0.01

# Dimensões da gôndola
num_rows = 10
num_cols = 4

# Caminho do arquivo CSV com dados dos produtos
FILE_PATH = 'db/supermarket_products.csv'

# Carrega os dados dos produtos do arquivo CSV
products_data = pd.read_csv(FILE_PATH).to_dict('records')

# Função para criar um indivíduo (layout aleatório de produtos)
def create_individual():
    layout = products_data[:]
    random.shuffle(layout)
    return layout

# Função para criar a população inicial de indivíduos
def create_population(size):
    return [create_individual() for _ in range(size)]

# Função de avaliação (fitness) de um indivíduo
def fitness(individual):
    score = 0
    for i in range(len(individual) - 1):
        # Aumenta a pontuação se produtos adjacentes pertencem à mesma categoria
        if individual[i]["category"] == individual[i + 1]["category"]:
            score += individual[i]["frequency"] + individual[i + 1]["frequency"]
        else:
            score -= 20  # Penaliza se os produtos adjacentes são de categorias diferentes
        # Aumenta a pontuação se a frequência de ambos os produtos adjacentes for alta
        if individual[i]["frequency"] > 50 and individual[i + 1]["frequency"] > 50:
            score += 10
    return score

# Função para selecionar os melhores indivíduos da população
def select(population):
    sorted_population = sorted(population, key=lambda ind: fitness(ind), reverse=True)
    return sorted_population[:POPULATION_SIZE // 2]

# Função de crossover (recombinação) entre dois indivíduos
def crossover(parent1, parent2):
    crossover_point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:crossover_point] + [item for item in parent2 if item not in parent1[:crossover_point]]
    child2 = parent2[:crossover_point] + [item for item in parent1 if item not in parent2[:crossover_point]]
    return child1, child2

# Função de mutação de um indivíduo
def mutate(individual):
    if random.random() < MUTATION_RATE:
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]

# Função para plotar o layout da gôndola
def plot_gondola_layout(layout):
    sorted_layout = sorted(layout, key=lambda x: (x["category"], -x["frequency"]))

    table_data = [["" for _ in range(num_cols)] for _ in range(num_rows)]
    cell_colors = [["w" for _ in range(num_cols)] for _ in range(num_rows)]
    category_colors = {
        "Bebidas": "lightblue",
        "Laticínios": "lightgreen",
        "Higiene": "lightyellow",
        "Hortifruti": "lightcoral",
        "Carnes": "lightpink",
        "Grãos": "lightgray",
        "Limpeza": "lightsalmon",
        "Massas": "lightgoldenrodyellow",
        "Snacks": "lightcyan"
    }

    def generate_random_color():
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def add_category_color(category):
        if category not in category_colors:
            category_colors[category] = generate_random_color()

    for product in products_data:
        add_category_color(product["category"])

    current_col = 0
    current_row = 0
    for category, items in groupby(sorted_layout, key=lambda x: x["category"]):
        items = list(items)
        while items:
            if current_row + len(items) <= num_rows:
                for item in items:
                    table_data[current_row][current_col] = item["name"]
                    cell_colors[current_row][current_col] = category_colors[item["category"]]
                    current_row += 1
                items = []
            else:
                remaining_space = num_rows - current_row
                for i in range(remaining_space):
                    item = items.pop(0)
                    table_data[current_row][current_col] = item["name"]
                    cell_colors[current_row][current_col] = category_colors[item["category"]]
                    current_row += 1
                current_row = 0
                current_col += 1

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=table_data, cellLoc='center', loc='center', cellColours=cell_colors,
                     colWidths=[0.25] * num_cols)
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)
    plt.title('Layout Final da Gôndola')
    plt.show()

# Função principal do algoritmo genético
def genetic_algorithm():
    population = create_population(POPULATION_SIZE)
    best_layouts = []
    fitness_scores = []

    for generation in range(NUM_GENERATIONS):
        population = select(population)
        next_generation = []

        while len(next_generation) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population, 2)
            child1, child2 = crossover(parent1, parent2)
            mutate(child1)
            mutate(child2)
            next_generation.extend([child1, child2])

        population = next_generation
        best_individual = max(population, key=fitness)
        best_layouts.append(best_individual)
        fitness_scores.append(fitness(best_individual))
        print(f'Geração {generation + 1}: Melhor pontuação = {fitness(best_individual)}')

    best_layout = max(population, key=fitness)
    print('Melhor layout final:', best_layout)

    plt.figure(figsize=(10, 5))
    plt.plot(range(1, NUM_GENERATIONS + 1), fitness_scores, marker='o')
    plt.title('Evolução da Pontuação de Fitness')
    plt.xlabel('Geração')
    plt.ylabel('Pontuação de Fitness')
    plt.grid(True)
    plt.show()

    plot_gondola_layout(best_layout)

    return best_layouts

# Executa o algoritmo genético
if __name__ == '__main__':
    best_layouts = genetic_algorithm()

    # Salva os melhores layouts de cada geração em um arquivo de texto
    with open('best_layouts.txt', 'w') as f:
        for generation, layout in enumerate(best_layouts, start=1):
            f.write(f"Geração {generation}:\n")
            for product in layout:
                f.write(f"{product['name']} ({product['category']}) - Frequência: {product['frequency']}\n")
            f.write("\n")
