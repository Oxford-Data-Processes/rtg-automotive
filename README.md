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


Create a Lambda that sends files from a Dropbox location to the S3 bucket automatically.


THINGS TO TEST IN PRODUCTION:

Then test with small store and RTG. Then with all stores.

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
