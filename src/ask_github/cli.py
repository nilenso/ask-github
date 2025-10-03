import argparse
from ask_github import ask


def main():
    """CLI entry point for ask-github."""
    parser = argparse.ArgumentParser(
        description="Ask questions about GitHub repositories"
    )
    parser.add_argument("repo_url", help="URL of the GitHub repository")
    parser.add_argument("prompt", help="Question or prompt about the repository")

    args = parser.parse_args()

    try:
        response = ask(args.repo_url, args.prompt)
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
