import os, sys, glob, asyncio
import logging
import aiofiles
import httpx

API = os.getenv("API_URL","http://localhost:8000")
SUPPORTED_EXTS = (".md", ".txt", ".json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | ingest | %(levelname)s | %(message)s")
logger = logging.getLogger("scripts.ingest")

async def read_file(path):
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()

async def main(dir_path):
    logger.info("collecting files from %s", dir_path)
    patterns = [f"**/*{ext}" for ext in SUPPORTED_EXTS]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(dir_path, pattern), recursive=True))
    files = sorted(set(files))
    texts = [await read_file(fp) for fp in files]
    if not texts:
        logger.warning("No supported files found to ingest (.md, .txt, .json).")
        return
    logger.info("sending %d documents to %s/rag/ingest", len(files), API)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{API}/rag/ingest", json={"texts": texts})
        r.raise_for_status()
        logger.info("ingest successful: %s", r.json())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest.py <dir_with_docs>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
