# premium_selection
DMTR preprocessing and patient selection tool for PREMIUM project. 

## Overview

## Usage
### Step 0. Setting up the repository
0.1 Clone the repository

```
git clone https://github.com/RensterMaat/premium_selection.git
cd premium_selection
```

0.2 Setup your conda environment and install dependencies
```
conda create -n premium_selection python
conda activate premium_selection
pip install -r requirements.txt
```

### Step 1. Preparing input data
1.1 Place all the raw dmtr files into a single folder. All DMTR files should be .xlsx files, and should have a single sheet with all columns of the file. 

1.2 Fill in config/config_template.yaml. At this step, you will need to specify the following:
- input_folder: folder containing the raw DMTR files (step 1.1)
- intermediate_output_folder: output folder of the first script. This will contain the files that will be used in step 3.
- names: raw dmtr files typically have a long and convoluted name. Specify how every raw input file should be renamed. For example:

```
names:
    "long_convoluted_name_of_center_A.xlsx": "center_A"
    "another_long_name_for_center_B.xlsx": "center_B"
```

### Step 2. Preprocess
Run the following command, with the filename of the config you created under 1.2 as an argument:

```
python src/01_preprocess.py config_template.yaml
```

### Step 3. Select which patients to add
Step 2 resulted in 2 .csv-files per center in the intermediate_output_folder: one called <center_name>.csv and one called <center_name>_possible.csv. The first contains patients which should definitely be included. The second contains patients who received 'other' therapy, but who otherwise satisfy all inclusion criteria. You will need to manually check if the therapy that they received falls inside the inclusion criteria. The information you need to determine this is in the column "typandst". 

Add the ids of the patients (column "upn") that should be included to the config_file under "include_with_other_therapy" like so:

```
include_with_other_therapy:
  "center_A.csv": [patient_id1, patient_id2, patient_id3, patient_id4]
  "center_B.csv": []
  "center_C.csv": [patient_id5, patient_id6]
```

### Step 4. Prepare for anonymization
4.1 Create a .csv-file with two columns: "upn" and "premium_id". This file should contain a row for every patient which does not yet have a study id:

```
upn,premium_id
12345678,PREM_AB_001
```

4.2 Add the path of the coding csv file created under 4.1 to the config:

```
upn_to_study_coding: /path/to/coding_file.csv

```

4.3 Specify which centers are already encoded:

```
already_encoded: ["center_A.csv", "center_B.csv"]
```

4.4 Specify the path to the final output file:
```
output_file: /path/to/output_file.csv
```

### Step 5. Run anonymization
Run the following command, with the filename of the config you created under 1.2 as an argument:

```
python src/02_anonymize.py config_template.yaml
```

