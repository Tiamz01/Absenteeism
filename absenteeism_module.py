# Import all the necessary libraries
import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin


# The custom scaler class
class CustomScaler(BaseEstimator, TransformerMixin):
    def __init__(self, columns, copy=True, with_mean=True, with_std=True):
        self.scaler = StandardScaler(copy=copy, with_mean=with_mean, with_std=with_std)
        self.columns = columns
        self.mean_ = None
        self.var_ = None

    def fit(self, X, y=None):
        self.scaler.fit(X[self.columns], y)
        self.mean_ = np.mean(X[self.columns])
        self.var_ = np.var(X[self.columns])
        return self

    def transform(self, X):
        init_col_order = X.columns
        X_scaled = pd.DataFrame(
            self.scaler.transform(X[self.columns]), columns=self.columns
        )
        X_not_scaled = X.loc[:, ~X.columns.isin(self.columns)]
        return pd.concat([X_not_scaled, X_scaled], axis=1)[init_col_order]


# Create the special class for predicting new data
class absenteeism_model:
    def __init__(self, model_file, scaler_file):
        # Read the 'model' and 'scaler' files which were saved
        with open("model", "rb") as model_file, open(
            "absenteeism_scaler", "rb"
        ) as scaler_file:
            self.linreg = pickle.load(model_file)
            self.scaler = pickle.load(scaler_file)
            self.data = None

    # Take a data file (*.csv) and preprocess it
    def load_and_clean_data(self, data_file):
        # Import the data
        df = pd.read_csv(data_file, delimiter=",")

        # Store the data in a new variable for later use
        self.df_with_predictions = df.copy()

        # Drop the 'ID' column
        df = df.drop(["ID"], axis=1)

        # To preserve the code we've created in the previous section, we will add a column with 'NaN' strings
        df["Absenteeism Time in Hours"] = "NaN"

        # Create a separate dataframe containing dummy values for ALL available reasons
        reason_columns = (
            pd.get_dummies(df["Reason for Absence"], drop_first=True)
            .astype(int)
            .applymap(int)
        )

        # Split reason_columns into 4 types
        reason_type_1 = reason_columns.loc[:, 1:14].max(axis=1)
        reason_type_2 = reason_columns.loc[:, 15:17].max(axis=1)
        reason_type_3 = reason_columns.loc[:, 18:21].max(axis=1)
        reason_type_4 = reason_columns.loc[:, 22:].max(axis=1)

        # To avoid multicollinearity, drop the 'Reason for Absence' column from df
        df = df.drop(["Reason for Absence"], axis=1)

        # Concatenate df and the 4 types of reasons for absence
        df = pd.concat(
            [df, reason_type_1, reason_type_2, reason_type_3, reason_type_4], axis=1
        )

        # Assign names to the 4 reason type columns
        column_names = [
            "Date",
            "Transportation Expense",
            "Distance to Work",
            "Age",
            "Daily Work Load Average",
            "Body Mass Index",
            "Education",
            "Children",
            "Pet",
            "Absenteeism Time in Hours",
            "Reason_1",
            "Reason_2",
            "Reason_3",
            "Reason_4",
        ]
        df.columns = column_names

        # Re-order the columns in df
        column_names_reordered = [
            "Reason_1",
            "Reason_2",
            "Reason_3",
            "Reason_4",
            "Date",
            "Transportation Expense",
            "Distance to Work",
            "Age",
            "Daily Work Load Average",
            "Body Mass Index",
            "Education",
            "Children",
            "Pet",
            "Absenteeism Time in Hours",
        ]
        df = df[column_names_reordered]

        # Convert the 'Date' column into datetime
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

        # Create a list with month values retrieved from the 'Date' column
        list_months = []
        for i in range(df.shape[0]):
            list_months.append(df["Date"][i].month)

        # Insert the values in a new column in df, called 'Month Value'
        df["Month Value"] = list_months

        # Create a new feature called 'Day of the Week'
        df["Day of the Week"] = df["Date"].apply(lambda x: x.weekday())

        # Drop the 'Date' column from df
        df = df.drop(["Date"], axis=1)

        # Re-order the columns in df
        column_names_upgrade = [
            "Reason_1",
            "Reason_2",
            "Reason_3",
            "Reason_4",
            "Month Value",
            "Day of the Week",
            "Transportation Expense",
            "Distance to Work",
            "Age",
            "Daily Work Load Average",
            "Body Mass Index",
            "Education",
            "Children",
            "Pet",
            "Absenteeism Time in Hours",
        ]
        df = df[column_names_upgrade]

        # Map 'Education' variables; the result is a dummy
        df["Education"] = df["Education"].map({1: 0, 2: 1, 3: 1, 4: 1})

        # Replace the NaN values
        df = df.fillna(value=0)

        # Drop the original absenteeism time
        df = df.drop(["Absenteeism Time in Hours"], axis=1)

        # Drop the variables we decide we don't need
        df = df.drop(
            ["Day of the Week", "Distance to Work", "Daily Work Load Average"], axis=1
        )

        # We have included this line of code if you want to call the 'preprocessed data'
        self.preprocessed_data = df.copy()

        # Initialize the scaler
        self.scaler = CustomScaler(
            columns=df.columns, copy=True, with_mean=True, with_std=True
        )

        # fit and transform the data using the scaler
        self.data = self.scaler.fit_transform(df)

    # A function which outputs the probability of a data point to be 1
    def predicted_probability(self):
        if self.data is not None:
            pred = self.linreg.predict_proba(self.data)[:, 1]
            return pred

    # A function which outputs 0 or 1 based on our model
    def predicted_output_category(self):
        if self.data is not None:
            pred_outputs = self.linreg.predict(self.data)
            return pred_outputs

    # Predict the outputs and the probabilities and add columns with these values at the end of the new data
    def predicted_outputs(self):
        if self.data is not None:
            self.preprocessed_data["Probability"] = self.linreg.predict_proba(
                self.data
            )[:, 1]
            self.preprocessed_data["Prediction"] = self.linreg.predict(self.data)
            return self.preprocessed_data
