# premium_selection
DMTR preprocessing and patient selection tool for PREMIUM project. 

### Step 0. Setting up the repository
0.1 Clone the repository

```
git clone https://github.com/RensterMaat/premium_selection.git
cd premium_selection
```

0.2 Setup your conda environment and install dependencies
```
conda create -n premium_selection python
pip install -r requirements.txt
```

### Step 1. Preparing input data
1.1 Place all the raw dmtr files into a single folder. All DMTR files should be .xlsx files, and should have a single sheet with all columns of the file. 

1.2 Fill in config/config_template.yaml. At this step, you will need to specify the following:
- input_folder: folder containing the raw DMTR files (step 1.1)
- intermediate_output_folder: output folder of the first script. This will contain the files that will be used in step 3.
- names: raw dmtr files typically have a long and convulaed name. 


