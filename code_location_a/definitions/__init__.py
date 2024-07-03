from dagster import Definitions, asset, AssetExecutionContext
import requests

@asset
def foo(context: AssetExecutionContext):
    context.log.info(f"Requests version: {requests.__version__}")
    return 1

all_definitions = Definitions(assets=[foo])