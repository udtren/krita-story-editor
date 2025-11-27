"""Handler for save_all_opened_docs action"""

import json
from krita import Krita


def handle_save_all_opened_docs(client, request, docker_instance):
    """Handle saving all opened documents"""
    try:
        opened_docs = Krita.instance().documents()
        for doc in opened_docs:
            doc.save()
        response = {
            "success": True,
            "response_type": "save_all_opened_docs",
            "result": "All opened documents saved.",
        }
        client.write(json.dumps(response).encode("utf-8"))
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))
