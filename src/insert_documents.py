import hashlib
import pathlib
import sys

import chromadb
from chromadb import errors

SEPARATOR = "## "

client = chromadb.HttpClient(host='localhost', port=8000)
db_files = pathlib.Path(__file__).parent / "db_files"


def insert_documents(clean: bool = False):
    for document in db_files.glob("*.md"):
        print(f"===== {document.name} =====")
        with open(document) as f:
            text = f.read()

        chunks = []
        ids = []

        for idx, chunk in enumerate(text.split(SEPARATOR)):
            if idx == 0:
                continue
            chunks.append(SEPARATOR + chunk)
            ids.append(hashlib.sha256(chunk.encode("utf-8")).hexdigest())

        collection_name = document.stem

        if clean:
            try:
                client.delete_collection(name=collection_name)
            except errors.NotFoundError:
                pass
        
        collection = client.get_or_create_collection(name=collection_name)

        print(f"Insert {len(chunks)} chunks into '{collection_name}' collection...")

        collection.add(
            ids=ids,
            documents=chunks,
        )

        print("Done.")


if __name__ == "__main__":
    clean_insert = False
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_insert = True
    insert_documents(clean_insert)
