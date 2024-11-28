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

RTG shop - 3 tabs for each Excel download. One for each prefix eg. UKF, UKD, etc.

Create mechanism for reducing size of tables. Write entire database into S3, then reduce supplier_stock table to keep only last 14 days of data. SQL query in a Python script that runs weekly.


THINGS TO TEST IN PRODUCTION:


Test initially with one small store.

Then test with store and RTG.




Backend:

- Get API
- Post API

Frontend:

- Stock Manager (RTG + other suppliers)
- eBay table generation
- Table Viewer
    - With and without splits
- Bulk Edit (append, delete, update)
    - With and without splits
- Add new supplier
- Add new ebay store
