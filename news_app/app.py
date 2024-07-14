import os
from flask import Flask, render_template, request
from datetime import datetime
from newsapi import NewsApiClient
from newspaper import Article
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize NewsAPI client
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

def get_valid_articles(articles, required_count):
    valid_articles = []
    for source in articles:
        if not source['urlToImage'] or not source['url']:
            continue
        article = {
            'title': source['title'],
            'url': source['url'],
            'timestamp': source['publishedAt'],
            'image': source['urlToImage']
        }
        try:
            # Use Newspaper3k to extract content
            news_article = Article(source['url'])
            news_article.download()
            news_article.parse()
            # Extract summary or the first few sentences
            summary = news_article.summary if news_article.summary else ' '.join(news_article.text.split()[:50])
            if len(summary) < len(news_article.text):
                summary += '...'
            article['content'] = summary
            valid_articles.append(article)
            if len(valid_articles) == required_count:
                break
        except Exception as e:
            print(f"Error parsing article: {e}")
            continue
    return valid_articles

def get_articles(page, page_size, topic=None):
    all_articles = []
    while len(all_articles) < page_size:
        offset = (page - 1) * page_size + len(all_articles) + 1
        if topic:
            top_headlines = newsapi.get_top_headlines(language='en', category=topic, page=offset, page_size=page_size * 2)
        else:
            top_headlines = newsapi.get_top_headlines(language='en', page=offset, page_size=page_size * 2)
        valid_articles = get_valid_articles(top_headlines['articles'], page_size - len(all_articles))
        if not valid_articles:
            break
        all_articles.extend(valid_articles)
    return all_articles

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    topic = request.args.get('topic', None, type=str)
    page_size = 4  # Number of articles per page
    articles = get_articles(page, page_size, topic)
    return render_template('home.html', articles=articles, page=page, topic=topic)

if __name__ == '__main__':
    app.run(debug=True)
