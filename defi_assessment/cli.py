import click
from pathlib import Path
from defi_assessment.data_collection.contract import create_contract_datasets
from defi_assessment.data_collection.finance import create_finance_datasets
from defi_assessment.preprocess.contract import pre_process
from defi_assessment.modelling import contract
from defi_assessment import __version__


@click.group()
@click.version_option(__version__)
def cli():
    pass


@click.command()
@click.option('-i', '--inc', is_flag=True,
              help='Collect data in incremental mode.')
@click.option('--contract/--no-contract', default=True,
              help='Collect data of smart contracts.')
@click.option('--finance/--no-finance', default=True,
              help='Collect data of finanacial risks.')
@click.option('-s', '--source', type=click.Path(exists=True),
              default=Path.cwd() / 'docs/platforms.csv',
              help='Location of platforms.csv.')
@click.option('-t', '--target', type=click.Path(),
              default=Path.cwd() / 'data/',
              help='Target directory to put collected data')
def data_collection(inc, contract, finance, source, target):
    """Collect raw data.

    Collect data for smart contract risks and financial risks. Three folders
    will be create: `contract/`, `social/` and `token_value`. The raw data in
    `contract` folder need to be further processed with `process` subcommand.
    """
    target = Path(target)
    if contract:
        tgt_folder = target/'contract'
        create_contract_datasets(source, tgt_folder, inc)
    if finance:
        create_finance_datasets(target, inc)


@click.command()
@click.option('-f', '--force', is_flag=True,
              help='Force to reproduce processed data')
@click.option('-s', '--source', type=click.Path(exists=True),
              default=Path.cwd() / 'data/contract',
              help='Directory of collected data')
@click.option('-t', '--target', type=click.Path(),
              default=(Path.cwd() / 'data/contract/contract_overview.csv'),
              help='Location to put newly created csv file.')
def data_process(force, source, target):
    """Process the data related to smart contracts.
    """
    target = Path(target)
    if target.exists() and not force:
        return
    df = pre_process(source)
    df.to_csv(target, index=False)


@click.command()
@click.option('-s', '--source', type=click.Path(exists=True),
              default=Path.cwd() / 'data/',
              help='Path of processed data.')
@click.option('-t', '--target', type=click.Path(),
              default=Path.cwd() / 'models/',
              help='Location to save the model.')
def train_model(source, target):
    """Train models.

    A Random Forest model for smart contract and a LSTM model for financial
    risks.
    """
    from defi_assessment.modelling import finance
    source = Path(source)
    target = Path(target)
    contract.train(source / 'contract/contract_overview.csv', target)
    finance.train(source, target)


@click.command()
@click.option('-p', '--port', default=8080, help='Port of the web server')
def build_web(port):
    """Create a simple local website to view the result.
    """
    from defi_assessment.run import app
    app.run(port=port, debug=False)


cli.add_command(data_collection, 'data')
cli.add_command(data_process, 'process')
cli.add_command(train_model, 'train')
cli.add_command(build_web, 'web')


if __name__ == '__main__':
    cli()
