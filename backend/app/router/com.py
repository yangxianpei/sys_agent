from fastapi import APIRouter, UploadFile, HTTPException, File
from app.utils.schemas import RespoceModel, resp_200, resp_500
import uuid
from app.config import Config
from pathlib import Path
from fastapi.responses import FileResponse

api_router = APIRouter(prefix="/v1", tags=["同意"])


@api_router.post("/upload", response_model=RespoceModel)
async def upload_image(
    file: UploadFile = File(..., description="文件"),
):
    try:
        file_dir = Config.BASE_DIR / "uploads"
        file_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex[:9]}_{file.filename}"
        content = await file.read()
        file_path = file_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return resp_200({"url": f"/uploads/{str(filename)}"}, "上传成功")
    except Exception as e:
        return resp_500(None, f"上传失败 {e}")
    except ValueError as e:
        return resp_500(None, f"{e}")


@api_router.get("/imgs/{image_name}", response_class=FileResponse)
async def imgs(
    image_name: str,
):
    file_dir = Config.BASE_DIR / "uploads"
    file_path = file_dir / image_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path))


@api_router.get("/imgs_url/{image_name}", response_model=RespoceModel)
async def imgs_to_url(
    image_name: str,
):
    file_dir = Config.BASE_DIR / "uploads"
    file_path = file_dir / image_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return resp_200({"url": f"/uploads/{str(image_name)}"}, "返回成功")
