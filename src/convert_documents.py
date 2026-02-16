import pathlib

from docling.document_converter import DocumentConverter

db_files = pathlib.Path(__file__).parent / "db_files"


def convert_files():
    converter = DocumentConverter()
    num_docs = 0

    for old_document in db_files.glob("*.pdf"):
        new_document_path = old_document.with_suffix(".md")
        print(f"Convert {old_document.name} --> {new_document_path.name}")

        result = converter.convert(old_document)

        with open(new_document_path, "w") as f:
            f.write(result.document.export_to_markdown())

        num_docs += 1
    
    print(f"{num_docs} documents successfully converted.")


if __name__ == "__main__":
    convert_files()
