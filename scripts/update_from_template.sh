# The purpose of this script is to update the current repo to a given tag in the template repo by creating patches and then 
# We hardcode the template because it is the thing to do here
if [ -z $1 ]; 
    then echo "neither tag, nor repository is set";
    exit
fi

if [ -z $2 ];
    then echo "defaulting to the main repository";
    main_repo="https://github.com/TRI-MAC/cdk-web-app-template.git";
    selected_tag=$1;
else
    main_repo=$1;
    selected_tag=$2;
fi

echo "Copying Configuration files"
cp -rv config config-backup

echo "Fetching from $main_repo"
git remote add upstream $main_repo
git fetch upstream --tag
git checkout -b merge-template-tag-$selected_tag

echo "Generating patch file"
mkdir patches
echo "Changing only .github, CDK and scripts directories" 
git diff merge-template-tag-$selected_tag $selected_tag -- \
    cdk/. \
    .devcontainer/. \
    .github/. \
    scripts/. \
    config/. \
    docker-compose.dev.yaml \
    docker-compose.yaml \
    GitVersion.yml \
    sample-services/. \
    README.md > patches/patch-$selected_tag



echo "Applying patch"
git apply --reject --whitespace=fix patches/patch-$1
echo "Template_Location: $main_repo" > template_version.yaml
echo "Template_Version: $selected_tag" >> template_version.yaml

echo "Cleaning up"
git remote remove upstream
git fetch --prune --prune-tags
echo "Please go through the template changes and pick the ones you wish to apply (especisl)"
echo "When you are done, you can remove the config-backup directory"