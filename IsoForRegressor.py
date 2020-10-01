from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator
import numpy as np
import pandas as pd

class IsoForRegressor(BaseEstimator):
    
    def __init__(self, random_state=42, contamination=0.01, n_estimators=100):
        self.random_state = random_state
        self.contamination = contamination
        self.n_estimators = n_estimators
        
        self.iso_for = IsolationForest( 
                                        random_state=self.random_state,
                                        n_estimators=self.n_estimators,
                                        contamination=self.contamination
                                    )

        self.reg_for = RandomForestRegressor(
                                        random_state=self.random_state,
                                        n_estimators=self.n_estimators,
                                    )
        
    def iso_fit(self, X):
        self.iso_for.fit(X)

    def reg_fit(self, X, y):
        self.reg_for.fit(X, y)
    
    def standard_scaler(self, X):
        return (X - np.min(X))/(np.max(X) - np.min(X))

    def decision_function(self, X):
        return self.standard_scaler(self.iso_for.decision_function(X))

    def predict_anomalies(self, X):
        return self.iso_for.predict(X)

    def predict_anomalies_cutoff(self, X, cutoff):
        dec = self.decision_function(X)
        return pd.Series([1 if dec > cutoff else 0])
        
    def predict(self, X):
        iso_pred = self.iso_for.predict(X)
        reg_pred = self.reg_for.predict(X)
        return (iso_pred, reg_pred)

    def fit(self, X, y, cutoff=0.01):
        '''Fits the Isolation Forest on all of the data, 
        then it picks the data that can be considered "normal",
        and trains the RandomForestRegressor on that data with "target_col" as target.
        '''
        self.iso_fit(X)

        anomalies = self.predict_anomalies(X)
        self.X_norm = X.loc[anomalies == 1]
        self.X_anom = X.loc[anomalies == -1]
        self.y_norm = y.loc[anomalies == 1]
        self.y_anom = y.loc[anomalies == -1]

        self.reg_fit(self.X_norm, self.y_norm)


