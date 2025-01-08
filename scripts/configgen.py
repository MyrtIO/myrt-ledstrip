"""Generate a config header file from a yaml file."""
import sys
import argparse
import yaml

USAGE = "Usage: python configgen.py <yaml_config_file> <output_h_file>"

def deep_flatten(input_dict: dict, delimiter: str = "_") -> dict:
    """
    Flatten a dictionary. Adds a delimiter between levels.
    """

    output = {}
    for key, value in input_dict.items():
        if isinstance(value, dict):
            for subkey, subvalue in deep_flatten(value, delimiter).items():
                output[key + delimiter + subkey] = subvalue
        else:
            output[key] = value
    return output


def generate() -> None:
    """Generate the config file."""
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(1)

    yaml_path = sys.argv[1]
    h_path = sys.argv[2]

    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)

    yaml_content = deep_flatten(yaml_content)
    h_content = ""
    for key, value in yaml_content.items():
        config_value = value
        if isinstance(config_value, str):
            if config_value.startswith('$raw'):
                config_value = config_value[5:]
            else:
                config_value = f'"{config_value}"'
        h_content += f"#define CONFIG_{key.upper()} {config_value}\n"

    with open(h_path, "w", encoding="utf-8") as f:
        f.write(h_content)

    print(f"Config generated at {h_path}")

def main():
    """Entrypoint"""
    parser = argparse.ArgumentParser(
        description="Generate a config header file from a yaml file.")
    parser.add_argument(
        "input",
        nargs="+",
        type=str,
        help="Paths to the yaml files")
    parser.add_argument(
        "--output",
        type=str,
        default="config.h",
        help="Path to the output header file")
    args = parser.parse_args()

    merged_config = {}
    for input_path in args.input:
        with open(input_path, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        yaml_content = deep_flatten(yaml_content)
        merged_config.update(yaml_content)

    h_content = ""
    for key, value in merged_config.items():
        config_value = value
        if isinstance(config_value, str):
            if config_value.startswith('$raw'):
                config_value = config_value[5:]
            else:
                config_value = f'"{config_value}"'
        h_content += f"#define CONFIG_{key.upper()} {config_value}\n"

    includes = []

    include_header = ""
    for file in includes:
        include_header += f"#include <{file}>\n"


    h_content = "#pragma once\n" + include_header + "\n" + h_content

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(h_content)

    print(f"Config generated at {args.output}")

if __name__ == "__main__":
    main()
