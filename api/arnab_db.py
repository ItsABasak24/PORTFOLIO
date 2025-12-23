# api/arnab_db.py
"""
Small utility to inspect the MongoDB collection from the normal module.

Usage:
  - To run manually from project root:
      python -m api.arnab_db
  - This module will NOT run its DB code when imported by other modules.
"""

try:
    # prefer relative import when used as a package (api.*)
    from . import temp
except Exception:
    # fallback to absolute import (if you run this file differently)
    import api.temp_arnab as temp_arnab

def show_one_document():
    """Fetch one document from the collection and print a cleaned version."""
    try:
        doc = temp.my_information.find_one()
        if not doc:
            print("No documents found in the collection.")
            return
        print("One document from DB:")
        print(temp.fix_doc_ids(doc))
    except Exception as e:
        print("Error reading from DB:", e)

if __name__ == "__main__":
    show_one_document()
