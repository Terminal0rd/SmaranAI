"""
Clear All PDFs and Chunks
Run this to delete all uploaded documents and their chunks
"""

import sqlite3

conn = sqlite3.connect('e:/Github Projects/SmaranAI/backend/smaranai.db')
cursor = conn.cursor()

print("[RESET] Clearing all PDFs and chunks...")

try:
    # Delete all chunks first (foreign key dependency)
    cursor.execute("DELETE FROM document_chunks")
    chunks_deleted = cursor.rowcount
    print(f"[OK] Deleted {chunks_deleted} document chunks")
except Exception as e:
    print(f"[ERROR] Failed to delete chunks: {e}")

try:
    # Delete all documents
    cursor.execute("DELETE FROM documents")
    docs_deleted = cursor.rowcount
    print(f"[OK] Deleted {docs_deleted} documents")
except Exception as e:
    print(f"[ERROR] Failed to delete documents: {e}")

conn.commit()
conn.close()

print("\n[SUCCESS] All PDFs and chunks have been cleared!")
print("[READY] You can now upload new PDFs.")
