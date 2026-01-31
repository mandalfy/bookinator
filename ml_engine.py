
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

class BookinatorEngine:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.books = []
        self.questions = []
        self.book_vectors = None
        self.feature_names = []  # Ordered list of all possible features
        self.user_vector = None
        self.asked_features = set()
        
        self.load_data()
        self.init_vectors()
        
    def load_data(self):
        with open(os.path.join(self.data_dir, 'books.json'), 'r') as f:
            self.books = json.load(f)
        with open(os.path.join(self.data_dir, 'questions.json'), 'r') as f:
            self.questions = json.load(f)
            
    def init_vectors(self):
        # 1. Collect all unique features from questions mapping
        # We rely on questions.json to define what features exist and matter
        self.feature_names = sorted([q['feature'] for q in self.questions])
        self.feature_map = {name: i for i, name in enumerate(self.feature_names)}
        
        # 2. Build Book Matrix (N_books x N_features)
        n_books = len(self.books)
        n_features = len(self.feature_names)
        self.book_vectors = np.zeros((n_books, n_features))
        
        for i, book in enumerate(self.books):
            for feature, value in book['features'].items():
                if feature in self.feature_map:
                    idx = self.feature_map[feature]
                    self.book_vectors[i, idx] = value
                    
        # 3. Initialize User Vector (starts as all 0s = neutral)
        self.reset_session()

    def reset_session(self):
        self.user_vector = np.zeros(len(self.feature_names))
        self.asked_features = set()

    def update_user_vector(self, feature, answer):
        """
        answer: "yes", "no", "maybe"
        Logic:
        - Yes: +1
        - No: -1
        - Maybe: 0 (no change/neutral)
        """
        if feature not in self.feature_map:
            return
            
        idx = self.feature_map[feature]
        self.asked_features.add(feature)
        
        if answer == 'yes':
            self.user_vector[idx] = 1.0
        elif answer == 'no':
            self.user_vector[idx] = -1.0
        else: # maybe or unknown
            # For 'maybe', we leave it as 0 (neutral), or could use 0.5?
            # Sticking to 0 preserves neutrality in dot product.
            self.user_vector[idx] = 0.0

    def get_recommendations(self):
        # Compute Cosine Similarity
        # user_vector [1, -1, 0...] vs book_vectors [1, 0, 1...]
        
        # Reshape user_vector for sklearn (1, n_features)
        user_vec_reshaped = self.user_vector.reshape(1, -1)
        
        # Calculate similarity
        # Note: If user_vector is all zeros, cosine_similarity is 0 (or undefined error handled by sklearn usually returns 0)
        # To avoid division by zero errors if strictly 0, we can add epsilon or handle explicitly
        if np.linalg.norm(user_vec_reshaped) == 0:
            # If no info yet, return uniform scores or base on popularity (simple avg)
            scores = np.zeros(len(self.books))
        else:
            scores = cosine_similarity(user_vec_reshaped, self.book_vectors)[0]
            
        # Add indices to sort
        scored_books = []
        for i, score in enumerate(scores):
            scored_books.append({
                'book': self.books[i],
                'score': float(score),
                'index': i
            })
            
        # Sort descending
        scored_books.sort(key=lambda x: x['score'], reverse=True)
        return scored_books

    def get_next_question(self):
        """
        Selects the best question using a Variance/Entropy heuristic.
        We want a feature that splits the remaining HIGH SCORING books ~50/50.
        """
        # 1. Get current top candidates (e.g., top 5 or all if early game)
        # If early game (few answers), considered all.
        # If late game, focus on distinguishing top candidates.
        recommendations = self.get_recommendations()
        
        # Consider top N candidates to decide next split
        # If we have very little info (scores all 0), consider all
        if recommendations[0]['score'] == 0:
            candidates = self.books
        else:
            # Take top 5 or those with score > threshold
            # For robustness, let's take top 50% of books or top 5
            top_n = max(3, len(self.books) // 2)
            candidates = [x['book'] for x in recommendations[:top_n]]
        
        candidate_indices = [self.books.index(b) for b in candidates]
        subset_vectors = self.book_vectors[candidate_indices]
        
        best_feature = None
        max_variance = -1
        
        for feature in self.feature_names:
            if feature in self.asked_features:
                continue
                
            idx = self.feature_map[feature]
            col = subset_vectors[:, idx]
            
            # Variance calculation: p * (1-p) for binary
            # p = fraction of books having this feature = 1
            p = np.mean(col)
            variance = p * (1 - p)
            
            # We want variance closest to 0.25 (which means p=0.5)
            # Actually maximizing variance is correct for binary split
            if variance > max_variance:
                max_variance = variance
                best_feature = feature
        
        if best_feature is None:
            return None # No more questions
            
        # Find question text for this feature
        for q in self.questions:
            if q['feature'] == best_feature:
                return q
                
        return None

    def get_explanation(self, book_id):
        # Simple heuristic explanation
        # "You asked for [features matched], and this book is [features]"
        # To be implemented on frontend or simple string here
        pass
