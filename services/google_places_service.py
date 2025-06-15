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
    
    def _filter_by_category(self, places, category, category_filters):
        """Filter places based on category-specific criteria"""
        if category not in category_filters:
            return places
        
        filters = category_filters[category]
        include_keywords = filters.get('include_keywords', [])
        exclude_keywords = filters.get('exclude_keywords', [])
        
        filtered_places = []
        
        for place in places:
            name = place.get('name', '').lower()
            types = [t.lower() for t in place.get('types', [])]
            vicinity = place.get('vicinity', '').lower()
            
            # Combine all text for keyword matching
            combined_text = f"{name} {' '.join(types)} {vicinity}"
            
            # Check if place should be excluded
            should_exclude = any(keyword in combined_text for keyword in exclude_keywords)
            if should_exclude:
                continue
            
            # Check if place matches category (for stricter filtering)
            matches_category = False
            
            # Check against include keywords
            if any(keyword in combined_text for keyword in include_keywords):
                matches_category = True
            
            # Check against place types for category alignment
            category_type_mapping = {
                'tourist_places': [
                    'tourist_attraction', 
                    'museum', 
                    'park', 
                    'zoo', 
                    'amusement_park', 
                    'aquarium',
                    'art_gallery',
                    'hindu_temple',
                    'natural_feature',
                    'campground'
                ],
                'restaurants': [
                    'restaurant', 
                    'meal_takeaway', 
                    'cafe',
                    'bakery',
                    'bar',
                    'food'
                ],
                'activities': [
                    'spa',
                    'bowling_alley',
                    'movie_theater',
                    'night_club',
                    'stadium',
                    'tourist_attraction',
                    'amusement_park',
                    'park',
                    'zoo',
                    'aquarium',
                    'casino',
                    'movie_rental'
                ],
                'hotels': [
                    'lodging',
                    'campground',
                    'rv_park'
                ]
            }
            
            relevant_types = category_type_mapping.get(category, [])
            if any(place_type in types for place_type in relevant_types):
                matches_category = True
            
            # For tourist places, be more lenient with highly rated places
            if category == 'tourist_places' and place.get('rating', 0) >= 4.0:
                matches_category = True
            
            if matches_category:
                filtered_places.append(place)
        
        return filtered_places
    
    def _calculate_relevance_score(self, place, category):
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
            
            # Define search queries based on type with proper Google Places API types
            search_queries = {
                'tourist_places': [
                    'tourist_attraction', 
                    'museum', 
                    'park', 
                    'zoo', 
                    'amusement_park', 
                    'aquarium',
                    'art_gallery',
                    'hindu_temple',
                    'natural_feature',
                    'campground'
                ],
                'restaurants': [
                    'restaurant', 
                    'meal_takeaway', 
                    'cafe',
                    'bakery',
                    'bar',
                    'food'
                ],
                'activities': [
                    'spa',
                    'bowling_alley',
                    'movie_theater',
                    'night_club',
                    'stadium',
                    'tourist_attraction',
                    'amusement_park',
                    'park',
                    'zoo',
                    'aquarium',
                    'casino',
                    'movie_rental'
                ],
                'hotels': [
                    'lodging',
                    'campground',
                    'rv_park'
                ]
            }
            
            # Category-specific filtering keywords
            category_filters = {
                'tourist_places': {
                    'include_keywords': ['tourist', 'attraction', 'museum', 'park', 'temple', 'church', 'monument', 'heritage', 'scenic', 'viewpoint', 'fort', 'palace'],
                    'exclude_keywords': ['restaurant', 'hotel', 'lodge', 'food', 'cafe', 'bar', 'gym', 'hospital', 'bank', 'university', 'travel_agency']
                },
                'restaurants': {
                    'include_keywords': ['restaurant', 'cafe', 'food', 'dining', 'kitchen', 'bistro', 'eatery', 'cuisine'],
                    'exclude_keywords': ['hotel', 'lodge', 'hospital', 'gym', 'temple', 'museum', 'university', 'travel_agency']
                },
                'activities': {
                    'include_keywords': ['activity', 'adventure', 'sports', 'recreation', 'entertainment', 'club', 'center', 'studio'],
                    'exclude_keywords': ['hotel', 'restaurant', 'spa', 'food', 'lodge', 'hospital', 'bank', 'university', 'hindu_temple', 'church', 'mosque', 'travel_agency']
                },
                'hotels': {
                    'include_keywords': ['hotel', 'resort', 'lodge', 'accommodation', 'stay', 'inn', 'guest house'],
                    'exclude_keywords': ['restaurant', 'cafe', 'food', 'hospital', 'gym', 'temple', 'museum', 'university', 'travel_agency']
                }
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
            
            # Filter results based on category
            filtered_results = self._filter_by_category(list(unique_results.values()), place_type, category_filters)
            
            # Enhanced sorting by quality score
            sorted_results = self._sort_places_by_quality(filtered_results)
            
            # Log top results for debugging
            logging.info(f"Top 5 results for {place_type}:")
            for i, place in enumerate(sorted_results[:5]):
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