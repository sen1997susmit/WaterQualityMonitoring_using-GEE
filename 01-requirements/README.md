# Instruction for required environment and package
Though it is possible to recreate the environment from the .yml file by running

`conda env create -f environment.yml`

or

`pip install -r environment.txt`

 and then `conda activate smb`
 
 we've found that  creating an environment in this way can fail. 
 
 What follows are the steps to create the environment from scratch. This process allows for flexibility to upgrade to newer versions of the packages. New packages run the risk of breaking functionality but we find those issues are easier to overcome than having no environment at all. 

If you'd like to delete an environment, you can run `conda env remove  -n smb`

 `conda create -n smb python=3.11`
 `conda activate smb`
 `conda install numpy` 
`conda install matplotlib`
`conda install pandas`
`conda install geopandas`or
`conda install --channel conda-forge geopandas`
or `pip install geopandas` 

`conda install -c anaconda scikit-learn`
`pip install rasterio=1.3.6`

`conda install ipykernel`

 `python -m ipykernel install --user --name smb --display-name "smb"`

`pip install notebook`


`conda update jupyter` This might be optional dependig on which version conda has in its repository

`conda install seaborn -c conda-forge1`
or `pip install seaborn`
or `conda install seaborn` 

`conda install -c conda-forge earthengine-api`

`conda install -c conda-forge google-cloud-sdk` This worked on the server but wouldn't run on my local though it has in the past. Earth Engine and geemap still worked fine afterwards.

`pip install geemap`

`pip install nbconvert`

conda install -c conda-forge ipyleaflet

# Export/Update Current Environment

**Using conda:**

You can export your conda environment to a .yml file using the following command:
`conda env export > environment.yml`
This command creates a file named environment.yml which contains a list of all packages in the current environment including the Python version.

**Using pip:**

You can generate a .txt file with all the installed packages in your current environment using the following command:
`pip freeze > requirements.txt`
This command creates a requirements.txt file, which contains a list of all Python libraries installed in the current environment.