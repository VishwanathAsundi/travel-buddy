class PlaceFilter:
    """Handles filtering of places based on category-specific criteria"""
    
    def filter_by_category(self, places, category, category_filters):
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
            relevant_types = self._get_category_type_mapping().get(category, [])
            if any(place_type in types for place_type in relevant_types):
                matches_category = True
            
            # For tourist places, be more lenient with highly rated places
            if category == 'tourist_places' and place.get('rating', 0) >= 4.0:
                matches_category = True
            
            if matches_category:
                filtered_places.append(place)
        
        return filtered_places
    
    def _get_category_type_mapping(self):
        """Get mapping of categories to Google Places API types"""
        return {
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