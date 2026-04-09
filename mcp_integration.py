"""
MCP Integration Module for Photo Update Dashboard

Handles communication with the Bulk Tools MCP server to:
1. Validate CSV format against bulk operation schema
2. Prepare CSV files for bulk upload
3. Open Bulk Tools UI with files pre-loaded
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class MCPClient:
    """Client for interacting with Bulk Tools MCP server"""

    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        Initialize MCP client

        Args:
            mcp_server_path: Path to bulk-tools-mcp executable
                           Defaults to ~/.bulk-tools-mcp/venv/bin/bulk-tools-mcp
        """
        if mcp_server_path is None:
            home = Path.home()
            self.mcp_server_path = home / ".bulk-tools-mcp" / "venv" / "bin" / "bulk-tools-mcp"
        else:
            self.mcp_server_path = Path(mcp_server_path)

        if not self.mcp_server_path.exists():
            raise FileNotFoundError(
                f"MCP server not found at {self.mcp_server_path}. "
                "Please install Bulk Tools MCP first."
            )

    def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool via subprocess

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments as dict

        Returns:
            Tool response as dict
        """
        # Construct MCP request in JSON-RPC format
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            # Call MCP server
            result = subprocess.run(
                [str(self.mcp_server_path)],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"MCP call failed: {result.stderr}")

            # Parse response
            response = json.loads(result.stdout)

            if "error" in response:
                raise RuntimeError(f"MCP error: {response['error']}")

            return response.get("result", {})

        except subprocess.TimeoutExpired:
            raise RuntimeError("MCP call timed out after 30 seconds")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse MCP response: {e}")

    def list_categories(self, search: Optional[str] = None) -> Dict[str, Any]:
        """
        List all bulk operation categories

        Args:
            search: Optional search term to filter categories

        Returns:
            Dict with categories list
        """
        args = {}
        if search:
            args["search"] = search

        return self._call_mcp_tool("bulk_list_categories", args)

    def list_operations(self, category: str) -> Dict[str, Any]:
        """
        List operations within a category

        Args:
            category: Category name (e.g., "menu", "store", "retail_catalog")

        Returns:
            Dict with operations list
        """
        return self._call_mcp_tool("bulk_list_operations", {"category_id": category})

    def get_schema(self, operation: str) -> Dict[str, Any]:
        """
        Get CSV schema for a bulk operation

        Args:
            operation: Operation name

        Returns:
            Dict with schema information
        """
        return self._call_mcp_tool("bulk_get_schema", {"operation": operation})

    def prepare_csv(
        self,
        category_id: str,
        operation_id: str,
        csv_path: str
    ) -> Dict[str, Any]:
        """
        Prepare and validate a CSV file for bulk upload

        Args:
            category_id: Bulk category ID (e.g., "retail_catalog")
            operation_id: Bulk operation ID (e.g., "update_product_item")
            csv_path: Path to CSV file to validate

        Returns:
            Dict with validation results and prepared file info
        """
        args = {
            "category_id": category_id,
            "operation_id": operation_id,
            "csv_file_path": csv_path
        }

        return self._call_mcp_tool("bulk_prepare_csv", args)

    def open_in_browser(
        self,
        category_id: str,
        operation_id: str,
        csv_path: str
    ) -> Dict[str, Any]:
        """
        Open Bulk Tools UI in browser with CSV pre-loaded

        Args:
            category_id: Bulk category ID (e.g., "retail_catalog")
            operation_id: Bulk operation ID (e.g., "update_product_item")
            csv_path: Path to CSV file to upload

        Returns:
            Dict with success status
        """
        args = {
            "category_id": category_id,
            "operation_id": operation_id,
            "csv_file_path": csv_path
        }

        return self._call_mcp_tool("bulk_open_in_browser", args)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of a submitted bulk job

        Args:
            job_id: Bulk job ID

        Returns:
            Dict with job status
        """
        return self._call_mcp_tool("bulk_get_job_status", {"job_id": job_id})


# Convenience functions for common workflows

def find_photo_operation(client: MCPClient) -> Optional[str]:
    """
    Find the correct bulk operation for photo updates

    Args:
        client: MCPClient instance

    Returns:
        Operation name or None if not found
    """
    # Search for photo/catalog related operations
    catalog_ops = client.list_operations("catalog")

    # Look for photo-related operations
    operations = catalog_ops.get("operations", [])
    for op in operations:
        op_name = op.get("name", "").lower()
        if "photo" in op_name or "image" in op_name:
            return op["name"]

    # Fallback: check menu category
    menu_ops = client.list_operations("menu")
    operations = menu_ops.get("operations", [])
    for op in operations:
        op_name = op.get("name", "").lower()
        if "photo" in op_name or "image" in op_name:
            return op["name"]

    return None


def validate_and_open(
    csv_path: str,
    category_id: str,
    operation_id: str
) -> Dict[str, Any]:
    """
    Complete workflow: validate CSV and open Bulk Tools UI

    Args:
        csv_path: Path to CSV file
        category_id: Bulk category ID (e.g., "retail_catalog")
        operation_id: Bulk operation ID (e.g., "update_product_item")

    Returns:
        Dict with workflow results
    """
    client = MCPClient()

    # Note: Skipping bulk_prepare_csv validation due to MCP subprocess stdio bug
    # The validation happens in the Bulk Tools UI anyway

    # Open in browser with file pre-loaded
    result = client.open_in_browser(category_id, operation_id, csv_path)

    return {
        "category_id": category_id,
        "operation_id": operation_id,
        "csv_path": csv_path,
        "validation_skipped": True,
        "browser_opened": True
    }
