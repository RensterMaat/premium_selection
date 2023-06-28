import argparse
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import warnings


warnings.filterwarnings("ignore")


parser = argparse.ArgumentParser()
parser.add_argument("config_name")
args = parser.parse_args()
with open(f"/home/rens/repos/premium_selection/config/{args.config_name}") as f:
    config = yaml.safe_load(f)


datasets = [
    ds.name
    for ds in Path(config["intermediate_output_folder"]).iterdir()
    if not "possible" in ds.name
]

coding = pd.read_csv(config["upn_to_study_coding"]).set_index("upn")
already_encoded = ["lumc.csv", "maxima.csv", "mst.csv", "umcg.csv"]


# loop through the preprocessed dataframe of every center
stack = []
for fp in datasets:
    print("#" * 100)
    print("Processing dataset {}\n".format(fp))

    # combine datasets of automatically and manually included patients
    dataset = pd.read_csv(Path(config["intermediate_output_folder"]) / fp)
    possible = pd.read_csv(
        Path(config["intermediate_output_folder"]) / (fp[:-4] + "_possible.csv")
    )
    to_add = possible[possible.upn.isin(config["include_with_other_therapy"][fp])]
    print(
        "Adding {} entries manually.\n".format(
            len(config["include_with_other_therapy"][fp])
        )
    )

    dataset = pd.concat([dataset, to_add])
    dataset["center"] = [fp[:-4]] * len(dataset)

    # check if patient ids have already been encoded
    if fp in already_encoded:
        # if yes, format the ids to have only _ instead of -
        dataset["id"] = [
            code.replace("-", "_") if not pd.isna(code) else code
            for code in dataset.upn
        ]

    else:
        # if no, find the corresponding code for every patient from the coding csv
        codes = []
        missing = []
        for upn in dataset.upn:
            try:
                codes.append(
                    coding.loc[
                        str(int(upn)) if type(upn) == float else upn, "premium_id"
                    ]
                )
            except:
                codes.append(float("nan"))
                missing.append(upn)
        dataset["id"] = codes

        print("No IDs are supplied for the following upns: \n{}\n".format(str(missing)))

    # change date of birth to year of birth
    if "gebdat" in dataset.columns:
        dataset["gebjaar"] = dataset["gebdat"].astype("datetime64[ns]").dt.year

    # drop columns with patient information
    for col in ["voorl", "tussen", "naam", "pcode", "gebdat", "land"]:
        if col in dataset.columns:
            dataset = dataset.drop(columns=[col])

    stack.append(dataset)

# combine dataframes of all centers
dmtr = pd.concat(stack)
dmtr["age"] = dmtr["start_date"].astype("datetime64[ns]").dt.year - dmtr["gebjaar"]
dmtr = dmtr.replace({"geslacht": {1: "Male", 2: "Female"}})

# fill some missing values for age and therapy
dmtr.loc["PREM_LU_109", "Age"] = 68
dmtr.loc["PREM_LU_212", "Age"] = 63
dmtr.loc["PREM_LU_413", "Age"] = 62
dmtr.loc["PREM_RA_232", "Age"] = 25
dmtr.loc["PREM_RA_235", "Age"] = 51
dmtr.loc["PREM_UMCU_010", "Age"] = 78
dmtr.loc["PREM_UMCU_029", "Age"] = 89
dmtr.loc["PREM_VU_178", "Age"] = 56
dmtr.loc["PREM_ZU_029", "Age"] = 57
dmtr.loc["PREM_VU_178", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_ZU_029", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_AM_004", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_AM_054", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_AM_067", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AM_123", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_IS_140", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_IS_141", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_IS_142", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_RA_105", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["IM_102", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["IM_248", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["IM_206", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_VU_186", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_VU_187", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_VU_188", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_VU_189", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_VU_190", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_VU_191", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_IS_143", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_LU_492", "Therapy"] = "Anti-PD1"
dmtr.loc["MAX_199", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_UMCU_040", "Therapy"] = "Anti-PD1"
dmtr.loc["PREM_AVL_578", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_579", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_581", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_583", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_584", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_586", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_588", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_591", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_593", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_595", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_596", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_597", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_598", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_599", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_600", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_603", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_604", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_605", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_606", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_607", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_609", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_611", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_612", "Therapy"] = "Ipilimumab & Nivolumab"
dmtr.loc["PREM_AVL_629", "Therapy"] = "Anti-PD1"

# save final file
dmtr.to_csv(config["output_file"], index=False)
