from dagster import Definitions, asset, AssetExecutionContext
import requests

@asset
def bar(context: AssetExecutionContext):
    context.log.info(f"Requests version: {requests.__version__}")
    return 2

all_definitions = Definitions(assets=[bar])