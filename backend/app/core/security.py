import re
import hashlib
from typing import Optional

def sanitize_repo_url(url: str) -> str:
    """Sanitize and normalize a GitHub repository URL."""
    url = url.strip()
    # Remove trailing .git or slashes
    url = re.sub(r"\.git/?$", "", url)
    url = re.sub(r"/+$", "", url)
    
    # Ensure https://github.com/owner/repo format
    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+)", url)
    if match:
        owner, repo = match.groups()
        return f"https://github.com/{owner}/{repo}"
    return url

def extract_owner_repo(url: str) -> tuple[Optional[str], Optional[str]]:
    """Extract owner and repo name from GitHub URL."""
    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+)", url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
