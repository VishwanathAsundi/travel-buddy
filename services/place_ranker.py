import math


class PlaceRanker:
    """Handles ranking and scoring of places based on various criteria"""
    
    def calculate_score(self, place):
        """Calculate a comprehensive score for ranking places"""
        rating = place.get('rating', 0)
        user_ratings_total = place.get('user_ratings_total', 0)
        
        # Base score from rating (0-5 scale)
        rating_score = rating * 2  # Convert to 0-10 scale
        
        # Popularity bonus based on number of reviews
        # Use logarithmic scale to prevent places with thousands of reviews from dominating
        if user_ratings_total > 0:
            popularity_bonus = min(math.log10(user_ratings_total + 1) * 2, 5)  # Max 5 points
        else:
            popularity_bonus = 0
        
        # Credibility factor: places with very few reviews get penalized
        if user_ratings_total < 50:
            credibility_factor = 0.5  # Reduce score by 50%
        elif user_ratings_total < 100:
            credibility_factor = 0.75  # Reduce score by 25%
        else:
            credibility_factor = 1.0  # No penalty
        
        # Final score calculation
        final_score = (rating_score + popularity_bonus) * credibility_factor
        
        return final_score
    
    def sort_places_by_quality(self, places):
        """Sort places by rating, review count, and overall quality"""
        def sort_key(place):
            # Primary sort: calculated score (higher is better)
            score = self.calculate_score(place)
            
            # Secondary sort: rating (higher is better)
            rating = place.get('rating', 0)
            
            # Tertiary sort: number of reviews (higher is better)
            review_count = place.get('user_ratings_total', 0)
            
            # Return tuple for sorting (negative values for descending order)
            return (-score, -rating, -review_count)
        
        return sorted(places, key=sort_key)
    
    def calculate_relevance_score(self, place, category):
        """Calculate how relevant a place is to the requested category"""
        name = place.get('name', '').lower()
        types = [t.lower() for t in place.get('types', [])]
        
        relevance_score = 0
        
        # Category-specific scoring
        if category == 'tourist_places':
            tourist_keywords = ['temple', 'museum', 'park', 'fort', 'palace', 'monument', 'heritage', 'scenic', 'viewpoint', 'attraction']
            relevance_score += sum(2 for keyword in tourist_keywords if keyword in name)
            relevance_score += sum(1 for place_type in types if place_type in ['tourist_attraction', 'museum', 'park', 'church', 'hindu_temple'])
            
        elif category == 'restaurants':
            food_keywords = ['restaurant', 'cafe', 'kitchen', 'dining', 'food', 'cuisine']
            relevance_score += sum(2 for keyword in food_keywords if keyword in name)
            relevance_score += sum(1 for place_type in types if place_type in ['restaurant', 'cafe', 'meal_takeaway'])
            
        elif category == 'activities':
            activity_keywords = ['club', 'center', 'studio', 'sports', 'gym', 'adventure']
            relevance_score += sum(2 for keyword in activity_keywords if keyword in name)
            relevance_score += sum(1 for place_type in types if place_type in ['gym', 'spa', 'night_club', 'bowling_alley'])
            
        elif category == 'hotels':
            hotel_keywords = ['hotel', 'resort', 'lodge', 'inn', 'stay']
            relevance_score += sum(2 for keyword in hotel_keywords if keyword in name)
            relevance_score += sum(1 for place_type in types if place_type == 'lodging')
        
        return relevance_score