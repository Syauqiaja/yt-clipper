from pydantic import BaseModel


class DriveUploadResult(BaseModel):
    file_id: str
    file_name: str
    view_link: str
    download_link: str
    thumbnail_link: str | None = None
