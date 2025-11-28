"""Handlers for document operations (add from template, duplicate, delete)"""

import json
from ..utils import (
    add_new_document_from_template,
    duplicate_document,
    delete_document,
)
from ..handlers.get_data_handler import get_latest_all_docs_svg_data


def handle_add_from_template(client, request, docker_instance):
    """Handle creating a new document from a template"""
    try:
        target_doc_path = request.get("doc_path", "")
        template_path = request.get("template_path", "")
        config_filepath = request.get("config_filepath", None)
        result = add_new_document_from_template(
            target_doc_path, template_path, config_filepath
        )
        if result["success"]:
            new_filename = result.get("new_filename", "")
            get_latest_all_docs_svg_data(
                client,
                docker_instance,
                "add_from_template",
                f"{new_filename} created from template",
            )
        else:
            response = {
                "success": False,
                "response_type": "add_from_template",
                "error": result.get("error", "Unknown error"),
            }
            client.write(json.dumps(response).encode("utf-8"))
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))


def handle_duplicate_document(client, request, docker_instance):
    """Handle duplicating an existing document"""
    try:
        doc_name = request.get("doc_name", "")
        doc_path = request.get("doc_path", "")
        config_filepath = request.get("config_filepath", None)
        result = duplicate_document(doc_name, doc_path, config_filepath)
        new_filename = result.get("new_filename", "")
        if result["success"]:
            original_filename = result.get("original_filename", "")
            get_latest_all_docs_svg_data(
                client,
                docker_instance,
                "duplicate_document",
                f"{new_filename} created from {original_filename} by duplication",
            )
        else:
            response = {
                "success": False,
                "response_type": "duplicate_document",
                "error": result.get("error", "Unknown error"),
            }
            client.write(json.dumps(response).encode("utf-8"))
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))


def handle_delete_document(client, request, docker_instance):
    """Handle deleting a document"""
    try:
        doc_name = request.get("doc_name", "")
        doc_path = request.get("doc_path", "")
        config_filepath = request.get("config_filepath", None)
        result = delete_document(doc_name, doc_path, config_filepath)
        if result["success"]:
            deleted_filename = result.get("deleted_filename", "")
            get_latest_all_docs_svg_data(
                client,
                docker_instance,
                "delete_document",
                f"{deleted_filename} deleted successfully",
            )
        else:
            response = {
                "success": False,
                "response_type": "delete_document",
                "error": result.get("error", "Unknown error"),
            }
            client.write(json.dumps(response).encode("utf-8"))
    except Exception as e:
        response = {"success": False, "error": str(e)}
        client.write(json.dumps(response).encode("utf-8"))
