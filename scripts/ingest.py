import os, sys, glob, asyncio
import aiofiles
import httpx

API = os.getenv("API_URL","http://localhost:8000")

async def read_file(path):
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()

async def main(dir_path):
    files = glob.glob(os.path.join(dir_path, "**/*.md"), recursive=True)
    texts = [await read_file(fp) for fp in files]
    if not texts:
        print("No markdown files found to ingest.")
        return
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{API}/rag/ingest", json={"texts": texts})
        r.raise_for_status()
        print("Ingest response:", r.json())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest.py <dir_with_md_files>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
