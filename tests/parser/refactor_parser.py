import re


def replace_line_numbers(text):
    def replace(match):
        return f"line={int(match.group(1)) - 1}"

    return re.sub(r"line=(\d+)", replace, text)


# Sample usage
if __name__ == "__main__":
    with open("./test_parser.py") as file:
        content = file.read()

    updated_content = replace_line_numbers(content)

    with open("./test_parser.py", "w") as file:
        file.write(updated_content)
