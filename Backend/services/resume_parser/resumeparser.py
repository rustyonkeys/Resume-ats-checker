from unstructured.partition.text import partition_text



def parse_resume(resume_text):
    elements = partition_text(
        # filename=("Backend/uploads/Kirthi Shetty Resume.pdf"),
        text = resume_text
    )

    print("Total elements:", len(elements))

    # for element in elements:
    #     print(type(element).__name__, ":", element.text)

    for element in elements:
        print(
            element.category,
            ":",
            element.text
        )
    return elements