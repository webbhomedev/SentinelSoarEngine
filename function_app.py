"""
Base Python for an Azure Function which will manipulate provided data to generate a series
Queries should then be passed back to Sentinel

Two key pieces of information are required: the Sentinel incident and a specially crafted
job payload. 

As of writing, job payloads should look something like this and are fairly self explanatory
    SAMPLE_ENRICH_JOB_DETAILS = {
        "item-type": "SOAR-trigger",
        "entity-type": "Account",
        "query": 'SigninLogs | where UserPrincipalName == \"%ENTITY%\"',
        "additional_params": {"severity_change": {"results_count_mt": 1, "severity": "High"}},
    }

Sample JSON data is not provided, however, this can be taken directly from a logic app run (take the outputs
of Sentinel incident creation)
and then dumped in payload.json

"""

import json
import pprint as pp
import azure.functions as func
import logging
from make_la_share_url import make_share_url
from make_job import main_make_job

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)





## If we are in AZ
@app.function_name(name="MakeJob")
@app.route(route="MakeJob")
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        req_body = json.loads(req.get_body())
    except :
        return func.HttpResponse("Missing JSON payload", 500)

    sentinel_incident = req_body.get("sentinel_incident", {})
    enrichment_job = req_body.get("enrichment_job", {})

    resp, result_code  = main_make_job({ 'sentinel_incident':sentinel_incident, 'enrichment_job': enrichment_job } )

    return func.HttpResponse(
        json.dumps(resp),
        status_code=result_code
        )



@app.function_name(name="MakeLaShareUrl")
@app.route(route="MakeLaShareUrl")
def make_url(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = json.loads(req.get_body())
    except :
        return func.HttpResponse("Missing JSON payload", 500)
    
    query=req_body.get("query", '')
    subscription_id = req_body.get("subscription_id", '')
    resource_group = req_body.get("resource_group", '')
    workspace_name = req_body.get('workspace_name', '')
    timespan = req_body.get('timespan', '')
    set_query_now = req_body.get('set_query_now', False)
    
    resp_body = {
        'share_url':'',
        'errors':''    
    }

    exit_c, resp = make_share_url(query=query,
                                     subscription_id=subscription_id, 
                                     resource_group=resource_group,
                                     workspace_name=workspace_name,
                                     timespan=timespan, 
                                     set_query_now=set_query_now)
    # non-zero
    http_status = 200
    if exit_c:
        resp_body['errors'] = resp
        http_status = 500
    else:
        resp_body['share_url'] = resp
        
    return func.HttpResponse(
        json.dumps(resp_body),
        status_code=http_status
        )