import click
from pathlib import Path
from data_collection.contract import create_contract_datasets
from data_collection.finance import create_finance_datasets
from preprocess.contract import pre_process
from modelling import contract, finance


@click.group()
def cli():
    pass


@click.command()
@click.option('-f', '--force', is_flag=True, help='Force to collect data')
@click.option('--contract/--no-contract', default=True, 
               help='Collect data of smart contracts.')
@click.option('--finance/--no-finance', default=True, 
              help='Collect data of finanacial risks.')
@click.option('-c', '--csv', type=click.Path(exists=True), 
               default=Path(__file__).resolve().parents[1] / 'docs/platforms.csv',
               help='Location of platforms.csv.')
@click.option('-t', '--target', type=click.Path(),
               default=Path(__file__).resolve().parents[1] / 'data/',
               help='Target directory to put collected data')
def data_collection(force, contract, finance, csv, target):
    if contract:
        tgt_folder = target/'contract'
        create_contract_datasets(csv, tgt_folder, force)
    if finance:
        create_finance_datasets(target, force)
        

@click.command()
@click.option('-f', '--force', is_flag=True, help='Force to collect data')
@click.option('-s', '--source', type=click.Path(exists=True),
               default=Path(__file__).resolve().parents[1] / 'data/contract',
               help='Directory of collected data')
@click.option('-t', '--target', type=click.Path(), 
               default=Path(__file__).resolve().parents[1] / 'data/contract/final.csv',
               help='Location to put newly created csv file.')
def data_process(force, source, target):
    source = Path(source)
    target = Path(target)
    if target.exists() and not force:
        return
    df = pre_process(source)
    df.to_csv(target, index=False)
    

@click.command()
@click.option('-s', '--source', type=click.Path(exists=True),
               default=Path(__file__).resolve().parents[1] / 'data/',
               help='Path of processed data.')
@click.option('-t', '--target', type=click.Path(), 
               default=Path(__file__).resolve().parents[1] / 'models/',
               help='Location to save the model.')
def train_model(source, target):
    source = Path(source)
    target = Path(target)
    contract.train(source / 'contract/final.csv', target)
    finance.train(source, target)
    

cli.add_command(data_collection, 'data')
cli.add_command(data_process, 'process')
cli.add_command(train_model, 'train')


if __name__ == '__main__':
    cli()