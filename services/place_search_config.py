class PlaceSearchConfig:
    """Configuration for place search queries and filters"""
    
    def get_search_queries(self, place_type):
        """Get search queries based on place type with proper Google Places API types"""
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
        
        return search_queries.get(place_type, [place_type])
    
    def get_category_filters(self):
        """Get category-specific filtering keywords"""
        return {
            'tourist_places': {
                'include_keywords': [
                    'tourist', 'attraction', 'museum', 'park', 'temple', 'church', 
                    'monument', 'heritage', 'scenic', 'viewpoint', 'fort', 'palace'
                ],
                'exclude_keywords': [
                    'restaurant', 'hotel', 'lodge', 'food', 'cafe', 'bar', 'gym', 
                    'hospital', 'bank', 'university', 'travel_agency'
                ]
            },
            'restaurants': {
                'include_keywords': [
                    'restaurant', 'cafe', 'food', 'dining', 'kitchen', 'bistro', 
                    'eatery', 'cuisine'
                ],
                'exclude_keywords': [
                    'hotel', 'lodge', 'hospital', 'gym', 'temple', 'museum', 
                    'university', 'travel_agency'
                ]
            },
            'activities': {
                'include_keywords': [
                    'activity', 'adventure', 'sports', 'recreation', 'entertainment', 
                    'club', 'center', 'studio'
                ],
                'exclude_keywords': [
                    'hotel', 'restaurant', 'spa', 'food', 'lodge', 'hospital', 'bank', 
                    'university', 'hindu_temple', 'church', 'mosque', 'travel_agency'
                ]
            },
            'hotels': {
                'include_keywords': [
                    'hotel', 'resort', 'lodge', 'accommodation', 'stay', 'inn', 
                    'guest house'
                ],
                'exclude_keywords': [
                    'restaurant', 'cafe', 'food', 'hospital', 'gym', 'temple', 
                    'museum', 'university', 'travel_agency'
                ]
            }
        }