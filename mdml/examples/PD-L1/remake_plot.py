
import pandas as pd
import os
from mdml import cli, plot

def remake_plot(path) -> None:
    cv_path = os.path.join(path, 'cross_validation.json')
    if os.path.exists(cv_path):
        cv = cli.load_json(cv_path)
        df = pd.DataFrame()
        df['ID'] = cv['ids']
        df['pred'] = cv['pred']
        df['obs'] = cv['obs']
        mean = df.groupby('ID').mean()
        plot.parity_plot(
            mean['pred'], mean['obs'], title='Cross-Validation', cod='Q^2',
            export_path=cv_path.replace('.json', '')
        )

if __name__ == '__main__':
    for path in os.listdir():
        remake_plot(path)


