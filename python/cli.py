import click

@click.group()
def cli():
    pass


# TODO: compelete the following function for data collection
@click.command()
def data_collection():
    pass


cli.add_command(data_collection, 'data')
