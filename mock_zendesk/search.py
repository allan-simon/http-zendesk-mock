from typing import Dict
from copy import deepcopy


def handle_search(tickets_store: Dict, query_params: Dict):

    print(query_params)
    results = []

    for ticket in tickets_store.values():
        external_id = query_params.get("external_id")
        if external_id is not None:
            if ticket.get("external_id") == external_id:
                ticket_copy = deepcopy(ticket)
                ticket_copy["result_type"] = "ticket"
                results.append(ticket_copy)

    return {
        "results": results,
        "facets": None,
        "next_page": None,
        "prev_page": None,
        "count": len(results),
    }
