import pandas as pd
import argparse
import numpy as np
import yaml
from pathlib import Path
import datetime
import warnings

warnings.filterwarnings("ignore")


def select(dataset):
    # find patients+episode treated with anti-pd1 or combination therapy, but exclude episodes with prior treatment
    grouped = dataset.groupby(["upn", "episodevolgnr"], sort=True).typsyth1.apply(list)

    included_patients = []
    pretreated = []
    excluded_because_of_pretreatment = []

    for (upn, episode), row in zip(grouped.index, grouped):
        if any([th in [5, 6] for th in row]):
            if not upn in pretreated:
                included_patients.append((upn, episode))
            else:
                if upn not in excluded_because_of_pretreatment:
                    excluded_because_of_pretreatment.append(upn)
        if any([th in [2, 3, 4, 5, 6, 7, 10] for th in row]):
            pretreated.append(upn)

    print(
        "Patients treated with anti-PD1/combination therapy: {}".format(
            len(excluded_because_of_pretreatment) + len(included_patients)
        )
    )
    print("Not treatment-naive: {}".format(len(excluded_because_of_pretreatment)))

    selected = dataset[
        dataset[["upn", "episodevolgnr"]].apply(tuple, axis=1).isin(included_patients)
    ]

    # exclude patients with ocular or mucosal melanoma
    before = len(pd.unique(selected["upn"]))
    selected = selected[~selected["ptloc"].isin([1, 6])]
    after = len(pd.unique(selected["upn"]))
    print("With ocular or mucosal melanoma: {}".format(before - after))

    # exclude patients with start date before 1-1-2016
    before = len(pd.unique(selected["upn"]))
    selected["start_date"] = selected[["startpd", "startipnicomb", "startandst"]].min(
        axis=1
    )
    selected = selected.loc[~(selected["start_date"] < np.datetime64("2016-01-01"))]
    after = len(pd.unique(selected["upn"]))

    print("Treated before 1-1-2016: {}".format(before - after))

    # # exclude patients with sysadj
    before = len(pd.unique(selected["upn"]))
    selected = selected[selected["sysadj"].isnull()]
    after = len(pd.unique(selected["upn"]))
    print("Treated in (neo-)adjuvant setting: {}".format(before - after))

    print("Remaining: {}".format(after))
    return selected


def select_possible(dataset):
    grouped = dataset.groupby(["upn", "episodevolgnr"], sort=True).typsyth1.apply(list)

    included_patients = []
    pretreated = []

    for (upn, episode), row in zip(grouped.index, grouped):
        if any([th in [7] for th in row]) and not upn in pretreated:
            included_patients.append((upn, episode))
        if any([th in [2, 3, 4, 5, 6, 10] for th in row]):
            pretreated.append(upn)

    possible = dataset[
        dataset[["upn", "episodevolgnr"]].apply(tuple, axis=1).isin(included_patients)
    ]

    # exclude patients with start date before 1-1-2016
    possible["start_date"] = possible[["startpd", "startipnicomb", "startandst"]].min(
        axis=1
    )
    possible = possible.loc[~(possible["start_date"] < np.datetime64("2016-01-01"))]

    # exclude patients with sysadj
    possible = possible[possible["sysadj"].isnull()]

    return possible


def determine_benefit(patient):
    if pd.isna(patient.start_date):
        return float("nan")
    try:
        relative_time = [
            (fu[0], fu[1] - np.datetime64(patient.start_date))
            for fu in patient.followup
        ]
    except:
        return float("nan")

    # if there was response at any time, there is clinical benefit
    if any(
        [
            moment[0]
            in [
                6,
                8,
            ]
            for moment in relative_time
        ]
    ):
        return 1

    # stable disease at 24 weeks counts as clinical benefit
    late_assessments = [
        moment
        for moment in relative_time
        if moment[1] >= datetime.timedelta(days=7 * 24)
    ]

    if late_assessments:
        first_assessment_after_24weeks = sorted(late_assessments, key=lambda x: x[1])[
            0
        ][0]
        # if the first assessment after 24 weeks showed response, there is benefit
        if first_assessment_after_24weeks in [2, 3]:
            return 1
        # otherwise, there has to be progression and there is no benefit
        else:
            return 0
    else:
        # if followup is less than 24 weeks...
        if 5 in [x[0] for x in patient.followup] and patient.doodoorz not in [
            2,
            3,
            7,
        ]:  # and the patient died, but not of something else
            return 0
        elif 4 in [x[0] for x in patient.followup]:  # or if the patient progressed
            return 0
        else:
            return float("nan")

    # if there was progressive disease at any time in other cases, there is no clinical benefit
    # if any([moment[0] in [4,5] for moment in relative_time]):
    #     return 0

    return "error"


