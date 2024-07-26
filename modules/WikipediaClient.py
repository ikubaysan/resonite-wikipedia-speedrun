import requests
import os
import base64
from typing import List

class WikipediaArticle:
    def __init__(self, title: str, url: str, encoded_url: str, links: List[str]):
        self.title = title
        self.url = url
        self.encoded_url = encoded_url
        self.links = links

    def __repr__(self):
        return f"WikipediaArticle(title={self.title}, url={self.url}, encoded_url={self.encoded_url}, links={self.links})"

class WikipediaClient:
    BASE_URL = "https://en.wikipedia.org/api/rest_v1/page"
    RANDOM_URL = "https://en.wikipedia.org/w/api.php"
    ARTICLE_URL = "https://en.wikipedia.org/wiki/"

    def __init__(self):
        pass

    def download_article_pdf(self, article: WikipediaArticle, file_path: str) -> None:
        """
        Downloads the specified Wikipedia article as a PDF and saves it to the given file path.
        Creates the directory if it does not exist.

        :param article: The WikipediaArticle object containing article details.
        :param file_path: The file path where the PDF should be saved.
        """
        url = f"{self.BASE_URL}/pdf/{article.title}"
        response = requests.get(url)
        response.raise_for_status()  # Raises an error if the request was unsuccessful

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Article '{article.title}' saved to '{file_path}'")

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
            "origin": "*"       # Handle CORS issues
        }
        response = requests.get(self.RANDOM_URL, params=params)
        response.raise_for_status()  # Raises an error if the request was unsuccessful
        data = response.json()

        articles = []
        for page in data['query']['pages'].values():
            title = page['title']
            url = f"{self.ARTICLE_URL}{title.replace(' ', '_')}"
            encoded_url = base64.urlsafe_b64encode(url.encode()).decode()
            links = self.get_article_links(page['pageid'])
            articles.append(WikipediaArticle(title=title, url=url, encoded_url=encoded_url, links=links))

        return articles

    def get_article_links(self, pageid: int) -> List[str]:
        """
        Gets the list of Wikipedia article links from a specified article.

        :param pageid: The page ID of the Wikipedia article.
        :return: A list of URLs to other Wikipedia articles.
        """
        params = {
            "format": "json",
            "action": "query",
            "prop": "links",
            "pageids": pageid,
            "plnamespace": 0,  # Only get links to articles in the main namespace
            "pllimit": "max"
        }
        response = requests.get(self.RANDOM_URL, params=params)
        response.raise_for_status()  # Raises an error if the request was unsuccessful
        data = response.json()

        links = []
        pages = data['query']['pages']
        for page in pages.values():
            if 'links' in page:
                for link in page['links']:
                    links.append(f"{self.ARTICLE_URL}{link['title'].replace(' ', '_')}")
        return links

if __name__ == "__main__":
    client = WikipediaClient()

    # Example usage
    random_articles = client.get_random_articles(3)
    print(f"Random articles: {random_articles}")

    # Download the random articles as PDFs
    # for article in random_articles:
    #     output_file_path = os.path.join(os.getcwd(), "downloads", f"{article.title}.pdf")
    #     client.download_article_pdf(article, output_file_path)
