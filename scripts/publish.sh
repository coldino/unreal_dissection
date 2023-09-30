#!/bin.bash
# Publish a new version of the package

set -e

# Check if there are any uncommitted changes
if [[ $(git status --porcelain) ]]; then
    read -p "🔴 There are uncommitted changes.\nAre you sure you wish to release? [y/N] " confirm
    if [[ $confirm != "y" ]]; then
        echo "Aborting"
        exit 1
    fi
fi

# Ask which bump type or version to use
NJOBS=4
echo "Version options:"
bump_options=(major minor patch premajor preminor prepatch prerelease)
for bump in ${bump_options[@]}
do
    echo "  [$bump] $(poetry version --dry-run -s -- $bump)" &
    if [[ $(jobs -r -p | wc -l) -ge $NJOBS ]]; then wait -n; fi
done
wait
read -p "Select bump type or enter new version string: " version_type

# Confirm the version
new_version=$(poetry version --dry-run -s -- "$version_type")
read -p "Are you sure you want to continue and publish $new_version? [y/N] " confirm
if [[ $confirm != "y" ]]; then
    echo "Aborting"
    exit 1
fi

echo "STOP"
exit 1

read -p "Press enter to continue"

# Bump the version
poetry version -- "$version_type"

# Update requirements.txt
poetry export --format requirements.txt --output requirements.txt --without-hashes

# Commit and tag the new version
git add requirements.txt pyproject.toml
git commit -m "Bump version to $new_version"
git tag v$(new_version)

# Build and publish the package (includes version/hash)
poetry build

# Publish the package to PyPI
poetry publish --repository testpypi

# Push the new version to GitHub
git push --follow-tags
