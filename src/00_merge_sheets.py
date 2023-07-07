import yaml
import argparse
import pandas as pd
from pathlib import Path


def merge_sheets(f, save_path):
    patient = pd.read_excel(f, sheet_name='patient')
    registratie = pd.read_excel(f, sheet_name='registratie')
    episode = pd.read_excel(f, sheet_name='episode')

    patient = patient.rename(columns={'uri':'patient_uri'})
    registratie = registratie.rename(columns={'uri':'registratie_uri'})
    episode = episode.rename(columns={'uri':'episode_uri'})

    df = patient.join(registratie.set_index('patient_uri'), on='patient_uri', rsuffix='_registratie')
    df = df.join(episode.set_index('registratie_uri'), on='registratie_uri', rsuffix='_episode')

    episode_sheets = [
        'chirurgie','radiotherapie','rfa','opname','chirurgie_ii',
        'tussklaar','fup','braf_dosisaanpassing','mek_dosisaanpassing',
        'anti_pd_1_dosisaanpassing','ipnicomb_uitstel','ipniond_uitstel'
    ]

    for sheet_name in episode_sheets:
        sheet = pd.read_excel(f, sheet_name=sheet_name).set_index('episode_uri')
        df = df.join(sheet, on='episode_uri', rsuffix=f"_{sheet_name}")

    df.to_csv(save_path)

parser = argparse.ArgumentParser()
parser.add_argument("config_name")

if __name__ == "__main__":
    args = parser.parse_args()

    with open(f"../config/{args.config_name}") as f:
        config = yaml.safe_load(f)

    for multiple_sheets_file in Path(config['multiple_sheet_files_folder']).iterdir():
        print(f'Merging {multiple_sheets_file.name}')

        save_path = Path(config['input_folder']) / (multiple_sheets_file.stem + '.csv')

        merge_sheets(multiple_sheets_file, save_path)
