import lizard
import sys


def format_analysis(info):
    program_header = f"{info.filename} ({info.nloc} lines of code)"
    funcs = []
    max_line_len = 0
    for func in info.function_list:
        header = f"Function `{func.name}` @ line {func.start_line}"
        text = f"""
{header}
  Lines: {func.nloc}
    CCN: {func.cyclomatic_complexity}"""
        max_line_len = max(len(header), max_line_len)
        funcs.append(text)

    print(f"{program_header}")
    for func in funcs:
        print(f"{'=' * max_line_len}{func}")


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: main.py <file_path>")
        return
    fpath = args[0]
    info = lizard.analyze_file(fpath)
    format_analysis(info)


if __name__ == '__main__':
    main()
