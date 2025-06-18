import googlemaps
from config import Config
import logging
from .place_ranker import PlaceRanker
from .place_filter import PlaceFilter
from .place_search_config import PlaceSearchConfig


class GooglePlacesService:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=Config.GOOGLE_PLACES_API_KEY)
        self.ranker = PlaceRanker()
        self.filter = PlaceFilter()
        self.search_config = PlaceSearchConfig()
    
    def search_places(self, location, place_type, radius=None):
        """Search for places using Google Places API with enhanced sorting and category filtering"""
        if radius is None:
            radius = Config.DEFAULT_SEARCH_RADIUS
        
        try:
            # Get coordinates for the location
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Get search queries for the place type
            search_queries = self.search_config.get_search_queries(place_type)
            
            all_results = []
            
            for query in search_queries:
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
            
            # Filter results based on category
            category_filters = self.search_config.get_category_filters()
            filtered_results = self.filter.filter_by_category(
                list(unique_results.values()), 
                place_type, 
                category_filters
            )
            
            # Enhanced sorting by quality score
            sorted_results = self.ranker.sort_places_by_quality(filtered_results)
            
            # Log top results for debugging
            self._log_top_results(sorted_results, place_type)
            
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
                        'photos', 'geometry', 'type', 'vicinity', 'international_phone_number', 'url', 'business_status'] 
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
            sorted_results = self.ranker.sort_places_by_quality(results)
            
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
            score = self.ranker.calculate_score(place)
            
            print(f"{i:2d}. {name}")
            print(f"    Rating: {rating} | Reviews: {reviews} | Score: {score:.2f}")
            print("-" * 50)
    
    def _log_top_results(self, sorted_results, place_type):
        """Log top results for debugging"""
        logging.info(f"Top 5 results for {place_type}:")
        for i, place in enumerate(sorted_results[:5]):
            score = self.ranker.calculate_score(place)
            logging.info(f"{i+1}. {place.get('name')} - Score: {score:.2f}, "
                       f"Rating: {place.get('rating', 'N/A')}, "
                       f"Reviews: {place.get('user_ratings_total', 0)}")