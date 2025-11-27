"""Handlers for document lifecycle actions (open, close, activate)"""

import os
import json
from krita import *
from ..utils import krita_file_name_safe
from ..handlers.get_data_handler import get_latest_all_docs_svg_data


def handle_activate_document(client, request, docker_instance):
    """Handle activating an already-opened document"""
    try:
        doc_name = request.get("doc_name", "")
        opened_docs = Krita.instance().documents()
        target_doc = None
        for doc in opened_docs:
            if krita_file_name_safe(doc) == doc_name:
                target_doc = doc
                break
        if target_doc:
            Krita.instance().setActiveDocument(target_doc)
            Application.activeWindow().addView(target_doc)
            response = {
                "success": True,
                "response_type": "activate_document",
                "result": f"Document '{doc_name}' activated.",
            }
        else:
            response = {
                "success": False,
                "response_type": "activate_document",
                "error": f"Document '{doc_name}' not found among opened documents.",
            }
        client.write(json.dumps(response).encode("utf-8"))
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))


def handle_open_document(client, request, docker_instance):
    """Handle opening a document from file path"""
    try:
        doc_path = request.get("doc_path", "")
        if os.path.exists(doc_path):
            opened_doc = Krita.instance().openDocument(doc_path)
            if opened_doc:
                Krita.instance().setActiveDocument(opened_doc)
                Application.activeWindow().addView(opened_doc)
            get_latest_all_docs_svg_data(
                client,
                docker_instance,
                "open_document",
                f"Document '{doc_path}' opened.",
            )
        else:
            response = {
                "success": False,
                "response_type": "open_document",
                "error": f"File '{doc_path}' does not exist.",
            }
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))


def handle_close_document(client, request, docker_instance):
    """Handle closing an opened document"""
    try:
        doc_name = request.get("doc_name", "")
        opened_docs = Krita.instance().documents()
        target_doc = None
        for doc in opened_docs:
            if krita_file_name_safe(doc) == doc_name:
                target_doc = doc
                break
        if target_doc:
            target_doc.close()
            get_latest_all_docs_svg_data(
                client,
                docker_instance,
                "close_document",
                f"Document '{doc_name}' closed.",
            )
        else:
            response = {
                "success": False,
                "response_type": "close_document",
                "error": f"Document '{doc_name}' not found among opened documents.",
            }
    except Exception as e:
        response = {"success": False, "error": str(e)}
