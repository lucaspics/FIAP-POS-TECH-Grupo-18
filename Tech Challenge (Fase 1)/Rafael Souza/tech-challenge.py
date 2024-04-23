import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor

# 1. Exploração de Dados
dados = pd.read_csv('dados_ficticios.csv')
print(dados.head())
print(dados.describe())

sns.pairplot(dados)
plt.show()

# Converter variáveis categóricas em numéricas
label_encoder = LabelEncoder()
dados['gênero'] = label_encoder.fit_transform(dados['gênero'])
dados['fumante'] = label_encoder.fit_transform(dados['fumante'])
dados['região'] = label_encoder.fit_transform(dados['região'])

sns.heatmap(dados.corr(), annot=True, cmap='coolwarm')
plt.title('Matriz de Correlação')
plt.show()

# 2. Pré-processamento de Dados
print(dados.isnull().sum())

X = dados.drop('encargos', axis=1)
y = dados['encargos']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

scaler_y = StandardScaler()
y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1))

# 3. Modelagem
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.2, random_state=42)

# Modelo de Regressão Linear
modelo_linear = LinearRegression()
modelo_linear.fit(X_train, y_train)
y_pred_linear = modelo_linear.predict(X_test)

# Modelo de regressão Árvore de Decisão
modelo_arvore = DecisionTreeRegressor()
modelo_arvore.fit(X_train, y_train)
y_pred_arvore = modelo_arvore.predict(X_test)

# 4. Avaliação do Modelo
print('Regressão Linear:')
print('MSE:', mean_squared_error(y_test, y_pred_linear))
print('R^2:', r2_score(y_test, y_pred_linear))
print('\nÁrvore de Decisão:')
print('MSE:', mean_squared_error(y_test, y_pred_arvore))
print('R^2:', r2_score(y_test, y_pred_arvore))

# Gráfico de dispersão para o modelo de regressão linear
plt.scatter(y_test, y_pred_linear, color='blue', label='Regressão Linear')

# Gráfico de dispersão para o modelo de regressão com árvore de decisão
plt.scatter(y_test, y_pred_arvore, color='red', label='Árvore de Decisão')

plt.xlabel('Valores Reais')
plt.ylabel('Previsões')
plt.title('Valores Reais vs Previsões')
plt.legend()
plt.show()