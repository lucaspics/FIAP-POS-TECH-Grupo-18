import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

df = pd.DataFrame()
df_size = 10000

df["idade"] = np.random.randint(18, 90, size=df_size) # Idade entre 18 e 90 anos
df["genero"] = np.random.choice(["masculino", "feminino"], size=df_size) # Gênero masculino ou feminino
df["imc"] = np.random.randint(120, 500, size=df_size) / 10 # Indice de massa corpórea da pessoa
df["filhos"] = np.random.randint(0, 5, size=df_size) # Quantidade de filhos que a pessoa possui
df["fumante"] = np.random.choice(["sim", "não"], size=df_size) # Fumante ou não fumante
df["regiao"] = np.random.choice(["norte", "nordeste", "centro-oeste", "sul", "sudeste"], size=df_size) # Gênero masculino ou feminino

# Calcula os encargos de cada pessoa com base nos dados informados anteriormente

# Calculo base
df["encargos"] = (

        # IDADE
        df["idade"] * 80.33

        # IMC
        + df["imc"] * 255.52
)

# Multiplicadores
df["encargos"] = df["encargos"] + (

      # GÊNERO
      + np.where(df["genero"] == 'masculino', df["encargos"] * 0.1, 0) # Homens possuem maior taxa de mortalidade

      # FILHOS
      + np.where((df["genero"] == 'feminino') & (df["filhos"] > 0), df["encargos"] * 0.05, 0) # Mulheres que ja tiveram filhos possuem uma tendencia maior a aparição de sintomas de saúde

      # FUMANTE
      + np.where(df["fumante"] == 'sim', df["encargos"] * 0.5, 0) # Individuos fumantes apresentam um enorme acrescimo na taxa de aparição de sintomas de saúde

      # REGIÃO
      + np.where(df["regiao"].isin(["sul", "sudeste"]), df["encargos"] * 0.2, 0) # Regiões sul e sudeste possuem hospitais mais caros
)

print(df)

# Exporta arquivo com dados amostrais
df.to_csv(r'custos_medicos_individuais.csv', index = False)