
import os

def submit(data:str, group:str, model:str) -> None:
    if group is None:
        name = f'{model}'.replace('.csv', '')
        os.system(f"mkdir {name}")
        os.system(f"hpcsub -e {name}/STDERR -o {name}/STDOUT -jc jc.l -- /prj/shieldb1/mdml/examples/PD-L1/mdml {data} {name} -model_type {model} -id_col Molecule -target_col pIC50 -nproc 20 -debug")
    else:
        name = f'{group}_{model}'.replace('.csv', '')
        os.system(f"mkdir {name}")
        os.system(f"hpcsub -e {name}/STDERR -o {name}/STDOUT -jc jc.l -- /prj/shieldb1/mdml/examples/PD-L1/mdml {data} {name} -group {group} -model_type {model} -id_col Molecule -target_col pIC50 -nproc 20 -debug")

if __name__ == '__main__':
    for data in ['data.csv']:
        for group in [None, 'mean']:
            for model in ['linear', 'ridge', 'lasso', 'random_forest', 'gradient_boosting']:
                submit(data, group, model)



