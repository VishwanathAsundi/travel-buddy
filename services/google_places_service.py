import googlemaps
from config import Config
import logging
from .place_ranker import PlaceRanker
from .place_filter import PlaceFilter
from .place_search_config import PlaceSearchConfig
from .rate_limiter import RateLimiter


class GooglePlacesService:
    def __init__(self, requests_per_second=10, requests_per_day=100000):
        self.gmaps = googlemaps.Client(key=Config.GOOGLE_PLACES_API_KEY)
        self.ranker = PlaceRanker()
        self.filter = PlaceFilter()
        self.search_config = PlaceSearchConfig()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_second=Config.GOOGLE_PLACES_MAX_REQUESTS_PER_SECOND,
            max_requests_per_day=Config.GOOGLE_PLACES_MAX_REQUESTS_PER_DAY
        )
        
        # Track API usage
        self.api_calls_made = 0
        self.api_errors = 0
    
    def _make_api_call(self, api_function, *args, **kwargs):
        """Wrapper for all API calls with rate limiting and error handling"""
        self.rate_limiter.wait_if_needed()
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                self.api_calls_made += 1
                result = api_function(*args, **kwargs)
                
                # Log successful API call
                logging.info(f"API call {self.api_calls_made} successful")
                logging.debug(f"API call {self.api_calls_made} successful")
                return result
                
            except googlemaps.exceptions.ApiError as e:
                self.api_errors += 1
                error_msg = str(e)
                
                if "OVER_QUERY_LIMIT" in error_msg:
                    # Exponential backoff for quota errors
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"Query limit exceeded. Retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                elif "REQUEST_DENIED" in error_msg:
                    logging.error(f"API request denied: {error_msg}")
                    raise
                elif "INVALID_REQUEST" in error_msg:
                    logging.error(f"Invalid API request: {error_msg}")
                    raise
                else:
                    # Other API errors - retry with backoff
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logging.warning(f"API error: {error_msg}. Retrying in {delay} seconds")
                        time.sleep(delay)
                        continue
                    else:
                        logging.error(f"API error after {max_retries} attempts: {error_msg}")
                        raise
                        
            except Exception as e:
                self.api_errors += 1
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"Unexpected error: {str(e)}. Retrying in {delay} seconds")
                    time.sleep(delay)
                    continue
                else:
                    logging.error(f"Unexpected error after {max_retries} attempts: {str(e)}")
                    raise
        
        return None
    
    def search_places(self, location, place_type, radius=None):
        """Search for places using Google Places API with enhanced sorting and category filtering"""
        if radius is None:
            radius = Config.DEFAULT_SEARCH_RADIUS
        
        try:
            # Get coordinates for the location with rate limiting
            geocode_result = self._make_api_call(self.gmaps.geocode, location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Get search queries for the place type
            search_queries = self.search_config.get_search_queries(place_type)
            
            all_results = []
            
            for query in search_queries:
                try:
                    # Make rate-limited API call
                    results = self._make_api_call(
                        self.gmaps.places_nearby,
                        location=lat_lng,
                        radius=radius,
                        type=query
                    )
                    if results:
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
            result = self._make_api_call(
                self.gmaps.place,
                place_id=place_id,
                fields=['name', 'rating', 'formatted_phone_number', 'formatted_address',
                       'website', 'opening_hours', 'price_level', 'reviews', 'user_ratings_total',
                        'photos', 'geometry', 'type', 'vicinity', 'international_phone_number', 'url', 'business_status']
            )
            return result.get('result', {}) if result else {}
        except Exception as e:
            logging.error(f"Error getting place details: {str(e)}")
            return {}
    
    def search_nearby_places(self, location, radius_km=50):
        """Search for nearby places to visit with enhanced sorting"""
        try:
            geocode_result = self._make_api_call(self.gmaps.geocode, location)
            if not geocode_result:
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            radius_meters = radius_km * 1000
            
            nearby_results = self._make_api_call(
                self.gmaps.places_nearby,
                location=lat_lng,
                radius=radius_meters,
                type='locality'
            )
            
            results = nearby_results.get('results', []) if nearby_results else []
            
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
    
    def get_api_usage_stats(self):
        """Get API usage statistics"""
        return {
            'total_calls': self.api_calls_made,
            'total_errors': self.api_errors,
            'error_rate': (self.api_errors / max(self.api_calls_made, 1)) * 100,
            'daily_requests_remaining': self.rate_limiter.max_requests_per_day - len(self.rate_limiter.requests_per_day),
            'current_requests_per_second': len(self.rate_limiter.requests_per_second)
        }
    
    def print_api_usage(self):
        """Print current API usage statistics"""
        stats = self.get_api_usage_stats()
        print("\n=== API USAGE STATISTICS ===")
        print(f"Total API Calls: {stats['total_calls']}")
        print(f"Total Errors: {stats['total_errors']}")
        print(f"Error Rate: {stats['error_rate']:.2f}%")
        print(f"Daily Requests Remaining: {stats['daily_requests_remaining']}")
        print(f"Current RPS: {stats['current_requests_per_second']}")
        print("=" * 30)
    
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
    
    def batch_get_place_details(self, place_ids, batch_delay=0.1):
        """Get details for multiple places with controlled batching"""
        results = {}
        
        for i, place_id in enumerate(place_ids):
            try:
                details = self.get_place_details(place_id)
                results[place_id] = details
                
                # Add small delay between batch requests to be API-friendly
                if batch_delay > 0 and i < len(place_ids) - 1:
                    time.sleep(batch_delay)
                    
            except Exception as e:
                logging.warning(f"Failed to get details for place {place_id}: {str(e)}")
                results[place_id] = {}
        
        return results