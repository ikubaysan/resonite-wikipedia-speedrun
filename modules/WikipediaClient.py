import requests
import os
import hashlib
from typing import List, Optional
import time
import logging
from modules.LinkIdentification.DocumentCollection import DocumentCollection

logger = logging.getLogger(__name__)

class WikipediaArticle:
    def __init__(self, title: str, url: str, links: List[str], summary: str):
        self.title = title
        # Everything after "wikipedia.org/wiki/" in the URL
        self.title_url_safe = url.split("wikipedia.org/wiki/")[1]
        self.pdf_url = f"https://en.wikipedia.org/api/rest_v1/page/pdf/{self.title_url_safe}"
        self.url = url
        self.hashed_url = hashlib.md5(url.encode()).hexdigest()
        self.links = links
        self.summary = summary

    @staticmethod
    def get_pdf_url_from_title_url_safe(title_url_safe: str) -> str:
        return f"https://en.wikipedia.org/api/rest_v1/page/pdf/{title_url_safe}"

    def as_resonite_string(self) -> str:
        full_str = ""

        # Process title
        # Truncate title to 100 characters if it's longer, otherwise pad with spaces to 100 characters
        title_str = self.title[:100].ljust(100)
        full_str += title_str

        # Process title_url_safe
        # Truncate title_url_safe to 100 characters if it's longer, otherwise pad with spaces to 100 characters
        title_url_safe_str = self.title_url_safe[:100].ljust(100)
        full_str += title_url_safe_str

        # Process pdf_url
        # Truncate pdf_url to 100 characters if it's longer, otherwise pad with spaces to 100 characters
        pdf_url_str = self.pdf_url[:100].ljust(100)
        full_str += pdf_url_str

        # Process summary
        # Truncate summary to 100 characters if it's longer, otherwise pad with spaces to 100 characters
        summary_length = 300
        summary_str = (self.summary[:summary_length - 3] + "...").ljust(summary_length)
        full_str += summary_str

        return full_str

    def __repr__(self):
        return (f"WikipediaArticle("
                f"title={self.title}, "
                f"title_url_safe={self.title_url_safe}, "
                f"url={self.url}, "
                f"pdf_url={self.pdf_url}, "
                f"hashed_url={self.hashed_url}, "
                f"links={self.links}, "
                f"summary={self.summary})")

