from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)

# Used To connect to SQl
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviemate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CORS(app, resources={r"/*": {"origins": ["https://movie-mate-six-rouge.vercel.app"]}})



# tHis is for the dataBase
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    kind = db.Column(db.String, default='movie')  
    director = db.Column(db.String, nullable=True)
    genre = db.Column(db.String, nullable=True)  
    platform = db.Column(db.String, nullable=True)
    status = db.Column(db.String, default='wishlist') 
    total_episodes = db.Column(db.Integer, default=0) 
    episodes_watched = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, nullable=True)
    review = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    runtime_minutes = db.Column(db.Integer, nullable=True)  
    image_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'kind': self.kind,
            'director': self.director,
            'genre': self.genre,
            'platform': self.platform,
            'status': self.status,
            'total_episodes': self.total_episodes,
            'episodes_watched': self.episodes_watched,
            'rating': self.rating,
            'review': self.review,
            'notes': self.notes,
            'runtime_minutes': self.runtime_minutes,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# This are the routes

@app.route('/')
def home():
    return jsonify({"message": "Hello from MovieMate backend!"})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


# Create item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.json or {}
    if not data.get('title'):
        return jsonify({'error': 'title required'}), 400

    item = Item(
        title=data['title'],
        kind=data.get('kind', 'movie'),
        director=data.get('director'),
        genre=data.get('genre'),
        platform=data.get('platform'),
        status=data.get('status', 'wishlist'),
        total_episodes=data.get('total_episodes', 0),
        episodes_watched=data.get('episodes_watched', 0),
        runtime_minutes=data.get('runtime_minutes'),
        image_url=data.get('image_url')
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# Filteration Logic
@app.route('/items', methods=['GET'])
def list_items():
    q = Item.query
    genre = request.args.get('genre')
    platform = request.args.get('platform')
    status = request.args.get('status')
    kind = request.args.get('kind')

    if genre:
        q = q.filter(Item.genre.contains(genre))
    if platform:
        q = q.filter_by(platform=platform)
    if status:
        q = q.filter_by(status=status)
    if kind:
        q = q.filter_by(kind=kind)

    sort = request.args.get('sort')
    if sort == 'rating_desc':
        q = q.order_by(Item.rating.desc().nullslast())
    elif sort == 'created_desc':
        q = q.order_by(Item.created_at.desc())

    items = q.all()
    return jsonify([i.to_dict() for i in items])


# Get single item
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())


# Update item
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json or {}

    for field in ['title', 'kind', 'director', 'genre', 'platform', 'status',
                  'total_episodes', 'episodes_watched', 'rating', 'review',
                  'notes', 'runtime_minutes', 'image_url']:
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return jsonify(item.to_dict())


# Delete item
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'deleted': True})


# Update progress
@app.route('/items/<int:item_id>/progress', methods=['POST'])
def update_progress(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json or {}

    try:
        delta = int(data.get('delta', 1))
    except:
        return jsonify({'error': 'invalid delta'}), 400

    item.episodes_watched = max(0, (item.episodes_watched or 0) + delta)

    if item.total_episodes and item.episodes_watched >= item.total_episodes:
        item.status = 'completed'

    db.session.commit()
    return jsonify(item.to_dict())


# Add review
@app.route('/items/<int:item_id>/review', methods=['POST'])
def add_review(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json or {}

    rating = data.get('rating')
    review = data.get('review')
    notes = data.get('notes')

    if rating is not None:
        try:
            item.rating = float(rating)
        except:
            return jsonify({'error': 'invalid rating'}), 400

    if review is not None:
        item.review = review
    if notes is not None:
        item.notes = notes

    db.session.commit()
    return jsonify(item.to_dict())


# Recommendations
@app.route('/recommendations', methods=['GET'])
def recommend():
    genre = request.args.get('genre')
    q = Item.query
    if genre:
        q = q.filter(Item.genre.contains(genre))
    q = q.filter(Item.status != 'completed')
    q = q.order_by(Item.rating.desc().nullslast())
    items = q.limit(10).all()
    return jsonify([i.to_dict() for i in items])

# This is used to create the database

# if __name__ == '__main__':
    
#     with app.app_context():
#         db.create_all()
#         print("Database tables created!")
    
#     app.run(debug=True, port=5000)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
