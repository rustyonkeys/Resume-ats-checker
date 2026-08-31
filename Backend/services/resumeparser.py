from unstructured.partition.text import partition_text



def parse_resume(resume_text: str) -> list[dict]:    # ->list[dict] means returns a list of dictionaries
    elements = partition_text( text = resume_text )

    cleaned_chunks = []

    for index, element in enumerate(elements):
        text = getattr(element, "text", "").strip()
        if not text:
            continue

        cleaned_chunks.append({
            "index": index,
            "category": getattr(element, "category", None),
            "text": text
        })

    return cleaned_chunks