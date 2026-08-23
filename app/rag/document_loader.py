from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    """A knowledge-base document with preserved provenance and frontmatter."""

    document_id: str
    filename: str
    path: str
    title: str
    content: str
    metadata: dict


class KnowledgeBaseLoader:
    """Loads Markdown documents and preserves their frontmatter metadata."""

    def __init__(self, knowledge_base_path: str | Path):
        self.knowledge_base_path = Path(knowledge_base_path)

    def load(self) -> list[Document]:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.knowledge_base_path}"
            )

        documents: list[Document] = []

        for path in sorted(self.knowledge_base_path.glob("*.md")):
            raw_content = path.read_text(encoding="utf-8")

            if not raw_content.strip():
                continue

            frontmatter, content = self._parse_frontmatter(raw_content)

            document_id = frontmatter.get("document_id", path.stem)
            title = frontmatter.get("title", self._extract_title(content, path))

            metadata = {
                "document_id": document_id,
                "filename": path.name,
                "source": "knowledge-base",
                **frontmatter,
            }

            documents.append(
                Document(
                    document_id=document_id,
                    filename=path.name,
                    path=str(path),
                    title=title,
                    content=content,
                    metadata=metadata,
                )
            )

        return documents

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict, str]:
        """
        Parse simple YAML-style frontmatter.

        Expected format:

        ---
        document_id: RET-2026-01
        status: active
        policy_authority: official
        ---
        """

        lines = content.splitlines()

        if not lines or lines[0].strip() != "---":
            return {}, content

        end_index = None

        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                end_index = index
                break

        if end_index is None:
            return {}, content

        metadata = {}

        for line in lines[1:end_index]:
            line = line.strip()

            if not line or line.startswith("#") or ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            metadata[key] = KnowledgeBaseLoader._parse_value(value)

        body = "\n".join(lines[end_index + 1:]).lstrip()

        return metadata, body

    @staticmethod
    def _parse_value(value: str):
        """Convert simple YAML scalar values to useful Python types."""

        if not value:
            return ""

        if value.lower() == "true":
            return True

        if value.lower() == "false":
            return False

        if value.lower() in {"null", "none"}:
            return None

        # Remove simple surrounding quotes.
        if len(value) >= 2 and value[0] == value[-1]:
            if value[0] in {"'", '"'}:
                return value[1:-1]

        return value

    @staticmethod
    def _extract_title(content: str, path: Path) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()

        return path.stem