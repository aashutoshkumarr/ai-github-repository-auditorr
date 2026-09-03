class HTTPException(Exception):
    """Standard HTTP exception with status code and detail messaging."""
    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")
