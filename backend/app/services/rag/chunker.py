import re
from typing import List, Dict, Any
from backend.app.services.repo_fetcher import RepositoryContext

class CodeChunk:
    def __init__(self, file_path: str, start_line: int, end_line: int, content: str, symbol_name: str = ""):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.symbol_name = symbol_name

class CodeChunker:
    @staticmethod
    def chunk_repository(ctx: RepositoryContext, chunk_size_lines: int = 50, overlap_lines: int = 10) -> List[CodeChunk]:
        """
        Chunks code files intelligently, preserving function definitions and line numbers.
        """
        chunks = []
        for rel_path, file in ctx.files.items():
            lines = file.content.splitlines()
            if not lines:
                continue

            # If small file, 1 chunk
            if len(lines) <= chunk_size_lines:
                chunks.append(CodeChunk(
                    file_path=rel_path,
                    start_line=1,
                    end_line=len(lines),
                    content=file.content,
                    symbol_name=rel_path
                ))
                continue

            i = 0
            while i < len(lines):
                end = min(i + chunk_size_lines, len(lines))
                chunk_lines = lines[i:end]
                
                # Check for symbol definition in chunk header
                symbol = rel_path
                for cl in chunk_lines[:5]:
                    match = re.search(r"(?:def|class|function|const|let|var)\s+([a-zA-Z0-9_]+)", cl)
                    if match:
                        symbol = match.group(1)
                        break

                chunks.append(CodeChunk(
                    file_path=rel_path,
                    start_line=i + 1,
                    end_line=end,
                    content="\n".join(chunk_lines),
                    symbol_name=symbol
                ))

                if end >= len(lines):
                    break
                i += (chunk_size_lines - overlap_lines)

        return chunks
