"""Handler for docs_svg_update action"""

import os
import json
from krita import Krita
from ..utils import (
    add_svg_layer_to_doc,
    update_doc_layers_svg,
    update_offline_kra_file,
    krita_file_name_safe,
)
from ..utils.logs import write_log
from ..handlers.get_data_handler import get_latest_all_docs_svg_data


def handle_docs_svg_update(client, request, docker_instance):
    """Handle updating SVG data in documents (both opened and offline)"""
    try:
        opened_docs = Krita.instance().documents()
        merged_requests = request.get("merged_requests", {})

        write_log(f"Received merged requests: {merged_requests}")

        # ===================================================================
        # Separate opened and offline requests
        # ===================================================================
        opened_docs_requests = []
        offline_docs_requests = []

        for doc_data in merged_requests:
            if doc_data.get("opened", False):
                opened_docs_requests.append(doc_data)
            else:
                offline_docs_requests.append(doc_data)

        # Sort both lists by document_name
        opened_docs_requests.sort(key=lambda x: x.get("doc_name", ""))
        offline_docs_requests.sort(key=lambda x: x.get("doc_name", ""))

        write_log(
            f"Opened documents: {[d.get('doc_name') for d in opened_docs_requests]}"
        )
        write_log(
            f"Offline documents: {[d.get('doc_name') for d in offline_docs_requests]}"
        )
        # ===================================================================

        # ===================================================================
        # Update Opened Documents
        # ===================================================================
        online_progress_messages = []

        for doc in opened_docs:
            for doc_data in opened_docs_requests:
                write_log(
                    f"[DEBUG] agent_docker compare Document name: {krita_file_name_safe(doc)}"
                )
                if krita_file_name_safe(doc) == doc_data.get("doc_name"):

                    existing_texts_updated = doc_data.get("existing_texts_updated", [])
                    new_texts_added = doc_data.get("new_texts_added", [])

                    result_message_base = f"{krita_file_name_safe(doc)}: "

                    if len(existing_texts_updated) > 0:

                        result = update_doc_layers_svg(doc, existing_texts_updated)

                        if result["success"]:
                            result_message_base += (
                                f"\n  Updated {result.get('count', 0)} existing texts. "
                            )

                        else:
                            online_progress_messages.append(
                                f"{krita_file_name_safe(doc)}: Updating existing texts failed."
                            )
                    if len(new_texts_added) > 0:

                        result = add_svg_layer_to_doc(doc, new_texts_added)
                        if result["success"]:
                            result_message_base += (
                                f"\n  Added {result.get('count', 0)} new texts. "
                            )

                        else:
                            online_progress_messages.append(
                                f"{krita_file_name_safe(doc)}: Creating new texts failed."
                            )
                    online_progress_messages.append(result_message_base)

        # ===================================================================
        # Update Offline Documents
        # ===================================================================
        offline_progress_messages = []

        if len(offline_docs_requests) > 0:

            write_log(
                f"Updating offline .kra files: {[d.get('doc_path') for d in offline_docs_requests]}"
            )

            for doc_data in offline_docs_requests:
                doc_name = doc_data.get("doc_name")
                doc_path = doc_data.get("doc_path")
                existing_texts_updated = doc_data.get("existing_texts_updated", [])

                # Check if file exists
                if not os.path.exists(doc_path):
                    write_log(f"[WARNING] File not found: {doc_path}")
                    continue

                result = update_offline_kra_file(doc_path, existing_texts_updated)
                offline_progress_messages.append(result.get("result", ""))

        ############################################################
        final_message = "Text update applied successfully"
        if online_progress_messages:
            final_message += "\n" + "\n".join(online_progress_messages) + "\n"
        if offline_progress_messages:
            final_message += "\n" + "\n".join(offline_progress_messages) + "\n"

        get_latest_all_docs_svg_data(
            client, docker_instance, "docs_svg_update", final_message
        )
    except Exception as e:
        response = {"success": False, "docs_svg_update_result": str(e)}
        client.write(json.dumps(response).encode("utf-8"))
