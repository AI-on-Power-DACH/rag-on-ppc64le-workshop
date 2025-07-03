import hashlib
import pathlib

import chromadb

SEPARATOR = "## "

client = chromadb.HttpClient(host='localhost', port=8000)
db_files = pathlib.Path(__file__).parent / "db_files"

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
    collection = client.get_or_create_collection(name=collection_name)
    print(f"Insert {len(chunks)} chunks into '{collection_name}' collection...")

    collection.add(
        ids=ids,
        documents=chunks,
    )

    print("Done.")