class WikipediaClient:
    BASE_URL = "https://en.wikipedia.org/api/rest_v1/page"
    RANDOM_URL = "https://en.wikipedia.org/w/api.php"
    ARTICLE_URL = "https://en.wikipedia.org/wiki/"

    def __init__(self, pdf_download_dir: str):
        self.pdf_filename_hash_to_pdf_url = {}
        self.pdf_download_dir = pdf_download_dir
        os.makedirs(pdf_download_dir, exist_ok=True)
        self.document_collection = DocumentCollection()
        pass

    def download_article_pdf_by_title_url_safe(self, title_url_safe: str) -> None:
        """
        Downloads the specified Wikipedia article as a PDF and saves it to the given file path.
        Creates the directory if it does not exist.

        :param title_url_safe: The title of the Wikipedia article in URL-safe format.
        """
        pdf_url = WikipediaArticle.get_pdf_url_from_title_url_safe(title_url_safe)
        response = requests.get(pdf_url)
        response.raise_for_status()

        file_path = os.path.join(self.pdf_download_dir, f"{title_url_safe}.pdf")

        with open(file_path, 'wb') as file:
            file.write(response.content)

        self.document_collection.add_document(file_path)

        logger.info(f"Article '{title_url_safe}' saved to '{file_path}'")

    def download_article_pdf(self, article: WikipediaArticle) -> None:
        """
        Downloads the specified Wikipedia article as a PDF and saves it to the given file path.
        Creates the directory if it does not exist.

        :param article: The WikipediaArticle object containing article details.
        """
        response = requests.get(article.pdf_url)
        response.raise_for_status()  # Raises an error if the request was unsuccessful

        file_path = os.path.join(self.pdf_download_dir, f"{article.title_url_safe}.pdf")

        with open(file_path, 'wb') as file:
            file.write(response.content)

        self.document_collection.add_document(file_path)

        logger.info(f"Article '{article.title}' saved to '{file_path}'")


    def get_random_articles(self, count: int = 1) -> List[WikipediaArticle]:
        """
        Gets multiple random Wikipedia articles.

        :param count: The number of random articles to retrieve.
        :return: A list of WikipediaArticle objects.
        """
        params = {
            "format": "json",
            "action": "query",
            "generator": "random",
            "grnlimit": count,
            "grnnamespace": 0,  # Only get articles in the main namespace
            "origin": "*",      # Handle CORS issues
            "prop": "extracts|links",
            "exintro": True,    # Only get the introduction part of the text
            "explaintext": True, # Get plain text extract
            "pllimit": "max"    # Get maximum links
        }
        response = requests.get(self.RANDOM_URL, params=params)
        response.raise_for_status()  # Raises an error if the request was unsuccessful
        data = response.json()

        articles = []
        for page in data['query']['pages'].values():
            title = page['title']
            url = f"{self.ARTICLE_URL}{title.replace(' ', '_')}"
            links = [f"{self.ARTICLE_URL}{link['title'].replace(' ', '_')}" for link in page.get('links', [])]
            summary = page.get('extract', '')
            articles.append(WikipediaArticle(title=title, url=url, links=links, summary=summary))

        return articles

    def get_articles_with_min_links(self, n_articles: int, min_links: int, count_per_call: int) -> List[WikipediaArticle]:
        """
        Gets <min_articles> random Wikipedia articles with at least the specified number of Wikipedia links.

        :param min_links: The minimum number of links required in each article.
        :param count_per_call: The number of random articles to fetch per API call.
        :return: A list of two WikipediaArticle objects with at least the specified number of links.
        """
        articles_with_min_links = []
        titles_of_articles_with_min_links = set()

        iterations = 0
        while len(articles_with_min_links) < n_articles:
            if iterations > 0:
                logger.info(f"Retrying to find articles with at least {min_links} links. "
                            f"Found so far: {len(articles_with_min_links)}/{n_articles}")
                time.sleep(5)

            articles = self.get_random_articles(count_per_call)
            for article in articles:
                if len(article.links) >= min_links:

                    if article.title in titles_of_articles_with_min_links:
                        continue

                    articles_with_min_links.append(article)

                    titles_of_articles_with_min_links.add(article.title)

                    if len(articles_with_min_links) == n_articles:
                        break
            iterations += 1

        logger.info(f"Found {n_articles} articles with at least {min_links} links in {iterations} iterations.")
        return articles_with_min_links




    def get_article_by_title(self, title: str) -> Optional[WikipediaArticle]:
        params = {
            "format": "json",
            "action": "query",
            "titles": title,
            "prop": "extracts|links",
            "exintro": True,
            "explaintext": True,
            "pllimit": "max"
        }
        response = requests.get(self.RANDOM_URL, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data['query']['pages']
        if "-1" in pages:
            # No article found with matching title
            return None

        # Get the first matching article
        for page in pages.values():
            title = page['title']
            url = f"{self.ARTICLE_URL}{title.replace(' ', '_')}"
            links = [f"{self.ARTICLE_URL}{link['title'].replace(' ', '_')}" for link in page.get('links', [])]
            summary = page.get('extract', '')
            return WikipediaArticle(title=title, url=url, links=links, summary=summary)

        return None

    def get_article_by_url(self, url: str) -> Optional[WikipediaArticle]:
        """
        Extracts the title from the URL and fetches the article details from the Wikipedia API.
        Returns a WikipediaArticle object if successful, otherwise returns None.
        """
        if not url.startswith(self.ARTICLE_URL):
            logger.info(f"URL does not start with the expected Wikipedia URL prefix: {self.ARTICLE_URL}")
            return None

        try:
            # Extract the title from the URL
            title_url_safe = url.split(self.ARTICLE_URL)[1]
            title = title_url_safe.replace('_', ' ')

            # Fetch the article by title
            return self.get_article_by_title(title)
        except Exception as e:
            logger.error(f"Error extracting article from URL: {url} - {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    client = WikipediaClient(pdf_download_dir="pdf_storage")

    # # Example usage
    # random_articles = client.get_random_articles(3)
    # logger.info(f"Random articles: {random_articles}")
    #
    # # Get 5 articles with at least 5 links each
    # min_links_articles = client.get_articles_with_min_links(n_articles=5, min_links=5, count_per_call=100)
    # logger.info(f"Articles with at least 5 links: {min_links_articles}")
    #
    # # Download the random articles as PDFs
    # for article in min_links_articles:
    #     output_file_dir = os.path.join(os.getcwd(), "pdf_storage")
    #     client.download_article_pdf(article)




    # Get article by title
    article_title = "Puppy"
    article = client.get_article_by_title(article_title)
    if article:
        #logger.info(f"Article found: {article}")
        pass
    else:
        logger.info(f"No article found for title '{article_title}'")


    logger.info(f"Resonite string: {article.as_resonite_string()}")

    pass