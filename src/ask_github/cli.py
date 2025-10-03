import argparse
import sys
from ask_github import ask


def parse_llm_args(argv):
    """
    Parse --llm-* arguments from command line.

    Returns:
        tuple: (parsed_args, llm_config_dict)
    """
    llm_config = {}
    filtered_argv = []
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--llm-"):
            # Extract the llm parameter name (remove --llm- prefix)
            param_name = arg[6:]  # Remove "--llm-" prefix

            # Check if there's a value following this argument
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                value = argv[i + 1]

                # Try to convert to appropriate type
                if value.lower() == "true":
                    llm_config[param_name] = True
                elif value.lower() == "false":
                    llm_config[param_name] = False
                elif value.replace(".", "", 1).replace("-", "", 1).isdigit():
                    # Try to parse as number
                    if "." in value:
                        llm_config[param_name] = float(value)
                    else:
                        llm_config[param_name] = int(value)
                else:
                    llm_config[param_name] = value

                i += 2  # Skip both the flag and its value
            else:
                # Boolean flag without value, assume True
                llm_config[param_name] = True
                i += 1
        else:
            filtered_argv.append(arg)
            i += 1

    return filtered_argv, llm_config


def main():
    """CLI entry point for ask-github."""
    # Parse --llm-* arguments separately
    filtered_argv, llm_config = parse_llm_args(sys.argv[1:])

    parser = argparse.ArgumentParser(
        description="Ask questions about GitHub repositories using AI",
        epilog="""
Examples:
  # Basic usage
  ask-github https://github.com/owner/repo "What does this repository do?"

  # With custom max iterations
  ask-github https://github.com/owner/repo "Explain the architecture" --max-iterations 50

  # With custom LLM model
  ask-github https://github.com/owner/repo "How does auth work?" --llm-model gpt-4o

  # With multiple LLM parameters
  ask-github https://github.com/torvalds/linux "Explain the scheduler" \\
    --max-iterations 30 \\
    --llm-model claude-3-5-sonnet-20241022 \\
    --llm-temperature 0.5 \\
    --llm-max-tokens 4000

LLM Options:
  Use --llm-* prefix to pass any litellm config parameter:
  --llm-model          Choose the model (default: gpt-5)
  --llm-temperature    Control randomness (0.0-2.0)
  --llm-max-tokens     Limit response length
  --llm-top-p          Nucleus sampling parameter
  See https://docs.litellm.ai/docs/completion/input for all options
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("repo_url", help="URL of the GitHub repository")
    parser.add_argument("prompt", help="Question or prompt about the repository")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=150,
        help="Maximum number of agentic loop iterations (default: 150)"
    )

    args = parser.parse_args(filtered_argv)

    try:
        response = ask(
            args.repo_url,
            args.prompt,
            max_iterations=args.max_iterations,
            **llm_config
        )
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
