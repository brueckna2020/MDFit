# MDML

Train machine learning models to predict potency from SimFPs and automatically identify
import interactions via feature importance.

## Installation

Build and activate a python 3 environment.

```
conda create -n mdml python=3.10
conda activate mdml
```

Install `mdml`.

```
git clone git@github.com:brueckna2020/MDFit.git
cd MDFit/mdml
pip install .
```

## Command Line Interface

After installation the `mdml_train` and `mdml_predict` command line scripts will be executable 
in the `mdml` environment.

### Train

Use pre-computed SimFPs to train regression models, evaluate performance using nested leave-one-
molecule-out cross-validation, and identify important interactions via feature importance. This
script generates a directory with the following results files.
- `model.pkl`: A model trained using all SimFP data.
- `cross_validation.json`: A summary of cross-validation results including predictions, observations, and feature importances from each fold and LOMO-CV metrics (computed using all folds).
- `cross_validation.svg`: A parity plot showing the LOMO-CV performance with metrics computed using the average predictions from SimFPs from different simulations for each molecule.
- `importance.csv`: The feature importance computed using the specified model type (e.g., weights for linear and node impurity for tree-based regressions).

```
usage: mdml_train [-h] [-debug] [-nproc NPROC] -target_col TARGET_COL -id_col ID_COL
                  [-drop_col DROP_COL [DROP_COL ...]] [-group GROUP] [-model_type MODEL_TYPE]
                  [-cv CV] [-lofo] [-nested]
                  input output

Train regression models, evaluate performance using nested leave-one-molecule-out cross-
validation, and identify important interactions via feature importance.

HELP:
  -h                    Show this help message and exit.
  -debug                Print debugging messages. (default: False)

COMPUTATION:
  -nproc NPROC          Number of processors to use for parallel computation. (default: 1)

DATA:
  input                 Path to CSV containing SimFP features, IDs, and target (optional).
  output                Directory path to save output files.
  -target_col TARGET_COL
                        Header of target column in training data CSV. (default: None)
  -id_col ID_COL        Header of compound ID column. (default: None)
  -drop_col DROP_COL [DROP_COL ...]
                        Columns that should be removed from the training CSV. (default: [])
  -group GROUP          Grouping method. The options include 'mean', 'min', and 'max'. Data will
                        be grouped by compound ID (id_col). (default: None)

MODEL:
  -model_type MODEL_TYPE
                        Regression model type. The options are 'linear', 'ridge', 'lasso',
                        'random_forest', and 'gradient_boosting'. (default: linear)
  -cv CV                Number of cross-validation folds to use in hyperparameter tuning. Specify
                        -1 for leave-one-out. (default: -1)
  -lofo                 Run leave-one-feature-out cross-validation analysis. (default: False)
  -nested               Toggle nested cross-validation. Hyperparamters will NOT be optimized in
                        each fold. (default: True)
```

### Predict

```
usage: mdml_predict [-h] [-debug] -model MODEL -id_col ID_COL [-drop_col DROP_COL [DROP_COL ...]]
                    [-group GROUP]
                    input output

Make predictions using trained MD simulation fingerprint models.

HELP:
  -h                    Show this help message and exit.
  -debug                Print debugging messages. (default: False)

DATA:
  input                 Path to CSV containing features and molecule IDs.
  output                Path to save prediction CSV.
  -model MODEL          Directory containing trained ML model (default: None)
  -id_col ID_COL        Header of compound ID column. (default: None)
  -drop_col DROP_COL [DROP_COL ...]
                        Columns that should be removed from the input feature CSV. (default: [])
  -group GROUP          Grouping method. The options include 'mean', 'min', and 'max'. Data will
                        be grouped by compound ID (id_col). (default: None)
```

