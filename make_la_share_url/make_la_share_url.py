import gzip
import base64
import datetime
import azure.functions as func
import json


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def make_share_url(query:str='', subscription_id:str='', resource_group:str='', workspace_name:str='', timespan:str='', set_query_now:bool=False):
   
    errors = []
    if not query:
        errors.append("Query must be supplied")
    
    if not subscription_id:
        errors.append("Subscription ID empty")
    
    if not resource_group:
        errors.append("Resource group empty")
        
    if not workspace_name:
        errors.append("Workspace name empty")
    
    if errors:
        return 1, ";".join(errors)
   
    # timespan sample: '2025-01-14T16%3A09%3A25.000Z%2F2025-01-14T16%3A09%3A26.475Z' or 'P7D'
    if set_query_now:
        now=datetime.datetime.now().isoformat()
        query = f"set query_now = datetime({now});\n{query}"

    # compress using gzip
    q_utf8=query.encode('utf-8')
    compressed_value = gzip.compress(bytes(q_utf8))

    # encode into base64 and get a return string
    encoded=base64.b64encode(bytes(compressed_value))
    encoded=encoded.decode("ascii")
    
    # sanitize for HTTP
    encoded = encoded.replace("/", "%2F")
    encoded = encoded.replace("+", "%2B")
    encoded = encoded.replace("=", "%3D")
    
    # build up URL
    base_url = (f"https://portal.azure.com/#view/Microsoft_OperationsManagementSuite_Workspace/Logs.ReactView/"
         f"resourceId/%2Fsubscriptions%2F{subscription_id}"
         f"%2FresourceGroups%2F{resource_group}%2F"
         f"providers%2FMicrosoft.OperationalInsights%2F"
         f"workspaces%2F{workspace_name}/source/LogsBlade.AnalyticsShareLinkToQuery/"
         f"q/{encoded}")
    
    if timespan:
        base_url + f"/timespan/{timespan}"
    
    return 0, base_url




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
        resp['share_url'] = resp
        
    return func.HttpResponse(
        json.dumps(resp),
        status_code=http_status
        )