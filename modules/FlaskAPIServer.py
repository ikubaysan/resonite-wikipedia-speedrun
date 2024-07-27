from flask import Flask, request
from WikipediaClient import WikipediaClient, WikipediaArticle
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FlaskAPIServer:
    def __init__(self, port: int = 5737):
        self.app = Flask(__name__)
        self.port = port
        self.client = WikipediaClient(pdf_download_dir="pdf_storage")
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/articles', methods=['GET'])
        def get_articles():
            articles = self.client.get_articles_with_min_links(n_articles=10, min_links=5, count_per_call=100)
            article_pairs_str = self.construct_article_pairs_string(articles)
            return article_pairs_str

        @self.app.route('/get_url_at_position', methods=['GET'])
        def get_url_at_position():
            title_url_safe = request.args.get('title_url_safe')
            x = float(request.args.get('normalized_click_point_x', request.args.get('x')))
            y = float(request.args.get('normalized_click_point_y', request.args.get('y')))
            page_index = int(request.args.get('page_index'))

            pdf_filename = f"{title_url_safe}.pdf"
            document = self.client.document_collection.get_document_by_filename(filename=pdf_filename)

            if not document:
                self.client.download_article_pdf_by_title_url_safe(title_url_safe)
                document = self.client.document_collection.get_document_by_filename(filename=pdf_filename)

            url = document.get_url_at_position(x, y, normalized_coordinates=True, page_index=page_index)
            if url:
                return WikipediaArticle.get_pdf_url_from_title_url_safe(title_url_safe)
            else:
                return ""

    def construct_article_pairs_string(self, articles):
        article_pairs_str = ""
        for i in range(0, len(articles), 2):
            pair = articles[i:i+2]
            for article in pair:
                article_pairs_str += f"{article.title:<100}{article.summary:<100}{article.pdf_url:<100}"
        return article_pairs_str

    def run(self):
        self.app.run(port=self.port)

if __name__ == "__main__":
    server = FlaskAPIServer()
    server.run()
