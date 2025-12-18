from pydantic import BaseModel
from typing import List

class FileItem(BaseModel):
    filename: str
    url: str

class UploadResponse(BaseModel):
    filename: str
    container: str
    uploaded: bool

class ListResponse(BaseModel):
    container: str
    files: List[FileItem]   # Each file now has a filename + URL
