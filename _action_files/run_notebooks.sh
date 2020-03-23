#!/bin/sh
set -e
cd $(dirname "$0")/..
cd _notebooks/

ERRORS=""

for file in *.ipynb
do
    if papermill --kernel python3 "${file}" "${file}"; then
        echo "Sucessfully refreshed ${file}"
        git add "${file}"
    else
        echo "ERROR Refreshing ${file}"
        ERRORS="${ERRORS}\n${file}"
    fi
done

# Emit Errors If Exists So Downstream Task Can Open An Issue
if [ -z "$ERRORS" ]
then
    echo "::set-output name=error_bool::true"
    echo "::set-output name=error_str::${ERRORS}"
else
    echo "::set-output name=error_bool::false"
fi
