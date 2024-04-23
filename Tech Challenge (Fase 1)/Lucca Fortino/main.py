import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Carregando o arquivo de dados
FILE_PATH = 'db/clients_filled.csv'

# Leitura dos dados
df = pd.read_csv(FILE_PATH)

# Análise dos dados
def eda_analysis(df):
    # Informações sobre o Dataset
    print("Informações sobre o dataset:")
    print(df.info())

    # Estatísticas descritivas para colunas numéricas
    print("\nEstatísticas Descritivas para Colunas Numéricas:")
    print(df.describe())

    # Histogramas para colunas numéricas
    plt.figure(figsize=(12, 8))
    for i, col in enumerate(df.select_dtypes(include=['int64', 'float64']).columns):
        plt.subplot(2, 2, i + 1)
        sns.histplot(data=df, x=col, kde=True)
        plt.title(f'Histograma de {col}')
    plt.tight_layout()
    plt.show()

    # Transformar colunas categóricas em colunas numéricas usando One-Hot Encoding
    categorical_cols = df.select_dtypes(include=['object']).columns
    encoder = OneHotEncoder(drop='first')
    encoded_cols = encoder.fit_transform(df[categorical_cols])

    # Criar DataFrame com as colunas codificadas
    df_encoded = pd.DataFrame(encoded_cols.toarray(), columns=encoder.get_feature_names_out(categorical_cols))

    # Matriz de Correlação das features
    plt.figure(figsize=(10, 8))
    correlation_matrix = df_encoded.corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Matriz de Correlação das Features')
    plt.show()

    # Gráfico de Boxplot para identificar outliers
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_encoded, orient='h')
    plt.title('Gráfico de Boxplot das Features')
    plt.show()

    # Contagem de valores únicos para colunas categóricas
    for col in df.select_dtypes(include=['object']).columns:
        print(f"\nContagem de valores únicos para {col}:")
        print(df[col].value_counts())

# Limpeza de Dados
def data_cleaning(data):
    print("Valores nulos por coluna:")
    print(data.isnull().sum())
    data.dropna(inplace=True)

# Pré-processamento
def data_preprocessing(data):
    feature_target = 'encargos'
    X = data.drop(feature_target, axis=1)
    y = data[feature_target]
    categorical_cols = X.select_dtypes(include=['object']).columns
    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ])
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])
    preprocessor = ColumnTransformer(transformers=[
        ('cat', categorical_transformer, categorical_cols),
        ('num', numeric_transformer, numeric_cols)
    ])
    X_processed = preprocessor.fit_transform(X)
    return X_processed, y

# Modelagem de Dados
def data_modeling(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    linear_reg = LinearRegression()
    decision_tree_reg = DecisionTreeRegressor(random_state=42)
    random_forest_reg = RandomForestRegressor(random_state=42)
    linear_reg.fit(X_train, y_train)
    decision_tree_reg.fit(X_train, y_train)
    random_forest_reg.fit(X_train, y_train)
    y_pred_linear = linear_reg.predict(X_test)
    y_pred_tree = decision_tree_reg.predict(X_test)
    y_pred_forest = random_forest_reg.predict(X_test)
    return y_test, y_pred_linear, y_pred_tree, y_pred_forest

# Avaliação dos modelos
def evaluate_models(y_test, y_pred_linear, y_pred_tree, y_pred_forest):
    mse_linear = mean_squared_error(y_test, y_pred_linear)
    mse_tree = mean_squared_error(y_test, y_pred_tree)
    mse_forest = mean_squared_error(y_test, y_pred_forest)
    r2_linear = r2_score(y_test, y_pred_linear)
    r2_tree = r2_score(y_test, y_pred_tree)
    r2_forest = r2_score(y_test, y_pred_forest)

    models_data = [
        {"nome": 'Regressão Linear', "mse": mse_linear, "r2": r2_linear, "y_pred": y_pred_linear},
        {"nome": 'Árvore de Decisão', "mse": mse_tree, "r2": r2_tree, "y_pred": y_pred_tree},
        {"nome": 'Random Forest', "mse": mse_forest, "r2": r2_forest, "y_pred": y_pred_forest},
    ]

    best_model = min(models_data, key=lambda x: x["mse"])

    print(f"\nMelhor modelo: {best_model['nome']}")
    print(f"Erro Quadrático Médio (MSE): {best_model['mse']:.2f}")
    print(f"Coeficiente de Determinação R^2: {best_model['r2']:.2f}")

    return best_model

# Função para visualizar a comparação entre valores reais e previstos
def plot_predictions(y_test, y_pred):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, color='green', label='Previsto')
    plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red', linestyle='--', lw=2, label='Real')
    plt.title('Valores Reais vs Valores Previstos')
    plt.xlabel('Valores Reais')
    plt.ylabel('Valores Previstos')
    plt.legend()
    plt.grid(True)
    plt.show()

# Chamadas das funções
eda_analysis(df)
data_cleaning(df)
X_processed, y = data_preprocessing(df)
y_test, y_pred_linear, y_pred_tree, y_pred_forest = data_modeling(X_processed, y)

best_model = evaluate_models(y_test, y_pred_linear, y_pred_tree, y_pred_forest)

# Chamada da função para plotar as previsões do melhor modelo
plot_predictions(y_test, best_model["y_pred"])
