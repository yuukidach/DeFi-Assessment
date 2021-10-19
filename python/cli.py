from typing import DefaultDict
import click
from pathlib import Path
from data_collection.smart_contract import create_contract_datasets

@click.group()
def cli():
    pass


# TODO: compelete the following function for data collection
@click.command()
@click.option('-f', '--force', is_flag=True, help='Force to collect data')
@click.option('--contract/--no-contract', default=True, 
               help='Collect data of smart contracts.')
@click.option('-c', '--csv', type=click.Path(exists=True), 
               default=Path(__file__).resolve().parents[1] / 'docs/platforms.csv',
               help='Location of platforms.csv.')
@click.option('-s', '--sdir', type=click.Path(),
               default=Path(__file__).resolve().parents[1] / 'data/',
               help='Directory to put collected data')
def data_collection(force, contract, csv, sdir):
    if contract:
        create_contract_datasets(csv, sdir, force)


cli.add_command(data_collection, 'data')

if __name__ == '__main__':
    cli()
