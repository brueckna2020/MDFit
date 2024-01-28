# PD-L1 Example

The following commands will reproduce the PD-L1 modeling and feature importance from the MDFit paper.

Evaluate models with duplicate SimFPs included.
```
mdml_train data.csv linear -nproc 10 -id_col Molecule -target_col pIC50 -model_type linear
mdml_train data.csv ridge -nproc 10 -id_col Molecule -target_col pIC50 -model_type ridge
mdml_train data.csv lasso -nproc 10 -id_col Molecule -target_col pIC50 -model_type lasso
mdml_train data.csv random_forest -nproc 10 -id_col Molecule -target_col pIC50 -model_type random_forest
mdml_train data.csv gradient_boosting -nproc 10 -id_col Molecule -target_col pIC50 -model_type gradient_boosting
```

Evaluate models with averaged SimFPs.
```
mdml_train data.csv linear_mean -nproc 10 -id_col Molecule -target_col pIC50 -model_type linear -group mean
mdml_train data.csv ridge_mean -nproc 10 -id_col Molecule -target_col pIC50 -model_type ridge -group mean
mdml_train data.csv lasso_mean -nproc 10 -id_col Molecule -target_col pIC50 -model_type lasso -group mean
mdml_train data.csv random_forest_mean -nproc 10 -id_col Molecule -target_col pIC50 -model_type random_forest -group mean
mdml_train data.csv gradient_boosting_mean -nproc 10 -id_col Molecule -target_col pIC50 -model_type gradient_boosting -group mean
```

**Note:** Metrics (e.g., $Q^2$) in `cross_validation.json` are computed using all entries (duplicates included) 
while metrics in `cross_validation.svg` are computed using the average of the predictions with SimFPs from 
different simulations for each molecule.