def determine_response(patient):
    if pd.isna(patient.start_date):
        return float("nan")
    try:
        relative_time = [
            (fu[0], fu[1] - np.datetime64(patient.start_date))
            for fu in patient.followup
        ]
    except:
        return float("nan")

    # if there was response at any time, there is response
    if any([moment[0] in [1, 6, 8] for moment in relative_time]):
        return 1

    # stable disease at 24 weeks counts as clinical benefit
    late_assessments = [
        moment
        for moment in relative_time
        if moment[1] >= datetime.timedelta(days=7 * 24)
    ]

    if late_assessments:
        # if followup is more than 24 weeks...
        # ... the patient did not achieve response (as per condition above and thus 0)
        return 0
    else:
        # if followup is less than 24 weeks...
        if 5 in [x[0] for x in patient.followup] and patient.doodoorz not in [
            2,
            3,
            7,
        ]:  # and the patient died, but not of something else
            return 0
        elif 4 in [x[0] for x in patient.followup]:  # or if the patient progressed
            return 0
        else:
            return float("nan")

    # if there was progressive disease at any time in other cases, there is no clinical benefit
    # if any([moment[0] in [4,5] for moment in relative_time]):
    #     return 0

    return "error"


def find_baseline_entry(dataset):
    # take the first entry in the episode
    starting_dates = (
        # dataset[~dataset["datlcont"].isna()].groupby("upn").datlcont.apply(min)
        dataset.groupby("upn").datlcont.apply(min)
    )
    upn_vs_start = list(zip(starting_dates.index, starting_dates))
    baseline = dataset[
        dataset[["upn", "datlcont"]].apply(tuple, axis=1).isin(upn_vs_start)
    ]

    baseline = baseline.groupby("upn").first()

    # add all followup to the baseline entry
    grouped = dataset.groupby(["upn", "episodevolgnr"])[
        ["statlcont", "datlcont"]
    ].apply(lambda x: list(zip(list(x["statlcont"]), list(x["datlcont"]))))

    followup = []
    for _, row in baseline.reset_index().iterrows():
        try:
            fu = grouped.loc[(row["upn"], row["episodevolgnr"])]
            followup.append(fu)
        except:
            followup.append([])

    baseline["followup"] = followup

    # determine durable clinical benefit
    benefits = []
    for _, row in baseline[["id", "start_date", "followup", "doodoorz"]].iterrows():
        benefits.append(determine_benefit(row))
    baseline["dcb"] = benefits

    # determine response
    responses = []
    for _, row in baseline[["id", "start_date", "followup", "doodoorz"]].iterrows():
        responses.append(determine_response(row))
    baseline["orr"] = responses

    return baseline


