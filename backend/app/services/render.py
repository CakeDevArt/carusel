import io
import os
import tempfile
import zipfile
import base64
import logging

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from app.models.slide import Slide
from app.services.assets import download_file

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _build_slide_html(slide: Slide, design: dict, slide_index: int, total_slides: int) -> str:
    template_name = design.get("template", "classic")
    template_file = f"slide_{template_name}.html"

    try:
        template = jinja_env.get_template(template_file)
    except Exception:
        template = jinja_env.get_template("slide_classic.html")

    bg_color = design.get("bg_color", "#ffffff")
    bg_dim = design.get("bg_dim", 0)
    padding = design.get("padding", 40)
    align_h = design.get("align_h", "left")
    align_v = design.get("align_v", "top")
    header_enabled = design.get("header_enabled", False)
    header_text = design.get("header_text", "")
    footer_enabled = design.get("footer_enabled", False)
    footer_text = design.get("footer_text", "")

    bg_image_b64 = ""
    bg_asset_s3_key = design.get("bg_asset_s3_key")
    bg_content_type = design.get("bg_asset_content_type", "image/jpeg")
    if bg_asset_s3_key:
        try:
            img_bytes = download_file(bg_asset_s3_key)
            bg_image_b64 = f"data:{bg_content_type};base64,{base64.b64encode(img_bytes).decode()}"
        except Exception as e:
            logger.warning("Could not load bg image: %s", e)

    with open(os.path.join(TEMPLATES_DIR, "base.css")) as f:
        base_css = f.read()

    return template.render(
        slide=slide,
        slide_index=slide_index,
        total_slides=total_slides,
        bg_color=bg_color,
        bg_image_b64=bg_image_b64,
        bg_dim=bg_dim,
        padding=padding,
        align_h=align_h,
        align_v=align_v,
        header_enabled=header_enabled,
        header_text=header_text,
        footer_enabled=footer_enabled,
        footer_text=footer_text,
        base_css=base_css,
    )


async def render_slide_png(html: str, out_path: str, width: int = 1080, height: int = 1350) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(path=out_path, full_page=False)
        await browser.close()


async def render_carousel_zip(slides: list[Slide], designs: list[dict]) -> bytes:
    """designs[i] — настройки дизайна для slides[i]"""
    total = len(slides)
    buf = io.BytesIO()

    with tempfile.TemporaryDirectory(prefix="carousel_render_") as tmpdir:
        for i, slide in enumerate(slides):
            design = designs[i] if i < len(designs) else {}
            html = _build_slide_html(slide, design, i + 1, total)
            png_path = os.path.join(tmpdir, f"slide_{i + 1:02d}.png")
            await render_slide_png(html, png_path)

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(total):
                png_path = os.path.join(tmpdir, f"slide_{i + 1:02d}.png")
                zf.write(png_path, f"slide_{i + 1:02d}.png")

    return buf.getvalue()
