# rtg-automotive

Start up:

python -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt

Bash:

bash src/bash/docker.sh {example-lambda-function-name}

Checks:

pre-commit run --all-files

mypy {path_to_file_or_directory} --explicit-package-bases

TO DO:

********

Log of files that are being downloaded (Zip folders for daily ebay uploads)

RTG shop - 3 tabs for each Excel download. One for each prefix eg. UKF, UKD, etc.

Get API ID programmatically, add to AWS utils.

Create mechanism for reducing size of tables.

Clean up code and write any modules/utils that I can re-use for other projects.
