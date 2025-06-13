import googlemaps
from config import Config
import logging
import math

class GooglePlacesService:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=Config.GOOGLE_PLACES_API_KEY)
    
    def _calculate_score(self, place):
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
        if user_ratings_total < 5:
            credibility_factor = 0.5  # Reduce score by 50%
        elif user_ratings_total < 20:
            credibility_factor = 0.75  # Reduce score by 25%
        else:
            credibility_factor = 1.0  # No penalty
        
        # Final score calculation
        final_score = (rating_score + popularity_bonus) * credibility_factor
        
        return final_score
    
    def _sort_places_by_quality(self, places):
        """Sort places by rating, review count, and overall quality"""
        def sort_key(place):
            # Primary sort: calculated score (higher is better)
            score = self._calculate_score(place)
            
            # Secondary sort: rating (higher is better)
            rating = place.get('rating', 0)
            
            # Tertiary sort: number of reviews (higher is better)
            review_count = place.get('user_ratings_total', 0)
            
            # Return tuple for sorting (negative values for descending order)
            return (-score, -rating, -review_count)
        
        return sorted(places, key=sort_key)
    
    def search_places(self, location, place_type, radius=None):
        """Search for places using Google Places API with enhanced sorting"""
        if radius is None:
            radius = Config.DEFAULT_SEARCH_RADIUS
        
        try:
            # Get coordinates for the location
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Define search queries based on type
            search_queries = {
                'tourist_places': ['beaches', 'mountains', 'tourist attraction', 'museum', 'park', 'zoo', 'amusement park', 'temples'],
                'restaurants': ['restaurant', 'food', 'meal takeaway', 'unique food'],
                'activities': ['trekking', 'sports', 'shopping mall', 'night club', 'yoga', 'concerts', 'new experiences'],
                'hotels': ['lodging', 'hotel', 'resorts']
            }
            
            all_results = []
            for query in search_queries.get(place_type, [place_type]):
                try:
                    results = self.gmaps.places_nearby(
                        location=lat_lng,
                        radius=radius,
                        type=query
                    )
                    all_results.extend(results.get('results', []))
                except Exception as e:
                    logging.warning(f"Error searching for {query}: {str(e)}")
                    continue
            
            # Remove duplicates based on place_id
            unique_results = {}
            for place in all_results:
                place_id = place.get('place_id')
                if place_id and place_id not in unique_results:
                    unique_results[place_id] = place
            
            # Enhanced sorting by quality score
            sorted_results = self._sort_places_by_quality(list(unique_results.values()))
            
            # Log top results for debugging
            logging.info(f"Top 3 results for {place_type}:")
            for i, place in enumerate(sorted_results[:3]):
                score = self._calculate_score(place)
                logging.info(f"{i+1}. {place.get('name')} - Score: {score:.2f}, "
                           f"Rating: {place.get('rating', 'N/A')}, "
                           f"Reviews: {place.get('user_ratings_total', 0)}")
            
            return sorted_results[:Config.MAX_RESULTS]
            
        except Exception as e:
            logging.error(f"Google Places API error: {str(e)}")
            return []
    
    def get_place_details(self, place_id):
        """Get detailed information about a specific place"""
        try:
            result = self.gmaps.place(
                place_id=place_id,
                fields=['name', 'rating', 'formatted_phone_number', 'formatted_address',
                       'website', 'opening_hours', 'price_level', 'reviews', 'user_ratings_total',
                        'photos', 'geometry', 'type', 'vicinity'] 
            )
            return result.get('result', {})
        except Exception as e:
            logging.error(f"Error getting place details: {str(e)}")
            return {}
    
    def search_nearby_places(self, location, radius_km=50):
        """Search for nearby places to visit with enhanced sorting"""
        try:
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            radius_meters = radius_km * 1000
            
            nearby_results = self.gmaps.places_nearby(
                location=lat_lng,
                radius=radius_meters,
                type='locality'
            )
            
            results = nearby_results.get('results', [])
            
            # Sort nearby places by quality as well
            sorted_results = self._sort_places_by_quality(results)
            
            return sorted_results[:10]
            
        except Exception as e:
            logging.error(f"Error searching nearby places: {str(e)}")
            return []
    
    def get_top_rated_places(self, location, place_type, min_rating=4.0, min_reviews=10, radius=None):
        """Get only high-quality places with minimum rating and review thresholds"""
        places = self.search_places(location, place_type, radius)
        
        # Filter by minimum criteria
        filtered_places = [
            place for place in places
            if place.get('rating', 0) >= min_rating and 
               place.get('user_ratings_total', 0) >= min_reviews
        ]
        
        return filtered_places
    
    def print_place_ranking_info(self, places):
        """Helper method to print detailed ranking information for debugging"""
        print("\n=== PLACE RANKING DETAILS ===")
        for i, place in enumerate(places[:10], 1):
            name = place.get('name', 'Unknown')
            rating = place.get('rating', 'N/A')
            reviews = place.get('user_ratings_total', 0)
            score = self._calculate_score(place)
            
            print(f"{i:2d}. {name}")
            print(f"    Rating: {rating} | Reviews: {reviews} | Score: {score:.2f}")
            print("-" * 50)