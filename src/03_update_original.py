import yaml
import pandas as pd

with open(f"../config/config_updated.yaml") as f:
    config_updated = yaml.safe_load(f)

updated_dmtr = pd.read_csv(config_updated["output_file"]).set_index("id")

with open(f"../config/config_original.yaml") as f:
    config_original = yaml.safe_load(f)

original_dmtr = pd.read_csv(config_original["output_file"]).set_index("id")

matched_step1 = original_dmtr.join(
    updated_dmtr, lsuffix="_original", rsuffix="_updated", how="inner"
)

unmatched_original = original_dmtr[
    ~original_dmtr.index.isin(matched_step1.index.tolist())
]
unmatched_updated = updated_dmtr[~updated_dmtr.index.isin(matched_step1.index.tolist())]

unmatched_original = unmatched_original[unmatched_original.center.isin(["lumc", "mst"])]

key = ["gebjaar", "datprim", "start_date"]

matched_step2 = (
    unmatched_original.reset_index()
    .set_index(key)
    .join(
        unmatched_original.set_index(key),
        lsuffix="_original",
        rsuffix="_updated",
        how="inner",
    )
    .set_index("id")
)

all_matched = pd.concat([matched_step1, matched_step2])

endpoints = [
    "fu_OS",
    "event_OS",
    "fu_PFS",
    "event_PFS",
    "dcb",
    "orr",
    "Best overall response",
]

merged_dmtr = original_dmtr.join(
    all_matched[[f"{p}_updated" for p in endpoints]], how="outer"
)

missing_patient_level_labels = pd.read_csv(
    r"C:\Users\user\data\tables\missing_patient_level_labels.csv", sep=";"
).set_index("patient")

dcb = []
response = []
for ix, row in merged_dmtr.iterrows():
    if pd.isna(row.dcb):
        if ix in missing_patient_level_labels.index:
            dcb.append(missing_patient_level_labels.loc[ix, "dcb"])
        else:
            dcb.append(float("nan"))
    else:
        dcb.append(row.dcb)

    if pd.isna(row.orr):
        if ix in missing_patient_level_labels.index:
            response.append(missing_patient_level_labels.loc[ix, "response"])
        else:
            response.append(float("nan"))
    else:
        response.append(row.orr)

merged_dmtr["dcb"] = dcb
merged_dmtr["orr"] = response

for endpoint in endpoints:
    values = []
    for ix, row in merged_dmtr.iterrows():
        if pd.isna(row[f"{endpoint}_updated"]):
            values.append(row[endpoint])
        else:
            values.append(row[f"{endpoint}_updated"])
    merged_dmtr[endpoint] = values

merged_dmtr = merged_dmtr.drop(columns=[f"{p}_updated" for p in endpoints])

merged_dmtr.to_csv(
    "V:\Medische-oncologie\OncologieOnderzoek\Melanoom\PREMIUM\premium_selection\data\dmtr.csv"
)
