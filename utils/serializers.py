from bson import ObjectId
from datetime import datetime
from typing import Any, Dict, List, Union

def serialize_doc(doc: Any) -> Any:
    """
    Convert MongoDB document to JSON-serializable dict.
    Handles ObjectId, datetime, nested dicts, and lists recursively.
    
    Args:
        doc: MongoDB document or any Python object
        
    Returns:
        JSON-serializable version of the document
    """
    if doc is None:
        return None
    
    # Handle lists
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    # Handle dictionaries (MongoDB documents)
    if isinstance(doc, dict):
        return {key: serialize_doc(value) for key, value in doc.items()}
    
    # Convert ObjectId to string
    if isinstance(doc, ObjectId):
        return str(doc)
    
    # Convert datetime to ISO format string
    if isinstance(doc, datetime):
        return doc.isoformat()
    
    # Return all other types as-is
    return doc


def serialize_list(docs: List[Dict]) -> List[Dict]:
    """
    Convenience function to serialize a list of MongoDB documents.
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of JSON-serializable dictionaries
    """
    return [serialize_doc(doc) for doc in docs]


def remove_password(doc: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Remove password field from user document(s) for security.
    
    Args:
        doc: Single document or list of documents
        
    Returns:
        Document(s) without password field
    """
    if isinstance(doc, list):
        return [remove_password(item) for item in doc]
    
    if isinstance(doc, dict):
        doc_copy = doc.copy()
        doc_copy.pop('password', None)
        return doc_copy
    
    return doc