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
        if user_ratings_total < 50:
            credibility_factor = 0.5  # Reduce score by 50%
        elif user_ratings_total < 100:
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
                'tourist_places': ['beaches', 'mountains', 'hill_station','tourist_attraction', 'museum', 'park', 'zoo', 'amusement_park', 'temples'],
                'restaurants': ['restaurant', 'food', 'meal takeaway', 'unique food', 'local dishes', 'local food'],
                'activities': ['trekking','water falls', 'yoga', 'concerts', 'museums', 'park', 'zoo','sports', 'night club', 'sports club'],
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
            
            return sorted_results[:Config.MAX_RESULTS]
            
        except Exception as e:
            logging.error(f"Error searching nearby places: {str(e)}")
            return []

    def get_location_name_from_coords(self, lat, lng):
        """Get location name from latitude and longitude coordinates using reverse geocoding"""
        try:
            # Perform reverse geocoding
            reverse_geocode_result = self.gmaps.reverse_geocode((lat, lng))
            
            if not reverse_geocode_result:
                logging.warning(f"No results found for coordinates: {lat}, {lng}")
                return None
            
            # Get the first result (most accurate)
            result = reverse_geocode_result[0]
            
            # Try to get the most appropriate location name
            # Priority: locality -> sublocality -> administrative_area_level_2 -> administrative_area_level_1
            location_types = ['locality', 'sublocality', 'administrative_area_level_2', 'administrative_area_level_1']
            
            for location_type in location_types:
                for component in result.get('address_components', []):
                    if location_type in component.get('types', []):
                        location_name = component.get('long_name')
                        logging.info(f"Found location name: {location_name} for coordinates: {lat}, {lng}")
                        return location_name
            
            # If no specific location type found, use formatted address
            formatted_address = result.get('formatted_address', '')
            if formatted_address:
                # Extract the first part of the formatted address (usually the most specific location)
                location_name = formatted_address.split(',')[0].strip()
                logging.info(f"Using formatted address: {location_name} for coordinates: {lat}, {lng}")
                return location_name
            
            logging.warning(f"Could not extract location name from reverse geocoding result for coordinates: {lat}, {lng}")
            return None
            
        except Exception as e:
            logging.error(f"Error in reverse geocoding for coordinates {lat}, {lng}: {str(e)}")
            return None

    def search_places_by_coords(self, lat, lng, query_type, search_radius=None):
        """Search for places using coordinates directly with enhanced sorting"""
        if search_radius is None:
            search_radius = Config.DEFAULT_SEARCH_RADIUS
        
        try:
            # Create lat/lng location object
            lat_lng = {'lat': lat, 'lng': lng}
            
            # Define search queries based on type
            search_queries = {
                'tourist_places': ['beaches', 'mountains', 'hill_station','tourist_attraction', 'museum', 'park', 'zoo', 'amusement_park', 'temples'],
                'restaurants': ['restaurant', 'food', 'meal_takeaway', 'unique_food', 'local_dishes', 'local_food'],
                'activities': ['trekking','water_falls', 'yoga', 'concerts', 'museums', 'park', 'zoo','sports', 'night_club', 'sports_club'],
                'hotels': ['lodging', 'hotel', 'resorts']
            }
            
            all_results = []
            queries_to_search = search_queries.get(query_type, [query_type])
            
            for query in queries_to_search:
                try:
                    results = self.gmaps.places_nearby(
                        location=lat_lng,
                        radius=search_radius,
                        type=query
                    )
                    all_results.extend(results.get('results', []))
                except Exception as e:
                    logging.warning(f"Error searching for {query} at coordinates {lat}, {lng}: {str(e)}")
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
            logging.info(f"Top 3 results for {query_type} at coordinates {lat}, {lng}:")
            for i, place in enumerate(sorted_results[:3]):
                score = self._calculate_score(place)
                logging.info(f"{i+1}. {place.get('name')} - Score: {score:.2f}, "
                           f"Rating: {place.get('rating', 'N/A')}, "
                           f"Reviews: {place.get('user_ratings_total', 0)}")
            
            return sorted_results[:Config.MAX_RESULTS]
            
        except Exception as e:
            logging.error(f"Google Places API error for coordinates {lat}, {lng}: {str(e)}")
            return []