import copy

def validateJobisJob(job) -> bool:
    """Checks to see if the specially crafted job is valid with a series of 'if' checks
    If the nob is not valid, a false is returned, along with a reason 

    Args:
        job (dict): the specially crafted job payload

    Returns:
        bool: pos 0, was the job successfully validated
        str: pos 2, any errors associated with the job. May be null
    """

    # check basic job params
    if job.get("item-type", None) != "SOAR-trigger":
        logging.error("Not of type SOAR-Trigger")
        return False, "Job type not SOAR trigger"
    if not job.get("entity-type", None):
        logging.error("No entity type specified")
        return False, "entity-type empty field"
    if not job.get("query", None):
        logging.error("Query field empty")
        return False, "invalid query"


    # check that if job severity is specified, required fields are there
    severity_change_params=job.get("additional_params", {}).get("severity_change", [])
    track_param_err=[]
    
    # for each param in list, check possible options by jey
    for param in severity_change_params:
        
        # results_count_mt validation
        if "results_count_mt" in param and not(int(param['results_count_mt'] > -1) ): # can only be zero. Also testing casting to int. If fails, will be caught in global catch/except
            track_param_err.append("Job Error: results_count_mt is not a number")
        if "results_count_mt" in param and param.get("severity", None) not in ["Low", "Medium", "High", "Informational"]:
            track_param_err.append('Job Error: Job included severity change but did not specify a Low/Medium/High/Informational')
                   
        
        if "entity_contains" in param and not param.get("entity_contains", None):
            track_param_err.append("Job Error: entity_contains requires string")
        if "entity_contains" in param and param.get("severity", None) not in ["Low", "Medium", "High", "Informational"]:
            track_param_err.append('Job Error: Job included severity change but did not specify a Low/Medium/High/Informational')

    
    # check contains comments param
    if job.get("additional_params", {}).get("commentOnIncidents", None):
        commentParam=job['additional_params']['commentOnIncidents']
        if commentParam not in [True, False]:
            track_param_err.append("commentOnIncidents is not true or false")
    
    
    # return error or true
    if not track_param_err:
        return True, ''
    else:
        return False, ",".join(track_param_err)
    

def returnEntities(payload) -> list:
    """A function which extracts a list of entities contained
    in the Sentinel Incident JSON

    Args:
        payload (dict): The Sentinel Incident JSON

    Returns:
        list: Entities, as formatted in the Sentinel JSON
    """
    return payload.get("object", {}).get("properties", {}).get("relatedEntities", [])

def manipulateEntityValues(entity, match_upn=True, full_netbios_name=False):
    """Will perform post manipulation on entities for enrichment. Add here for future
    adjustment.

    Args:
        entity (dict): an item from a list of Sentinel entities
    """

    if (
        match_upn
        and entity["kind"] == "Account"
        and entity.get("properties", {}).get("upnSuffix")
        and entity.get("properties", {}).get("accountName", None)
    ):
        return f"{entity['properties']['accountName']}@{entity['properties']['upnSuffix']}"
    else:
        return


def generateCustomEntitiesList(entities) -> list:
    """Generated a list of finalized entities. If the entity requires some 
    additional manipulation (see function manipulateEntityValues) then this value
    will be added in place
    

    Args:
        entities (list): A list of extracted entities from the Sentinel
        incidents

    Returns:
        list: a list finalised entities
    """
    
    custom_entities_list = []

    # take friendly name or another value from custom function
    for e in entities:
        entry = {}
        entry["kind"] = e["kind"]
        entry["entity_value"] = e.get("properties", {}).get("friendlyName", "")

        if manipulateEntityValues(e):
            entry["entity_value"] = manipulateEntityValues(e)

        custom_entities_list.append(entry)

    return custom_entities_list


def main_make_job(payload={}):
        
    # set default global configuration
    REWRITE_QUERIES = True
    POST_QUERY_RSLT_COMMENT = True
    RETURN_PAYLOAD = {
        "jobs": [],
        "distinct_entities": [],
        "friendly_entities": [],
        "customised_entities": [],
        "warnings": "",
        "errors": "",
        "status": "",
    }



    SENTINEL_INC_JSON = payload.get("sentinel_incident", {})
    ENRICH_JOB_DETAILS = payload.get("enrichment_job", {})

    ## Error processing
    http_error_code=None
    
    # nothing to enrich
    try:
        INC_ENTITIES = returnEntities(SENTINEL_INC_JSON)
        if not INC_ENTITIES:
            RETURN_PAYLOAD["warnings"] += "no entities in incident"
            RETURN_PAYLOAD["status"] += "1:see_warnings,"
            http_error_code = 202

        # check that the enrichment job is valid
        successful, job_errors = validateJobisJob(ENRICH_JOB_DETAILS)
        if not successful:
            RETURN_PAYLOAD["status"] += "2:see_errors,"
            RETURN_PAYLOAD["errors"] += job_errors
            http_error_code = 400
    except:
        RETURN_PAYLOAD["errors"] += "incorrect schema or malformed payload"
        http_error_code=418

    
    if http_error_code: 
        return RETURN_PAYLOAD, http_error_code

    ## End Error Processing

    # get useful debug value and configure our lists
    DISTINCT_ENTITY_TYPES = list(set([f"{x['kind'].lower()}" for x in INC_ENTITIES]))
    FRIENDLY_ENTITY_TYPES = [f"{x['properties']['friendlyName']}:{(x['kind']).lower()}" for x in INC_ENTITIES]
    MANIPULATED_ENTITIES = generateCustomEntitiesList(INC_ENTITIES)
    

    # set values in our payload
    RETURN_PAYLOAD["distinct_entities"] = DISTINCT_ENTITY_TYPES
    RETURN_PAYLOAD["friendly_entities"] = FRIENDLY_ENTITY_TYPES
    RETURN_PAYLOAD["customised_entities"] = MANIPULATED_ENTITIES


    if not ENRICH_JOB_DETAILS["entity-type"].lower() in DISTINCT_ENTITY_TYPES:
        RETURN_PAYLOAD["status"] = "0:job entity type not in sentinel incident"
        return RETURN_PAYLOAD, 202

    # work out which entities we need to run a query against by if they match the SOAR job
    # create a default empty list and add to it, replacing our placeholder %ENTITY% with the actual value
    # then add it to the return payload
    JOB_ENTITIES = []
    JOB_ENTITIES = [x for x in MANIPULATED_ENTITIES if x["kind"].lower() == ENRICH_JOB_DETAILS["entity-type"].lower()]
    
    # take copy  and add the query that should be run against it
    ENTITIES_WITH_JOBS = copy.deepcopy(JOB_ENTITIES)
    for job in ENTITIES_WITH_JOBS:
        job['query_to_run']=ENRICH_JOB_DETAILS.get("query").replace("%ENTITY%",job['entity_value'])
        
        


    RETURN_PAYLOAD["jobs"] = ENTITIES_WITH_JOBS

    # if we have made it this far without an early return, as
    RETURN_PAYLOAD["status"] = "0:ok"
    return RETURN_PAYLOAD, 200
