import re


def extract_tags(text):
    pattern = re.compile(r"<(\w+)>\s*(.*?)\s*</\1>", re.DOTALL)

    matches = pattern.findall(text)

    result = {tag: content.strip() for tag, content in matches}

    return result


if __name__ == "__main__":
    text = "<summary>hello world</summary>"
    # Extracting the custom tags into a dictionary
    tags_dict = extract_tags(text)

    print(tags_dict)
