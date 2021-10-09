# Engineering Guideline

## Environment

Before you start to code, make sure you have create an isolated environment with `virtualenv`, `py-env` or `conda`.

Here, use conda as an example:

``` sh
# create env
conda create -n <your_env_name>

# active env
conda activate <your_env_name>

# after you have activate your env, install package with
conda install <pkg_name> 
# or: pip install <pkg_name>
```

## Git

To write code in parallel, **DO NOT** push to the `master` branch directly. The workflow of this repo should be:

1. check out a new branch
2. commit changes to the new branch
3. create a PR (pull request)
4. ask other members to review to PR and confirm merge commit

Example of creating a new branch:

``` sh
# if your shell does not show your branch directly, use
git branch
# to check out which branch your are working on

# create a new branch and checkout to it
git checkout -b <your_branch_name>
# then, you shall be in the new branch
```

## Code

Rememter to write annotations for your code. To document use [Google style](https://google.github.io/styleguide/pyguide.html) docstring.
