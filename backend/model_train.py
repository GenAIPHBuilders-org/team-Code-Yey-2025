import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from catboost import CatBoostRegressor, Pool

data = pd.read_csv('backend/dataset/philippines_crop_prices_mock_data.csv')

#features
data['Date'] = pd.to_datetime(data['Date'])
data['Month'] = data['Date'].dt.month
data['Year'] = data['Date'].dt.year
data['Quarter'] = data['Date'].dt.quarter
data['DayOfYear'] = data['Date'].dt.dayofyear

data['Pest Outbreak'] = data['Pest Outbreak'].map({'No': 0, 'Yes': 1})
data['Rainfall_Temperature'] = data['Rainfall (mm)'] * data['Temperature (°C)']
data['Fertilizer_Fuel_Ratio'] = data['Fertilizer Cost (PHP/kg)'] / data['Fuel Price (PHP/liter)']
data.drop(columns=['Date'], inplace=True)

y = data['Price per kg']
X = data.drop(columns=['Price per kg'])

categorical_features = ['Region', 'Crop']

#train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
train_pool = Pool(X_train, y_train, cat_features=categorical_features)
test_pool = Pool(X_test, y_test, cat_features=categorical_features)

cat_model = CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    eval_metric='RMSE',
    random_seed=42,
    verbose=100,
    early_stopping_rounds=50
)

cat_model.fit(train_pool, eval_set=test_pool)

cat_pred = cat_model.predict(X_test)
cat_rmse = np.sqrt(mean_squared_error(y_test, cat_pred))

# rmse = 20.45

# cat_model.save_model('price_predictor.cbm')

# feature_names = cat_model.feature_names_
# print(feature_names)