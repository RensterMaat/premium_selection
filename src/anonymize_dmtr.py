import pandas as pd
import os
import numpy as np
from pathlib import Path

r = Path(r"C:\Users\user\repos\PREMIUM\code\radiomics_paper")

datasets = [
    ds for ds in os.listdir(r / "data" / "processed_dmtr") if not "possible" in ds
]



already_encoded = ["lumc.csv", "maxima.csv", "mst.csv", "umcg.csv"]

stack = []
for fp in datasets:
    print("#" * 100)
    print("Processing dataset {}\n".format(fp))

    dataset = pd.read_csv(r / "data" / "processed_dmtr" / fp)

    possible = pd.read_csv(r / "data" / "processed_dmtr" / (fp[:-4] + "_possible.csv"))
    to_add = possible[possible.upn.isin(manually_added[fp])]
    print("Adding {} entries manually.\n".format(len(manually_added[fp])))

    dataset = dataset.append(to_add)
    dataset["center"] = [fp[:-4]] * len(dataset)

    if fp in already_encoded:
        dataset["id"] = [
            code.replace("-", "_") if not pd.isna(code) else code
            for code in dataset.upn
        ]

    else:
        conversion = pd.read_excel(r / "data" / "coding" / (fp[:-4] + ".xlsx"))
        if not dataset.upn.dtype == float:
            conversion["Patientnummer"] = conversion["Patientnummer"].astype(str)
            dataset["upn"] = dataset["upn"].astype(str)

        conversion = conversion.set_index("Patientnummer")

        codes = []
        missing = []
        for upn in dataset.upn:
            try:
                codes.append(conversion.loc[upn][0])
            except:
                codes.append(float("nan"))
                missing.append(upn)
        dataset["id"] = codes

        print("No IDs are supplied for the following upns: \n{}\n".format(str(missing)))
        print(
            "IDs for the following upns were supplied, but not used: \n{}\n".format(
                str([ID for ID in conversion.index if not ID in dataset.upn.values])
            )
        )

    if "gebdat" in dataset.columns:
        dataset["gebjaar"] = dataset["gebdat"].astype(np.datetime64).dt.year
    for col in ["voorl", "tussen", "naam", "pcode", "gebdat", "land"]:
        if col in dataset.columns:
            dataset = dataset.drop(columns=[col])

    stack.append(dataset)

dmtr = pd.concat(stack)
dmtr["age"] = dmtr["start_date"].astype(np.datetime64).dt.year - dmtr["gebjaar"]
dmtr = dmtr.replace({"geslacht": {1: "Male", 2: "Female"}})

dmtr.to_csv(r / "dmtr3.csv", index=False)
