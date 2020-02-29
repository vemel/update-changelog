import os
import argparse
import datetime
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

from github import Github
from github.PullRequest import PullRequest


def get_logger() -> logging.Logger:
    """
    Main logger.
    """
    logger = logging.getLogger("releaser")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(name)s: %(levelname)-8s %(message)s")
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG)
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    return logger


def get_parser() -> argparse.ArgumentParser:
    """
    CLI arguments parser.
    """
    parser = argparse.ArgumentParser("releaser")
    parser.add_argument("--changelog-path", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("-v", "--version", default=None)
    return parser


class GitHubEnv:
    """
    GitHub workflow env helper.
    """

    def __init__(self) -> None:
        self.github_repository = os.environ["GITHUB_REPOSITORY"]
        self.github_token = os.environ["GITHUB_TOKEN"]


class FileUpdater:
    """
    Changelog and version file updater.
    """

    RELEASE_NAME = "release"

    def __init__(self) -> None:
        self._env = GitHubEnv()
        self.client = Github(self._env.github_token)
        self.repo = self.client.get_repo(self._env.github_repository)
        self.repo.get_pulls()
        self.changed_paths: List[Path] = []
        self.pulls_list: List[PullRequest] = []

    def list_pulls_since_release(self) -> List[PullRequest]:
        result: List[PullRequest] = []
        pull: PullRequest
        for pull in self.repo.get_pulls(direction="desc", state="closed"):
            result.append(pull)

        result.reverse()
        return result

    def join_pull_changelogs(self) -> str:
        sections: Dict[str, List[str]] = {
            "Added": [],
            "Changes": [],
            "Deprecated": [],
            "Removed": [],
            "Fixed": [],
            "Security": [],
            "Other": [],
        }
        for pull in self.pulls_list:
            section: Optional[str] = None
            lines = pull.body.split("\n")
            for line in lines:
                if not line.strip():
                    continue
                if line.startswith("#") and " " in line:
                    header = line.split(" ", 1)[-1]
                    if header in sections.keys():
                        section = header
                    continue

                if section is not None:
                    sections[section].append(line)

        result: List[str] = []
        for section, lines in sections.items():
            if not lines:
                continue
            result.append(f"### {section}\n")
            for line in lines:
                result.append(line)

        return "\n".join(result)

    def update_changelog(self, changelog_path: Path, version: str) -> None:
        old_changelog = changelog_path.read_text()
        self.pulls_list = self.list_pulls_since_release()
        new_section_text = (
            self.join_pull_changelogs()
            or f"### Changes\n\n- Bumped version to {version}"
        )
        if "# [Released]" not in old_changelog:
            header = f"{old_changelog}\n"
            footer = ""
        else:
            header, footer = old_changelog.split("# [Released]", 1)

        today = datetime.date.today().strftime("%Y-%m-%d")
        new_changelog = "".join(
            [
                header,
                "# [Released]",
                "\n\n",
                f"## [{version}] - {today}\n\n",
                new_section_text,
                footer,
            ]
        )
        changelog_path.write_text(new_changelog)
        self.changed_paths.append(changelog_path)

    def get_pulls_list_md(self) -> str:
        result: List[str] = []
        for pull in self.pulls_list:
            result.append(f"- [x] PR #{pull.number}: {pull.title}")

        return "\n".join(result)


def main() -> None:
    logger = get_logger()
    try:
        args = get_parser().parse_args()
        file_updater = FileUpdater()
        if args.version:
            file_updater.update_changelog(args.changelog_path, args.version)

            output = json.dumps({"pulls_list_md": file_updater.get_pulls_list_md()})
            logger.debug(output)
            print(output)

        for changed_path in file_updater.changed_paths:
            logger.debug(f"File changed: {changed_path}")
    except Exception as e:
        logger.error(e)
        raise


if __name__ == "__main__":
    main()