def preprocess(baseline, selected, dataset):
    stages = []
    for upn, row in baseline.iterrows():
        if row["locafmethersen"] == 1:
            stages.append("M1d")
        elif any(
            row[["locafmetlever", "locafmetdarm", "locafmetbot", "locafmetand"]] == 1
        ):
            stages.append("M1c")
        elif row["locafmetlong"] == 1:
            stages.append("M1b")
        elif any(row[["locafmetlklier", "locafmetcutis"]] == 1):
            stages.append("M1a")
        elif row["lokrec"] == 1:
            stages.append("IIIC")
        else:
            stages.append(float("nan"))
    baseline["stage"] = stages

    baseline["Best overall response"] = [float("nan")] * len(baseline)

    responses_data = selected.groupby("upn").statlcont.apply(list)
    for upn, responses in zip(responses_data.index, responses_data):
        if any([r in [1, 8] for r in responses]):
            bor = "Complete response"  # CR
        elif 6 in responses:
            bor = "Partial response"  # PR
        elif any([r in [2, 3] for r in responses]):
            bor = "Stable disease"  # SD
        elif (
            4 in responses
            or 1 in selected.groupby("upn")["doodoorz"].apply(list).loc[upn]
        ):  # also if cause of death is melanoma
            bor = "Progressive disease"  # PD
        elif 5 in responses:
            bor = "Death"  # Dead
        elif 7 in responses:
            bor = "Lost to follow up"  # LTFU
        else:
            bor = float("nan")
        baseline.loc[upn, "Best overall response"] = bor

    # find last date of followup
    last_contact = dataset[~dataset["datlcont"].isna()].groupby("upn").datlcont.max()
    baseline["last_contact"] = pd.to_datetime(
        last_contact[last_contact.index.isin(baseline.index)]
    )

    # end of followup is the latter of moment of death or last contact
    baseline["end_of_fu"] = baseline[["last_contact", "datovl"]].max(axis=1)

    # calculate duration of followup
    baseline["fu_OS"] = baseline["end_of_fu"] - baseline["start_date"]

    # for OS, event is defined as death
    baseline["event_OS"] = ~baseline["datovl"].isnull()

    # for PFS, event is defined as moment of progression or death
    progressed = []
    for upn, followup in selected.groupby("upn").statlcont.apply(list).items():
        if any([fu in [4, 5] for fu in followup]):
            progressed.append(True)
        else:
            progressed.append(False)
    baseline["event_PFS"] = baseline["event_OS"] | progressed

    # duration of followup is lesser of time to progression or time to death
    baseline["date_of_progression"] = (
        selected[selected["statlcont"].isin([4, 5])].groupby("upn")["datlcont"].min()
    )
    baseline["time_to_progression"] = (
        baseline["date_of_progression"] - baseline["start_date"]
    )
    baseline["fu_PFS"] = baseline[["time_to_progression", "fu_OS"]].min(axis=1)

    # format column names and variable names
    baseline = baseline.rename(
        columns={
            "geslacht": "Sex",
            "who": "WHO",
            "stagepet": "Type of scan",
            "labdlhd": "LDH",
            "stage": "Stage",
            "typsyth1": "Therapy",
        }
    )

    baseline = baseline.replace(
        {
            "Sex": {1: "Male", 2: "Female"},
            "WHO": {9: float("nan")},
            "Type of scan": {0: "CT", 1: "PET-CT"},
            "LDH": {0: float("nan"), 1: "Normal", 2: "Elevated", 9: float("nan")},
            "Therapy": {5: "Anti-PD1", 6: "Ipilimumab & Nivolumab", 7: float("nan")},
        }
    )

    # add age
    if "gebdat" in baseline.columns:
        baseline["gebjaar"] = baseline["gebdat"].astype("datetime64[ns]").dt.year
    baseline["Age"] = (
        baseline["start_date"].astype("datetime64[ns]").dt.year - baseline["gebjaar"]
    )

    return baseline


parser = argparse.ArgumentParser()
parser.add_argument("config_name")

if __name__ == "__main__":
    args = parser.parse_args()

    with open(f"../config/{args.config_name}") as f:
        config = yaml.safe_load(f)

    for dataset_fp in Path(config["input_folder"]).iterdir():
        dataset = pd.read_excel(dataset_fp)

        print("#" * 100)
        print("Processing dataset {} ...".format(dataset_fp.name))
        name = config["names"][dataset_fp.name]

        dataset["upn"] = dataset["upn"].astype(str)

        selected = select(dataset)
        baseline = find_baseline_entry(selected)
        baseline = preprocess(baseline, selected, dataset)
        baseline.to_csv(Path(config["intermediate_output_folder"]) / (name + ".csv"))

        possible = select_possible(dataset)
        possible_baseline = find_baseline_entry(possible)
        possible_baseline = preprocess(possible_baseline, possible, dataset)
        possible_baseline.to_csv(
            Path(config["intermediate_output_folder"]) / (name + "_possible.csv")
        )
