import subprocess
from flask import *
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db'

db = SQLAlchemy(app)



class ProductResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    img = db.Column(db.String(1000))
    url = db.Column(db.String(1000))
    price_lower = db.Column(db.Float)
    price_upper = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    search_text = db.Column(db.String(255))
    source = db.Column(db.String(255))
    
    def __init__(self, name, img, url, price_lower, price_upper, search_text, source):
        self.name = name
        self.img = img
        self.url = url
        self.price_lower = price_lower
        self.price_upper = price_upper
        self.search_text = search_text
        self.source = source
        
        
class TrackedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tracked = db.Column(db.Boolean, default=True)

    def __init__(self, name, tracked=True):
        self.name = name
        self.tracked = tracked
        
        
@app.route('/results', methods=['POST'])
def submit_results():
    results = request.json.get('data')
    search_text = request.json.get('search_text')
    source = request.json.get('source')
    
    for result in results:
        product_result = ProductResult(
            name=result['name'],
            url=result['url'],
            img=result['img'],
            price_lower=result['price_lower'],
            price_upper=result['price_upper'],
            search_text=search_text,
            source=source
        )
        db.session.add(product_result)
    db.session.commit()
    response = {'message': 'Received data successfully'}
    return jsonify(response), 200


@app.route('/unique-search-texts', methods=['GET'])
def get_unique_search_texts():
    unique_search_texts = db.session.query(ProductResult.search_text).distinct().all()
    unique_search_texts = [text[0] for text in unique_search_texts]
    
    return jsonify(unique_search_texts)


@app.route('/results', methods=['GET'])
def get_product_results():
    search_text = request.args.get('search_text')
    results = ProductResult.query.filter_by(search_text=search_text).order_by(
        ProductResult.created_at.desc()
    ).all()
    
    product_dict = {}
    for result in results:
        url = result.url
        if url not in product_dict:
            product_dict[url] = {
                'name': result.name,
                'url': result.url,
                'img': result.img,
                'source': result.source,
                'created_at': result.created_at,
                'price_history': []
            }
        product_dict[url]['price_history'].append({
            'price': result.price_upper,
            'date': result.created_at
        })
        
    formated_results = list(product_dict.values())
    
    return jsonify(formated_results)


@app.route('/all-results', methods=['GET'])
def get_results():
    results = ProductResult.query.all()
    product_results = []
    for result in results:
        product_results.append({
            'name': result.name,
            'url': result.url,
            'price_lower': result.price_lower,
            'price_upper': result.price_upper,
            'img': result.img,
            'date': result.created_at,
            'created_at': result.created_at,
            'search_text': result.search_text,
            'source': result.source,
        })
        
    return jsonify(product_results)


@app.route('/start-scraper', methods=['POST'])
def start_scraper():
    url = request.json.get('url')
    search_text = request.json.get('search_text')
    
    command = f"python ./scraper/main.py {url} \"{search_text}\" /results"
    print(command)
    subprocess.Popen(command, shell=True)
    
    response = {'message': 'Scraper ran successfully'}
    return jsonify(response), 200


@app.route('/add-tracked-product', methods=['GET'])
def add_tracked_product():
    name = request.json.get('name')
    tracked_product = TrackedProduct(name=name)
    db.session.add(tracked_product)
    db.session.commit()
    
    response = {'message': 'Tracked product added successfully', 'id': tracked_product.id}
    return jsonify(response), 200


@app.route('/tracked-product/<int:product_id>', methods=['GET'])
def toggle_tracked_product(product_id):
    tracked_product = TrackedProduct.query.get(product_id)
    if tracked_product is None:
        response = {'message': 'Tracked product not found'}
        return jsonify(response), 400
    
    tracked_product.tracked = not tracked_product.tracked
    db.session.commit()
    
    response = {'message': 'Tracked product toggled successfully'}
    return jsonify(response), 200


@app.route('/tracked-products', methods=['GET'])
def get_tracked_products():
    tracked_products = TrackedProduct.query.all()
    results = []
    
    for product in tracked_products:
        results.append({
            'id': product.id,
            'name': product.name,
            'created_at': product.created_at,
            'tracked': product.tracked,
        })
        
    return jsonify(results), 200


@app.route("/update-tracked-products", methods=["POST"])
def update_tracked_products():
    tracked_products = TrackedProduct.query.all()
    url = "https://shopee.vn/"

    product_names = []
    for tracked_product in tracked_products:
        name = tracked_product.name
        if not tracked_product.tracked:
            continue

        command = f"python ./scraper/__init__.py {url} \"{name}\" /results"
        subprocess.Popen(command, shell=True)
        product_names.append(name)

    response = {'message': 'Scrapers started successfully',
                "products": product_names}
    return jsonify(response), 200
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()