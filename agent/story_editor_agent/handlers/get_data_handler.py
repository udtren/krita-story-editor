"""Handler for get_all_docs_svg_data action"""

import json
from krita import Krita
from ..utils import (
    get_opened_doc_svg_data,
    get_all_offline_docs_from_folder,
    get_comic_config_info,
)
from ..utils.logs import write_log


def handle_get_all_docs_svg_data(client, request, docker_instance):
    """Handle retrieving SVG data from all documents (opened and offline)

    Args:
        client: The client socket connection
        request: The request data containing folder_path
        docker_instance: The StoryEditorAgentDocker instance (needed to update comic_config_info)
    """
    opened_docs = Krita.instance().documents()
    krita_folder_path = request.get("folder_path", None)
    if krita_folder_path is not None:
        docker_instance.krita_folder_path = krita_folder_path
    all_svg_data = []
    opened_docs_path = []

    # ===================================================================
    # Get all docs svg data from opened documents
    # ===================================================================
    if not opened_docs:
        response = {
            "success": False,
            "error": "No single active document",
        }
    else:
        try:
            for doc in opened_docs:
                response_data = get_opened_doc_svg_data(doc)
                all_svg_data.append(response_data)
                opened_docs_path.append(response_data.get("document_path", ""))

        except Exception as e:
            response = {"success": False, "error": str(e)}
    # ===================================================================

    if krita_folder_path:
        # ===================================================================
        # Get all docs svg data from .kra files in folder
        # ===================================================================
        try:
            write_log(f"krita_folder_path: {krita_folder_path}")
            offline_docs_svg_data = get_all_offline_docs_from_folder(
                krita_folder_path, opened_docs_path
            )
            all_svg_data.extend(offline_docs_svg_data)

        except Exception as e:
            response = {"success": False, "error": str(e)}
        # ===================================================================

        docker_instance.comic_config_info = get_comic_config_info(krita_folder_path)
    else:
        docker_instance.comic_config_info = None

    # Sort all_svg_data by document_name
    all_svg_data.sort(key=lambda x: x.get("document_name", ""))

    if docker_instance.comic_config_info:
        write_log(f"Comic config info: {docker_instance.comic_config_info}")

        response = {
            "success": True,
            "all_docs_svg_data": all_svg_data,
            "comic_config_info": docker_instance.comic_config_info,
        }
        client.write(json.dumps(response).encode("utf-8"))
    else:
        response = {
            "success": True,
            "all_docs_svg_data": all_svg_data,
            "comic_config_info": None,
        }
        client.write(json.dumps(response).encode("utf-8"))


def get_latest_all_docs_svg_data(client, docker_instance, task_type, task_result):

    write_log(f"Getting latest all docs svg data for task: {task_type}")
    opened_docs = Krita.instance().documents()
    all_svg_data = []
    opened_docs_path = []

    # ===================================================================
    # Get all docs svg data from opened documents
    # ===================================================================
    if not opened_docs:
        response = {
            "success": False,
            "error": "No single active document",
        }
    else:
        try:
            for doc in opened_docs:
                response_data = get_opened_doc_svg_data(doc)
                all_svg_data.append(response_data)
                opened_docs_path.append(response_data.get("document_path", ""))

        except Exception as e:
            response = {"success": False, "error": str(e)}
    # ===================================================================

    if docker_instance.krita_folder_path:
        # ===================================================================
        # Get all docs svg data from .kra files in folder
        # ===================================================================
        try:
            write_log(f"krita_folder_path: {docker_instance.krita_folder_path}")
            offline_docs_svg_data = get_all_offline_docs_from_folder(
                docker_instance.krita_folder_path, opened_docs_path
            )
            all_svg_data.extend(offline_docs_svg_data)

        except Exception as e:
            response = {"success": False, "error": str(e)}
        # ===================================================================

    # Sort all_svg_data by document_name
    all_svg_data.sort(key=lambda x: x.get("document_name", ""))

    if docker_instance.comic_config_info:
        response = {
            "success": True,
            "task_type": task_type,
            "task_result": task_result,
            "all_docs_svg_data": all_svg_data,
            "comic_config_info": docker_instance.comic_config_info,
        }
        client.write(json.dumps(response).encode("utf-8"))
        write_log(f"Sent latest all docs svg data with comic config info.")
    else:
        response = {
            "success": True,
            "task_type": task_type,
            "task_result": task_result,
            "all_docs_svg_data": all_svg_data,
            "comic_config_info": None,
        }
        client.write(json.dumps(response).encode("utf-8"))
        write_log(f"Sent latest all docs svg data without comic config info.")
