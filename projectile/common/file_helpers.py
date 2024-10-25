import os
import aiohttp
import aiofiles
import asyncio
import io
from PyPDF2 import PdfMerger


async def download_pdf(session, url, destination_folder):
    async with session.get(url) as response:
        filename = url.split("/")[-1]
        filepath = f"{destination_folder}/{filename}"
        async with aiofiles.open(filepath, 'wb') as file:
            await file.write(await response.read())

async def download_multiple_pdfs(urls, destination_folder):
    async with aiohttp.ClientSession() as session:
        tasks = [download_pdf(session, url, destination_folder) for url in urls]
        await asyncio.gather(*tasks)

async def create_zip(destination_folder, zip_filename):
    command = f"zip -j {zip_filename} {destination_folder}/*.pdf"
    process = await asyncio.create_subprocess_shell(command)
    await process.communicate()


async def download_pdf_for_merge(session, url):
    async with session.get(url) as response:
        return await response.read()

async def merge_pdfs(pdf_urls, duplicates=1):
    async with aiohttp.ClientSession() as session:
        tasks = [download_pdf_for_merge(session, url) for url in pdf_urls]
        downloaded_pdfs = await asyncio.gather(*tasks)

        merger = PdfMerger()

        for pdf_data in downloaded_pdfs:
            for _ in range(duplicates):
                merger.append(io.BytesIO(pdf_data))

        return merger
