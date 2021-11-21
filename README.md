# DeFi Assessement (dass)

![](https://img.shields.io/github/license/yuukidach/DeFi-Assessment)

A prototype project to perform risk assessment on different DeFi lending platforms.

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [DeFi Assessement (dass)](#defi-assessement-dass)
  - [Overview](#overview)
    - [Web Page](#web-page)
    - [Command-line Tool](#command-line-tool)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Data collection](#data-collection)
    - [Data process](#data-process)
    - [Model Training](#model-training)
    - [Web Application](#web-application)
  - [Contributors](#contributors)

<!-- /code_chunk_output -->

## Overview

### Web Page

![](./docs/res/index.png)

### Command-line Tool

![](./docs/res/data_collection.png)

## Installation

From local repository:

```shell
pip3 install .[cpu]  # for tensorflow with cpu only
pip3 install .[gpu]  # for tensorflow-gpu
```

From PyPI:

```shell
pip3 install DeFi-Assessment[cpu]
pip3 install DeFi-Assessment[gpu]
```

## Usage

This project is packed into a command-line tool with 4 subcommand:

```shell
Usage: dass [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help  Show this message and exit.

Commands:
  data     Collect raw data.
  process  Process the data related to smart contracts.
  train    Train models.
  web      Create a simple local website to view the result.
```

The workflow of the 4 commands should be:

```shell
data -> process -> train -> web
```

### Data collection

`data` command is used to collect data for training and assessment (prediction). All of the other three commands are dependent on it. Make sure to run this command at beginning.

To collect data for smart contracts, `docs/platforms.csv` shoud be used. This file provides the github repository link for different smart contracts. And it also provide intermediary status for corresponding platforms.

This command will **NOT** overwrite any existing data. Users can use `--inc` option to collect data in incremental mode, which means new records and new attributes will be collected. And old data still exists.

### Data process

`process` command is aimed to process raw data. Currently, only sart contract data need to be processed after collection.

### Model Training

`train` command is simple. It trains 2 models. A Random Forest model for smart contracts and a LSTM mdoel for financial risks.

### Web Application

`web` command builds a local web interface for users to directly view the result of assessement.

## Contributors

<a href="https://github.com/yuukidach/DeFi-Assessment/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yuukidach/DeFi-Assessment" />
</a>
