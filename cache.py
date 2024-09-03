import os
import uuid
import os.path as osp
from typing import Optional
import requests
from loguru import logger

class CacheManager:
    def __init__(self, logger: logger, cache_path: str = "cache") -> None:
        """Caches images from CDN
        
        Args:
            cache_path (str): Path for saving images ('cache' is default, if changing - don't forget to edit static handler!)
        """
        self.cache_path = cache_path
        self.logger = logger

        # Default image
        self.default_image = "default.png"

    def extract_filename(self, url: str) -> Optional[str]:
        """Get filename from CDN URL (all urls for this app are typical)
        
        Args:
            url (str): URL to needed file

        Returns:
            Extracted filename
        """
        try:
            filename = url.split('/')[5].split('?')[0]
            if len(filename) == 0:
                raise ValueError("Got empty file name (zero length)")
            return filename
        except Exception as e:
            self.logger.warning(f"Failed to extract filename from URL {url}: {e}")
            return

    def save(self, target_url: str, fresh: bool = False) -> str:
        """Downloads file via provided url and saves locally
        
        Args:
            target_url (str): Full URL to file from CDN
            fresh (bool): If True - redownloads image, even if exists

        Returns:
            The name of downloaded image
        """
        # Getting filename
        target_name = self.extract_filename(target_url)
        if not target_name:
            target_name = f"{uuid.uuid4()}.jpg"

        out_path = osp.join(
            self.cache_path, target_name
        )

        # Checking cache
        if osp.exists(out_path) and fresh is False:
            self.logger.debug(f"Loaded cached {target_name}")
            return target_name

        # Downloading file to cache
        try:
            ctx = requests.get(url=target_url, timeout=5)

            if ctx.status_code != 200:
                raise ValueError(f"HTTP: {ctx.status_code}, CTX: {ctx.text}")
            
            # Saving to file system
            with open(out_path, "wb") as image:
                image.write(ctx.content)
            
            self.logger.debug(f"Image {target_name} has just been cached")
            return target_name
        except Exception as e:
            self.logger.warning(f"Failed to cache image {target_name}: {e}")
            return self.default_image